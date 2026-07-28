"""Main evaluation loop used by notebooks/eval/10_eval_plausibility.ipynb."""

from __future__ import annotations

import json
import re
import sys
import threading
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .client import ChatClient, is_open_endpoint
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

try:
    from tqdm.auto import tqdm
except ImportError:  # pragma: no cover

    def tqdm(iterable=None, **kwargs):  # type: ignore
        if iterable is None:

            class _Dummy:
                def update(self, *a, **k):
                    pass

                def set_postfix(self, *a, **k):
                    pass

                def close(self):
                    pass

            return _Dummy()
        return iterable


def _log(msg: str) -> None:
    print(msg, flush=True)
    sys.stdout.flush()


def _fmt_mean(mean: Any) -> str:
    if mean is None:
        return "None"
    try:
        return f"{float(mean):.1f}"
    except (TypeError, ValueError):
        return str(mean)


def _is_rate_limit_error(exc: BaseException) -> bool:
    s = str(exc)
    return ("429" in s) or ("Rate limit" in s) or ("rate_limit" in s.lower())


def _rate_limit_sleep_seconds(exc: BaseException, *, default: float = 65.0) -> float:
    """Parse OpenRouter/OpenAI reset hint; fall back to ~1 minute."""
    s = str(exc)
    m = re.search(r"X-RateLimit-Reset['\"\s:]+['\"]?(\d+)", s)
    if m:
        reset = int(m.group(1))
        if reset > 10_000_000_000:  # epoch ms
            wait = reset / 1000.0 - time.time() + 0.75
            return max(1.0, min(wait, 180.0))
        if reset > 1_000_000_000:  # epoch s
            wait = reset - time.time() + 0.75
            return max(1.0, min(wait, 180.0))
        return max(1.0, min(float(reset), 180.0))
    m2 = re.search(r"retry[_ -]?after['\"\s:]+['\"]?(\d+(?:\.\d+)?)", s, flags=re.I)
    if m2:
        return max(1.0, min(float(m2.group(1)), 180.0))
    return float(default)


def _relpath(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _safe_sample_id(sample_id: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in sample_id)


def _call_path(calls_dir: Path, sample_id: str, call_index: int) -> Path:
    return calls_dir / f"{_safe_sample_id(sample_id)}__call{call_index}.json"


def _load_scores_map(scores_path: Path) -> Dict[str, Dict[str, Any]]:
    if not scores_path.exists():
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for row in read_jsonl(scores_path):
        sid = row.get("sample_id")
        if sid is not None:
            out[str(sid)] = row
    return out


def _row_complete(row: Dict[str, Any], n_samples: int) -> bool:
    usage = row.get("usage") or {}
    n_calls = int(usage.get("n_api_calls") or 0)
    if n_calls >= n_samples:
        return True
    refs = row.get("call_refs") or []
    return len(refs) >= n_samples


def _load_existing_call(calls_dir: Path, sample_id: str, call_index: int) -> Optional[Dict[str, Any]]:
    path = _call_path(calls_dir, sample_id, call_index)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _missing_call_indices(
    calls_dir: Path, sample_id: str, n_samples: int, *, resume: bool
) -> List[int]:
    missing: List[int] = []
    for k in range(n_samples):
        if resume and _call_path(calls_dir, sample_id, k).exists():
            continue
        missing.append(k)
    return missing


def _parse_call_score(call_result: Dict[str, Any], expect_schema: bool) -> Tuple[Optional[int], bool]:
    score, ok = parse_score_from_output(
        call_result.get("output_text") or "",
        expect_schema=expect_schema,
    )
    if not ok:
        rea = call_result.get("reasoning_text") or ""
        if rea:
            score2, ok2 = parse_score_from_output(rea, expect_schema=expect_schema)
            if ok2:
                return score2, ok2
        return None, False
    return score, ok


def _slot_from_existing(existing: Dict[str, Any], sid: str, k: int, expect_schema: bool) -> Dict[str, Any]:
    score = existing.get("parsed_score")
    ok = bool(existing.get("parse_ok"))
    if score is None and not ok:
        score, ok = _parse_call_score(existing, expect_schema)
    return {
        "score": score if ok else None,
        "usage": existing.get("usage")
        or {"input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0},
        "rel": f"calls/{_safe_sample_id(sid)}__call{k}.json",
        "latency_ms": int(existing.get("latency_ms") or 0),
        "reused": True,
    }


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


def _thinking_extra(cfg: Dict[str, Any], provider: str) -> Dict[str, Any]:
    thinking = cfg.get("thinking") or {}
    if provider == "llamacpp_endpoint":
        return dict(
            thinking.get("llamacpp_on_extra")
            or {"chat_template_kwargs": {"enable_thinking": True}}
        )
    if provider == "openrouter":
        return dict(thinking.get("openrouter_extra") or {"reasoning": {"effort": "medium"}})
    if provider == "gemini_openai_compat":
        return dict(thinking.get("gemini_on_extra") or {"reasoning_effort": "medium"})
    return dict(thinking.get("openai_extra") or {"reasoning_effort": "medium"})


def _thinking_off_extra(cfg: Dict[str, Any], provider: str) -> Optional[Dict[str, Any]]:
    """Explicitly disable thinking/reasoning for ORIG / S."""
    thinking = cfg.get("thinking") or {}
    if provider == "llamacpp_endpoint":
        return dict(
            thinking.get("llamacpp_off_extra")
            or {"chat_template_kwargs": {"enable_thinking": False}}
        )
    if provider == "openrouter":
        return dict(thinking.get("openrouter_off_extra") or {"reasoning": {"effort": "none"}})
    if provider == "gemini_openai_compat":
        # Gemini 3.x: reasoning_effort=none → 400; thinking cannot be fully disabled.
        # Use minimal (= thinking_level minimal/low) as closest ORIG/S control.
        # Docs: https://ai.google.dev/gemini-api/docs/openai
        return dict(thinking.get("gemini_off_extra") or {"reasoning_effort": "minimal"})
    return dict(thinking.get("openai_off_extra") or {"reasoning_effort": "none"})


def apply_reasoning_effort(
    extra: Optional[Dict[str, Any]],
    provider: str,
    effort: Optional[str],
) -> Optional[Dict[str, Any]]:
    """Override reasoning effort for thinking-on modes (OpenRouter / OpenAI-compat)."""
    if effort is None:
        return extra
    level = str(effort).strip().lower()
    if not level:
        return extra
    out = dict(extra or {})
    if provider == "openrouter":
        reasoning = dict(out.get("reasoning") or {})
        reasoning["effort"] = level
        out["reasoning"] = reasoning
        return out
    if provider == "llamacpp_endpoint":
        # llama.cpp: on/off only via enable_thinking; effort not mapped
        return out
    # OpenAI official + Gemini OpenAI-compat
    out["reasoning_effort"] = level
    return out


def merge_openrouter_provider(
    extra: Optional[Dict[str, Any]],
    providers: Optional[List[str]],
    *,
    allow_fallbacks: bool = True,
) -> Optional[Dict[str, Any]]:
    """Attach OpenRouter `provider.order` (list of provider slugs) into extra_body."""
    if not providers:
        return extra
    cleaned = [str(p).strip() for p in providers if str(p).strip()]
    if not cleaned:
        return extra
    out = dict(extra or {})
    existing = dict(out.get("provider") or {})
    existing["order"] = cleaned
    existing["allow_fallbacks"] = bool(allow_fallbacks)
    out["provider"] = existing
    return out


def _ordered_rows(samples: List[Dict[str, Any]], by_id: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for sample in samples:
        sid = str(sample.get("sample_id"))
        if sid in by_id:
            rows.append(by_id[sid])
    return rows


def run_evaluation(
    *,
    model: str,
    token: str,
    base_url: str,
    mode: str,
    repo: Optional[Path] = None,
    config_path: Optional[Path] = None,
    smoke: bool = False,
    n_samples_override: Optional[int] = None,
    limit_sentences: Optional[int] = None,
    resume: bool = True,
    openrouter_providers: Optional[List[str]] = None,
    openrouter_allow_fallbacks: Optional[bool] = None,
    max_concurrency: Optional[int] = None,
    reasoning_effort: Optional[str] = None,
    temperature_override: Optional[float] = None,
    request_delay_sec: Optional[float] = None,
    rate_limit_retries: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Run one MODEL × MODE evaluation.
    Writes results/<model>/<MODE>/{calls,scores.jsonl,metrics.json,run_meta.json}.
    Does NOT compute USD.

    max_concurrency: số request API chạy song song (default từ experiment.yaml).
    reasoning_effort: mức reasoning khi MODE có thinking (T/ST/ST-E).
      OpenRouter: max|xhigh|high|medium|low|minimal|none. None → experiment.yaml.
    temperature_override: ghi đè temperature (None → open/closed theo BASE_URL).
    request_delay_sec: nghỉ tối thiểu giữa 2 request (pace toàn cục).
    rate_limit_retries: số lần đợi + retry khi 429 (0 = không retry).
    """
    repo = Path(repo) if repo else find_repo_root()
    cfg_path = Path(config_path) if config_path else repo / "configs" / "experiment.yaml"
    cfg = load_yaml(cfg_path)
    mode = validate_mode(mode)
    flags = MODE_FLAGS[mode]

    data_path = repo / cfg.get("data_path", "data/ready/mem_enc_human_and_gpt.jsonl")
    samples = read_jsonl(data_path)
    lim = limit_sentences
    if smoke:
        lim = lim or int(cfg.get("smoke_n_sentences") or 5)
    if lim is not None:
        samples = samples[: int(lim)]

    markers = list(cfg.get("open_base_url_markers") or [])
    open_ep = is_open_endpoint(base_url, markers)
    if temperature_override is not None:
        temperature = float(temperature_override)
    else:
        temperature = float(cfg["temperature_open"] if open_ep else cfg["temperature_closed"])
    n_samples = int(n_samples_override if n_samples_override is not None else cfg.get("n_samples") or 20)
    max_tokens = int((cfg.get("max_tokens") or {}).get(mode, 20))
    if max_concurrency is None:
        max_concurrency = int(cfg.get("max_concurrency") or 1)
    max_concurrency = max(1, int(max_concurrency))
    if reasoning_effort is None:
        reasoning_effort = cfg.get("reasoning_effort")
    if reasoning_effort is not None:
        reasoning_effort = str(reasoning_effort).strip().lower() or None
    if request_delay_sec is None:
        request_delay_sec = float(cfg.get("request_delay_sec") or 0.0)
    request_delay_sec = max(0.0, float(request_delay_sec))
    if rate_limit_retries is None:
        rate_limit_retries = int(cfg.get("rate_limit_retries") or 6)
    rate_limit_retries = max(0, int(rate_limit_retries))

    out_dir = results_dir(repo, model, mode)
    calls_dir = out_dir / "calls"
    calls_dir.mkdir(parents=True, exist_ok=True)
    scores_path = out_dir / "scores.jsonl"

    existing_by_id = _load_scores_map(scores_path) if resume else {}
    if not resume and scores_path.exists():
        _log(
            "[eval] resume=False — will overwrite scores for this run "
            "(existing call files may be reused only if resume=True)"
        )

    client = ChatClient(base_url=base_url, token=token, model=model)
    provider = client.provider
    # Gemini 3.x spends completion budget on hidden thinking; paper ORIG max_tokens=20
    # often yields empty content (finish_reason=length). Raise floor when needed.
    if provider == "gemini_openai_compat":
        floor = int(cfg.get("gemini_min_max_tokens") or 512)
        if max_tokens < floor:
            max_tokens = floor
    rf = _response_format(cfg, flags["schema"])
    if flags["thinking"]:
        extra = _thinking_extra(cfg, provider)
        extra = apply_reasoning_effort(extra, provider, reasoning_effort)
    else:
        extra = _thinking_off_extra(cfg, provider)

    or_providers = openrouter_providers
    or_fallbacks = openrouter_allow_fallbacks
    if provider == "openrouter":
        if or_providers is None:
            or_providers = cfg.get("openrouter_providers")
        if or_fallbacks is None:
            or_fallbacks = bool(cfg.get("openrouter_allow_fallbacks", True))
        extra = merge_openrouter_provider(
            extra,
            or_providers,
            allow_fallbacks=bool(or_fallbacks),
        )

    example_args = dict(cfg.get("example_args") or {})
    prompt_name = cfg.get("prompt_name") or "mem_enc"

    todo: List[Dict[str, Any]] = []
    skipped = 0
    slots: Dict[str, Dict[int, Dict[str, Any]]] = {}
    sample_by_id: Dict[str, Dict[str, Any]] = {}
    work: List[Tuple[str, int, List[Dict[str, str]]]] = []

    for sample in samples:
        sid = str(sample.get("sample_id"))
        sample_by_id[sid] = sample
        row = existing_by_id.get(sid)
        if resume and row and _row_complete(row, n_samples):
            skipped += 1
            continue
        todo.append(sample)
        slots[sid] = {}
        messages = build_messages(
            sample["sentence"],
            repo=repo,
            prompt_name=prompt_name,
            example_args=example_args,
            add_examples=flags["examples"],
        )
        missing = _missing_call_indices(calls_dir, sid, n_samples, resume=resume)
        for k in range(n_samples):
            if k in missing:
                continue
            existing = _load_existing_call(calls_dir, sid, k)
            if existing is not None:
                slots[sid][k] = _slot_from_existing(existing, sid, k, flags["schema"])
            else:
                missing.append(k)
        for k in sorted(set(missing)):
            work.append((sid, k, messages))

    remaining_calls = len(work)
    total_calls = len(samples) * n_samples
    _log(
        f"[eval] model={model} mode={mode} provider={provider}\n"
        f"       sentences={len(samples)} n_samples={n_samples} → {total_calls} API calls (full)\n"
        f"       resume={resume} skip_done={skipped} todo={len(todo)} remaining_calls={remaining_calls}\n"
        f"       temp={temperature} max_tokens={max_tokens} concurrency={max_concurrency} "
        f"reasoning={reasoning_effort}\n"
        f"       request_delay_sec={request_delay_sec} rate_limit_retries={rate_limit_retries}\n"
        f"       providers={or_providers} out={out_dir}"
    )

    pbar = tqdm(
        total=max(remaining_calls, 1) if work else 1,
        desc=f"{model}/{mode}",
        unit="call",
        file=sys.stdout,
        dynamic_ncols=True,
        mininterval=0.5,
    )
    if not work:
        pbar.update(1)

    io_lock = threading.Lock()
    pace_lock = threading.Lock()
    last_request_mono = 0.0
    done_sentences: set[str] = set()

    def _pace_before_request() -> None:
        """Global min spacing between API calls (all worker threads)."""
        nonlocal last_request_mono
        if request_delay_sec <= 0:
            return
        with pace_lock:
            now = time.monotonic()
            wait = request_delay_sec - (now - last_request_mono)
            if wait > 0:
                time.sleep(wait)
            last_request_mono = time.monotonic()

    def _note_request_finished() -> None:
        nonlocal last_request_mono
        with pace_lock:
            last_request_mono = time.monotonic()

    def _persist_sentence_if_ready(sid: str) -> None:
        if sid in done_sentences:
            return
        if len(slots.get(sid, {})) < n_samples:
            return
        sample = sample_by_id[sid]
        ordered = [slots[sid][k] for k in range(n_samples)]
        row = aggregate_sentence_row(
            sample=sample,
            provider=provider,
            model_id=model,
            condition_id=mode,
            scores=[s["score"] for s in ordered],
            usages=[s["usage"] for s in ordered],
            call_refs=[s["rel"] for s in ordered],
            latency_ms_total=sum(int(s["latency_ms"]) for s in ordered),
        )
        existing_by_id[sid] = row
        write_jsonl(scores_path, _ordered_rows(samples, existing_by_id))
        done_sentences.add(sid)
        line = (
            f"[eval]   → sample_id={sid} mean={_fmt_mean(row.get('model_mean'))} "
            f"parse_fail={row.get('parse_fail_count')} (saved)"
        )
        # Keep one clean line in notebook (don't let tqdm eat / fragment it)
        try:
            pbar.write(line)
        except Exception:
            _log(line)

    for sid in list(slots.keys()):
        if sid not in {w[0] for w in work} and len(slots[sid]) >= n_samples:
            _persist_sentence_if_ready(sid)

    def _run_one(
        sid: str, k: int, messages: List[Dict[str, str]]
    ) -> Tuple[str, int, Optional[Dict[str, Any]]]:
        call_result: Optional[Dict[str, Any]] = None
        for attempt in range(rate_limit_retries + 1):
            _pace_before_request()
            try:
                call_result = client.chat(
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=rf,
                    extra_body=extra,
                )
                _note_request_finished()
                break
            except Exception as exc:
                _note_request_finished()
                if _is_rate_limit_error(exc) and attempt < rate_limit_retries:
                    wait_s = _rate_limit_sleep_seconds(exc)
                    try:
                        pbar.write(
                            f"[eval] 429 {sid}#{k} — đợi {wait_s:.0f}s rồi retry "
                            f"({attempt + 1}/{rate_limit_retries})"
                        )
                    except Exception:
                        _log(
                            f"[eval] 429 {sid}#{k} — đợi {wait_s:.0f}s rồi retry "
                            f"({attempt + 1}/{rate_limit_retries})"
                        )
                    time.sleep(wait_s)
                    continue
                # Do NOT save error calls — resume will retry missing call files.
                try:
                    pbar.write(f"[eval] ERROR {sid}#{k}: {exc} (not saved)")
                except Exception:
                    _log(f"[eval] ERROR {sid}#{k}: {exc} (not saved)")
                return sid, k, None

        if call_result is None:
            return sid, k, None

        score, ok = _parse_call_score(call_result, flags["schema"])
        with io_lock:
            rel = save_call(
                calls_dir,
                sample_id=sid,
                call_index=k,
                provider=provider,
                model_id=model,
                condition_id=mode,
                call_result=call_result,
                parsed_score=score,
                parse_ok=ok,
            )
        slot = {
            "score": score,
            "usage": call_result.get("usage")
            or {"input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0},
            "rel": rel,
            "latency_ms": int(call_result.get("latency_ms") or 0),
            "reused": False,
        }
        return sid, k, slot

    if work:
        with ThreadPoolExecutor(max_workers=max_concurrency) as pool:
            futs = {pool.submit(_run_one, sid, k, messages): (sid, k) for sid, k, messages in work}
            for fut in as_completed(futs):
                sid, k, slot = fut.result()
                if slot is None:
                    pbar.update(1)
                    pbar.set_postfix(sample_id=sid, call=k, status="fail", refresh=False)
                    continue
                with io_lock:
                    slots.setdefault(sid, {})[k] = slot
                    _persist_sentence_if_ready(sid)
                pbar.update(1)
                pbar.set_postfix(sample_id=sid, call=k, refresh=False)

    pbar.close()

    for sid in slots:
        with io_lock:
            _persist_sentence_if_ready(sid)

    rows = _ordered_rows(samples, existing_by_id)
    write_jsonl(scores_path, rows)
    metrics = compute_metrics(rows)
    metrics["model_id"] = model
    metrics["mode"] = mode
    metrics["provider"] = provider
    write_json(out_dir / "metrics.json", metrics)
    _log(f"[eval] done → {out_dir}")
    _log(f"[eval] metrics: {metrics}")

    host = urllib.parse.urlparse(base_url).netloc
    run_meta = {
        "created_at": now_iso(),
        "model": model,
        "model_dirname": model_dirname(model),
        "mode": mode,
        "flags": flags,
        "provider": provider,
        "base_url_host": host,
        "temperature": temperature,
        "n_samples": n_samples,
        "max_tokens": max_tokens,
        "max_concurrency": max_concurrency,
        "request_delay_sec": request_delay_sec,
        "rate_limit_retries": rate_limit_retries,
        "reasoning_effort": reasoning_effort,
        "smoke": smoke,
        "resume": resume,
        "n_sentences": len(samples),
        "n_skipped_resume": skipped,
        "subset": cfg.get("subset"),
        "data_path": _relpath(data_path, repo),
        "prompt_name": prompt_name,
        "example_args": example_args,
        "openrouter_providers": or_providers,
        "openrouter_allow_fallbacks": or_fallbacks,
        "request_extra": extra,
        "protocol_notes": "No USD at eval time; tokens + raw calls only. Resume skips completed sentences.",
    }
    write_json(out_dir / "run_meta.json", run_meta)
    notes = out_dir / "notes.md"
    if not notes.exists():
        notes.write_text(
            f"# {model} / {mode}\n\n- provider: `{provider}`\n- sentences: {len(samples)}\n- n_samples: {n_samples}\n",
            encoding="utf-8",
        )

    return {"out_dir": str(out_dir), "metrics": metrics, "run_meta": run_meta}
