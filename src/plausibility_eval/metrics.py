"""Quality metrics (Pearson, MAE, RMSE, parse fail). No USD."""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Optional, Sequence


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
    n = len(xs)
    if n < 2 or n != len(ys):
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den_x = math.sqrt(sum((x - mx) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - my) ** 2 for y in ys))
    if den_x == 0 or den_y == 0:
        return None
    return num / (den_x * den_y)


def compute_metrics(rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    human: List[float] = []
    model: List[float] = []
    parse_fails = 0
    n_calls = 0
    in_tok = out_tok = rea_tok = 0
    lat = 0

    rows_list = list(rows)
    for r in rows_list:
        hm = r.get("human_mean")
        mm = r.get("model_mean")
        if hm is not None and mm is not None:
            human.append(float(hm))
            model.append(float(mm))
        parse_fails += int(r.get("parse_fail_count") or 0)
        usage = r.get("usage") or {}
        n_calls += int(usage.get("n_api_calls") or 0)
        in_tok += int(usage.get("input_tokens") or 0)
        out_tok += int(usage.get("output_tokens") or 0)
        rea_tok += int(usage.get("reasoning_tokens") or 0)
        lat += int(r.get("latency_ms_total") or 0)

    n = len(human)
    mae = sum(abs(h - m) for h, m in zip(human, model)) / n if n else None
    rmse = math.sqrt(sum((h - m) ** 2 for h, m in zip(human, model)) / n) if n else None
    denom_calls = n_calls or 1

    return {
        "n_sentences": len(rows_list),
        "n_scored": n,
        "pearson_r": _pearson(human, model),
        "mae": mae,
        "rmse": rmse,
        "parse_fail_count": parse_fails,
        "parse_fail_rate": parse_fails / denom_calls,
        "usage_totals": {
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "reasoning_tokens": rea_tok,
            "total_tokens": in_tok + out_tok + rea_tok,
            "n_api_calls": n_calls,
        },
        "mean_tokens_per_sentence": {
            "input": in_tok / len(rows_list) if rows_list else 0,
            "output": out_tok / len(rows_list) if rows_list else 0,
            "reasoning": rea_tok / len(rows_list) if rows_list else 0,
        },
        "latency_ms_total": lat,
    }


def coarse_accuracy(
    rows: Sequence[Dict[str, Any]], threshold: float = 3.0
) -> Optional[float]:
    """Binary: score < threshold ⇒ implausible. Accuracy vs human labels."""
    ok = 0
    n = 0
    for r in rows:
        hm, mm = r.get("human_mean"), r.get("model_mean")
        if hm is None or mm is None:
            continue
        n += 1
        h_lab = float(hm) < threshold
        m_lab = float(mm) < threshold
        ok += int(h_lab == m_lab)
    return ok / n if n else None
