"""Persist raw call evidence + scores (no USD)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .io_utils import write_json


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def save_call(
    calls_dir: Path,
    *,
    sample_id: str,
    call_index: int,
    provider: str,
    model_id: str,
    condition_id: str,
    call_result: Dict[str, Any],
    parsed_score: Optional[int],
    parse_ok: bool,
) -> str:
    calls_dir.mkdir(parents=True, exist_ok=True)
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in sample_id)
    rel = f"calls/{safe_id}__call{call_index}.json"
    path = calls_dir.parent / rel if calls_dir.name == "calls" else calls_dir / f"{safe_id}__call{call_index}.json"
    # Prefer results/<m>/<mode>/calls/...
    if calls_dir.name == "calls":
        path = calls_dir / f"{safe_id}__call{call_index}.json"
        rel = f"calls/{safe_id}__call{call_index}.json"

    payload = {
        "sample_id": sample_id,
        "call_index": call_index,
        "provider": provider,
        "model_id": model_id,
        "condition_id": condition_id,
        "trace_id": call_result.get("trace_id"),
        "request_id": call_result.get("request_id"),
        "created_at": now_iso(),
        "request": call_result.get("request"),
        "response_raw": call_result.get("response_raw"),
        "output_text": call_result.get("output_text"),
        "reasoning_text": call_result.get("reasoning_text"),
        "usage": call_result.get("usage"),
        "parsed_score": parsed_score,
        "parse_ok": parse_ok,
        "latency_ms": call_result.get("latency_ms"),
    }
    write_json(path, payload)
    return rel


def aggregate_sentence_row(
    *,
    sample: Dict[str, Any],
    provider: str,
    model_id: str,
    condition_id: str,
    scores: List[Optional[int]],
    usages: List[Dict[str, int]],
    call_refs: List[str],
    latency_ms_total: int,
) -> Dict[str, Any]:
    valid = [s for s in scores if s is not None]
    parse_fail = sum(1 for s in scores if s is None)
    in_t = sum(u.get("input_tokens", 0) for u in usages)
    out_t = sum(u.get("output_tokens", 0) for u in usages)
    rea_t = sum(u.get("reasoning_tokens", 0) for u in usages)
    return {
        "sample_id": sample.get("sample_id"),
        "sentence": sample.get("sentence"),
        "human_mean": sample.get("human_mean"),
        "human_n_annotators": sample.get("human_n") or sample.get("human_n_annotators"),
        "model_scores": valid,
        "model_mean": (sum(valid) / len(valid)) if valid else None,
        "provider": provider,
        "model_id": model_id,
        "condition_id": condition_id,
        "usage": {
            "input_tokens": in_t,
            "output_tokens": out_t,
            "reasoning_tokens": rea_t,
            "total_tokens": in_t + out_t + rea_t,
            "n_api_calls": len(usages),
        },
        "call_refs": call_refs,
        "parse_fail_count": parse_fail,
        "latency_ms_total": latency_ms_total,
    }
