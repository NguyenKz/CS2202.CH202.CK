"""OpenAI Batch API helpers for plausibility eval (−50% vs realtime).

Official OpenAI only (api.openai.com) — not OpenRouter.
Writes the same results/<model>/<MODE>/{calls,scores.jsonl,metrics.json} layout
as the realtime notebook so 20_compare_summary.ipynb still works.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .client import extract_text_and_reasoning, extract_usage
from .io_utils import (
    find_repo_root,
    load_yaml,
    model_dirname,
    read_jsonl,
    results_dir,
    write_json,
    write_jsonl,
)
from .logger import aggregate_sentence_row, now_iso, save_call
from .metrics import compute_metrics
from .modes import MODE_FLAGS, validate_mode
from .parse import parse_score_from_output
from .prompts import build_messages
from .run_eval import _call_path, _load_scores_map, _missing_call_indices, _ordered_rows, _row_complete


def custom_id_for(sample_id: str, call_index: int) -> str:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in sample_id)
    return f"{safe}__call{call_index}"


def parse_custom_id(custom_id: str) -> Tuple[str, int]:
    if "__call" not in custom_id:
        raise ValueError(f"Bad custom_id: {custom_id!r}")
    sid, _, idx = custom_id.rpartition("__call")
    return sid, int(idx)


def _jsonable(obj: Any) -> Any:
    """Convert OpenAI SDK / pydantic objects into plain JSON types."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(x) for x in obj]
    if hasattr(obj, "model_dump"):
        try:
            return _jsonable(obj.model_dump())
        except Exception:
            pass
    if hasattr(obj, "dict"):
        try:
            return _jsonable(obj.dict())
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        data = {k: v for k, v in vars(obj).items() if not k.startswith("_")}
        if data:
            return _jsonable(data)
    return str(obj)


def _response_format(cfg: Dict[str, Any], use_schema: bool) -> Optional[Dict[str, Any]]:
    if not use_schema:
        return None
    js = cfg.get("json_schema") or {}
    return {
        "type": "json_schema",
        "json_schema": {
            "name": js.get("name", "plausibility_score"),
            "strict": bool(js.get("strict", True)),
            "schema": js.get("schema"),
        },
    }


def build_chat_body(
    *,
    model: str,
    messages: List[Dict[str, str]],
    temperature: float,
    max_tokens: int,
    flags: Dict[str, bool],
    cfg: Dict[str, Any],
    reasoning_effort: Optional[str],
) -> Dict[str, Any]:
    mid = model.lower()
    # GPT-5 / o-series: max_completion_tokens; many only allow default temperature=1
    is_reasoning_family = any(x in mid for x in ("gpt-5", "o1", "o3", "o4"))

    body: Dict[str, Any] = {
        "model": model,
        "messages": messages,
    }
    if is_reasoning_family:
        body["max_completion_tokens"] = int(max_tokens)
        # Only include temperature when it is the supported default (1).
        if float(temperature) == 1.0:
            body["temperature"] = 1.0
    else:
        body["temperature"] = float(temperature)
        body["max_tokens"] = int(max_tokens)

    rf = _response_format(cfg, bool(flags.get("schema")))
    if rf is not None:
        body["response_format"] = rf
    if flags.get("thinking"):
        effort = reasoning_effort or cfg.get("reasoning_effort") or "medium"
        body["reasoning_effort"] = str(effort).strip().lower()
    elif is_reasoning_family:
        off = ((cfg.get("thinking") or {}).get("openai_off_extra") or {}).get("reasoning_effort")
        body["reasoning_effort"] = off or "none"
    return body


def build_batch_requests(
    *,
    model: str,
    mode: str,
    repo: Optional[Path] = None,
    config_path: Optional[Path] = None,
    n_samples_override: Optional[int] = None,
    limit_sentences: Optional[int] = None,
    temperature_override: Optional[float] = None,
    reasoning_effort: Optional[str] = None,
    resume: bool = True,
) -> Dict[str, Any]:
    """
    Build Batch JSONL under results/<model>/<MODE>/batch/requests.jsonl.
    Skips call indices that already exist when resume=True.
    """
    repo = Path(repo) if repo else find_repo_root()
    cfg_path = Path(config_path) if config_path else repo / "configs" / "experiment.yaml"
    cfg = load_yaml(cfg_path)
    mode = validate_mode(mode)
    flags = MODE_FLAGS[mode]

    data_path = repo / cfg.get("data_path", "data/ready/mem_enc_human_and_gpt.jsonl")
    samples = read_jsonl(data_path)
    if limit_sentences is not None:
        samples = samples[: int(limit_sentences)]

    n_samples = int(n_samples_override if n_samples_override is not None else cfg.get("n_samples") or 20)
    # Official OpenAI = closed temp by default
    temperature = float(
        temperature_override
        if temperature_override is not None
        else cfg.get("temperature_closed", 1.5)
    )
    max_tokens = int((cfg.get("max_tokens") or {}).get(mode, 20))
    example_args = dict(cfg.get("example_args") or {})
    prompt_name = cfg.get("prompt_name") or "mem_enc"

    out_dir = results_dir(repo, model, mode)
    calls_dir = out_dir / "calls"
    calls_dir.mkdir(parents=True, exist_ok=True)
    batch_dir = out_dir / "batch"
    batch_dir.mkdir(parents=True, exist_ok=True)
    scores_path = out_dir / "scores.jsonl"
    existing_by_id = _load_scores_map(scores_path) if resume else {}

    lines: List[str] = []
    planned: List[Dict[str, Any]] = []
    skipped_complete = 0
    skipped_existing_calls = 0

    for sample in samples:
        sid = str(sample.get("sample_id"))
        row = existing_by_id.get(sid)
        if resume and row and _row_complete(row, n_samples):
            skipped_complete += 1
            continue
        messages = build_messages(
            sample["sentence"],
            repo=repo,
            prompt_name=prompt_name,
            example_args=example_args,
            add_examples=flags["examples"],
        )
        missing = _missing_call_indices(calls_dir, sid, n_samples, resume=resume)
        for k in missing:
            if resume and _call_path(calls_dir, sid, k).exists():
                skipped_existing_calls += 1
                continue
            cid = custom_id_for(sid, k)
            body = build_chat_body(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                flags=flags,
                cfg=cfg,
                reasoning_effort=reasoning_effort,
            )
            req = {
                "custom_id": cid,
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": body,
            }
            lines.append(json.dumps(req, ensure_ascii=False))
            planned.append({"custom_id": cid, "sample_id": sid, "call_index": k})

    requests_path = batch_dir / "requests.jsonl"
    requests_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    meta = {
        "created_at": now_iso(),
        "model": model,
        "mode": mode,
        "flags": flags,
        "n_samples": n_samples,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "reasoning_effort": reasoning_effort,
        "n_requests": len(lines),
        "n_sentences": len(samples),
        "skipped_complete_sentences": skipped_complete,
        "skipped_existing_calls": skipped_existing_calls,
        "requests_path": str(requests_path.relative_to(repo)),
        "protocol": "openai_batch_50pct",
    }
    write_json(batch_dir / "build_meta.json", meta)
    return {
        "out_dir": out_dir,
        "batch_dir": batch_dir,
        "requests_path": requests_path,
        "n_requests": len(lines),
        "planned": planned,
        "meta": meta,
    }


def submit_batch(
    *,
    requests_path: Path,
    token: str,
    batch_dir: Path,
    endpoint: str = "/v1/chat/completions",
    completion_window: str = "24h",
) -> Dict[str, Any]:
    from openai import OpenAI

    client = OpenAI(api_key=token)
    with Path(requests_path).open("rb") as f:
        up = client.files.create(file=f, purpose="batch")
    batch = client.batches.create(
        input_file_id=up.id,
        endpoint=endpoint,
        completion_window=completion_window,
    )
    info = {
        "submitted_at": now_iso(),
        "file_id": up.id,
        "batch_id": batch.id,
        "status": batch.status,
        "endpoint": endpoint,
        "completion_window": completion_window,
        "request_counts": _jsonable(getattr(batch, "request_counts", None)),
    }
    if hasattr(batch, "model_dump"):
        info["batch_raw"] = _jsonable(batch.model_dump())
    write_json(Path(batch_dir) / "batch_job.json", info)
    return info


def get_batch_status(*, batch_id: str, token: str, batch_dir: Optional[Path] = None) -> Dict[str, Any]:
    from openai import OpenAI

    client = OpenAI(api_key=token)
    batch = client.batches.retrieve(batch_id)
    info: Dict[str, Any] = {
        "checked_at": now_iso(),
        "batch_id": batch.id,
        "status": batch.status,
        "request_counts": _jsonable(getattr(batch, "request_counts", None)),
        "output_file_id": getattr(batch, "output_file_id", None),
        "error_file_id": getattr(batch, "error_file_id", None),
    }
    if hasattr(batch, "model_dump"):
        info["batch_raw"] = _jsonable(batch.model_dump())
    if batch_dir is not None:
        prev: Dict[str, Any] = {}
        job_path = Path(batch_dir) / "batch_job.json"
        if job_path.exists():
            try:
                prev = json.loads(job_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                prev = {}
        write_json(job_path, {**prev, **info})
    return info


def wait_batch(
    *,
    batch_id: str,
    token: str,
    batch_dir: Optional[Path] = None,
    poll_sec: float = 30.0,
    timeout_sec: float = 86_400.0,
) -> Dict[str, Any]:
    t0 = time.time()
    terminal = {"completed", "failed", "expired", "cancelled"}
    while True:
        info = get_batch_status(batch_id=batch_id, token=token, batch_dir=batch_dir)
        status = info.get("status")
        print(f"[batch] status={status} counts={info.get('request_counts')}", flush=True)
        if status in terminal:
            return info
        if time.time() - t0 > timeout_sec:
            raise TimeoutError(f"Batch {batch_id} still {status} after {timeout_sec}s")
        time.sleep(max(5.0, float(poll_sec)))


def download_batch_files(
    *,
    token: str,
    batch_dir: Path,
    output_file_id: Optional[str],
    error_file_id: Optional[str] = None,
) -> Dict[str, Optional[Path]]:
    from openai import OpenAI

    client = OpenAI(api_key=token)
    batch_dir = Path(batch_dir)
    batch_dir.mkdir(parents=True, exist_ok=True)
    out: Dict[str, Optional[Path]] = {"results_path": None, "errors_path": None}

    def _save(file_id: str, name: str) -> Path:
        content = client.files.content(file_id)
        # SDK may return HttpxBinaryResponseContent
        data = content.read() if hasattr(content, "read") else bytes(content)
        path = batch_dir / name
        path.write_bytes(data)
        return path

    if output_file_id:
        out["results_path"] = _save(output_file_id, "results.jsonl")
    if error_file_id:
        out["errors_path"] = _save(error_file_id, "errors.jsonl")
    return out


def _parse_batch_line(line: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Optional[str]]:
    """Return (custom_id, call_result-like dict, error_message|None)."""
    cid = str(line.get("custom_id") or "")
    err = line.get("error")
    if err:
        return cid, {}, (err if isinstance(err, str) else json.dumps(err, ensure_ascii=False))

    resp = (line.get("response") or {})
    body = resp.get("body") if isinstance(resp, dict) else None
    if not isinstance(body, dict):
        return cid, {}, f"missing response.body for {cid}"

    # Reuse extractors with dict-shaped OpenAI response
    output_text, reasoning_text = extract_text_and_reasoning(body)
    usage = extract_usage(body)
    trace_id = body.get("id")
    call_result = {
        "response_raw": body,
        "output_text": output_text,
        "reasoning_text": reasoning_text,
        "usage": usage,
        "trace_id": trace_id,
        "request_id": trace_id,
        "latency_ms": None,
        "request": {
            "source": "openai_batch",
            "custom_id": cid,
            "http_status": resp.get("status_code"),
        },
    }
    status = resp.get("status_code")
    if status and int(status) >= 400:
        return cid, call_result, f"http {status}"
    return cid, call_result, None


def ingest_batch_results(
    *,
    model: str,
    mode: str,
    results_path: Path,
    repo: Optional[Path] = None,
    config_path: Optional[Path] = None,
    errors_path: Optional[Path] = None,
    n_samples_override: Optional[int] = None,
) -> Dict[str, Any]:
    """Parse Batch results JSONL → calls/ + scores.jsonl + metrics.json."""
    repo = Path(repo) if repo else find_repo_root()
    cfg_path = Path(config_path) if config_path else repo / "configs" / "experiment.yaml"
    cfg = load_yaml(cfg_path)
    mode = validate_mode(mode)
    flags = MODE_FLAGS[mode]
    n_samples = int(n_samples_override if n_samples_override is not None else cfg.get("n_samples") or 20)

    data_path = repo / cfg.get("data_path", "data/ready/mem_enc_human_and_gpt.jsonl")
    samples = read_jsonl(data_path)
    sample_by_id = {str(s.get("sample_id")): s for s in samples}

    out_dir = results_dir(repo, model, mode)
    calls_dir = out_dir / "calls"
    calls_dir.mkdir(parents=True, exist_ok=True)
    scores_path = out_dir / "scores.jsonl"
    existing_by_id = _load_scores_map(scores_path)

    saved = 0
    failed_lines = 0
    slots: Dict[str, Dict[int, Dict[str, Any]]] = {}

    # Load any existing good calls for incomplete sentences
    for sample in samples:
        sid = str(sample.get("sample_id"))
        for k in range(n_samples):
            path = _call_path(calls_dir, sid, k)
            if not path.exists():
                continue
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if existing.get("response_raw") and isinstance(existing["response_raw"], dict):
                if existing["response_raw"].get("error"):
                    continue
            score = existing.get("parsed_score")
            ok = bool(existing.get("parse_ok"))
            if score is None and not ok:
                score, ok = parse_score_from_output(
                    existing.get("output_text") or "",
                    expect_schema=flags["schema"],
                )
            slots.setdefault(sid, {})[k] = {
                "score": score if ok else None,
                "usage": existing.get("usage")
                or {"input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0},
                "rel": f"calls/{path.name}",
                "latency_ms": int(existing.get("latency_ms") or 0),
            }

    def _ingest_file(path: Path, *, is_error_file: bool = False) -> None:
        nonlocal saved, failed_lines
        if path is None or not Path(path).exists():
            return
        for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            line = json.loads(raw_line)
            try:
                cid, call_result, err = _parse_batch_line(line)
                sid, k = parse_custom_id(cid)
            except Exception as exc:
                failed_lines += 1
                print(f"[batch] skip line: {exc}", flush=True)
                continue
            if err or is_error_file or not call_result:
                failed_lines += 1
                print(f"[batch] fail {cid}: {err}", flush=True)
                continue
            score, ok = parse_score_from_output(
                call_result.get("output_text") or "",
                expect_schema=flags["schema"],
            )
            if not ok and call_result.get("reasoning_text"):
                score2, ok2 = parse_score_from_output(
                    call_result["reasoning_text"],
                    expect_schema=flags["schema"],
                )
                if ok2:
                    score, ok = score2, ok2
            rel = save_call(
                calls_dir,
                sample_id=sid,
                call_index=k,
                provider="openai_official_batch",
                model_id=model,
                condition_id=mode,
                call_result=call_result,
                parsed_score=score,
                parse_ok=ok,
            )
            slots.setdefault(sid, {})[k] = {
                "score": score if ok else None,
                "usage": call_result.get("usage")
                or {"input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0},
                "rel": rel,
                "latency_ms": int(call_result.get("latency_ms") or 0),
            }
            saved += 1

    _ingest_file(Path(results_path))
    if errors_path:
        _ingest_file(Path(errors_path), is_error_file=True)

    # Aggregate complete sentences only
    for sid, by_k in slots.items():
        if len(by_k) < n_samples:
            continue
        sample = sample_by_id.get(sid)
        if sample is None:
            continue
        ordered = [by_k[k] for k in range(n_samples)]
        row = aggregate_sentence_row(
            sample=sample,
            provider="openai_official_batch",
            model_id=model,
            condition_id=mode,
            scores=[s["score"] for s in ordered],
            usages=[s["usage"] for s in ordered],
            call_refs=[s["rel"] for s in ordered],
            latency_ms_total=sum(int(s["latency_ms"] or 0) for s in ordered),
        )
        existing_by_id[sid] = row

    rows = _ordered_rows(samples, existing_by_id)
    write_jsonl(scores_path, rows)
    metrics = compute_metrics(rows)
    metrics["model_id"] = model
    metrics["mode"] = mode
    metrics["provider"] = "openai_official_batch"
    write_json(out_dir / "metrics.json", metrics)
    write_json(
        out_dir / "run_meta.json",
        {
            "created_at": now_iso(),
            "model": model,
            "model_dirname": model_dirname(model),
            "mode": mode,
            "flags": flags,
            "provider": "openai_official_batch",
            "n_samples": n_samples,
            "protocol": "openai_batch_50pct",
            "ingest_saved_calls": saved,
            "ingest_failed_lines": failed_lines,
            "n_scored_sentences": len(rows),
        },
    )
    return {
        "out_dir": str(out_dir),
        "saved_calls": saved,
        "failed_lines": failed_lines,
        "n_scores": len(rows),
        "metrics": metrics,
    }
