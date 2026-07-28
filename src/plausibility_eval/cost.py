"""Post-hoc cost from token logs × pricing.yaml (summary only)."""

from __future__ import annotations

from typing import Any, Dict, Optional


def lookup_price(pricing: Dict[str, Any], model_id: str) -> Dict[str, Any]:
    models = pricing.get("models") or {}
    if model_id in models:
        return models[model_id]
    # try slash / dirname variants
    alt = model_id.replace("__", "/")
    if alt in models:
        return models[alt]
    for k, v in models.items():
        if k.replace("/", "__") == model_id.replace("/", "__"):
            return v
    return pricing.get("default") or {
        "input_per_1m": 0.0,
        "output_per_1m": 0.0,
        "reasoning_per_1m": None,
        "source": "missing",
    }


def tokens_to_usd(usage: Dict[str, Any], price: Dict[str, Any]) -> Dict[str, Any]:
    inp = int(usage.get("input_tokens") or 0)
    out = int(usage.get("output_tokens") or 0)
    rea = int(usage.get("reasoning_tokens") or 0)
    pin = float(price.get("input_per_1m") or 0.0)
    pout = float(price.get("output_per_1m") or 0.0)
    prea = price.get("reasoning_per_1m")
    if prea is None:
        # fold reasoning into output billable tokens for providers that don't split
        out_billable = out + rea
        rea_cost = 0.0
        out_cost = out_billable / 1_000_000.0 * pout
    else:
        out_billable = out
        rea_cost = rea / 1_000_000.0 * float(prea)
        out_cost = out / 1_000_000.0 * pout
    in_cost = inp / 1_000_000.0 * pin
    total = in_cost + out_cost + rea_cost
    return {
        "input": in_cost,
        "output": out_cost,
        "reasoning": rea_cost,
        "total": total,
        "price_input_per_1m": pin,
        "price_output_per_1m": pout,
        "price_reasoning_per_1m": prea,
        "pricing_source": price.get("source"),
        "cost_mode": price.get("cost_mode", "api"),
    }


def human_cost_per_sentence(
    pricing: Dict[str, Any], human_n: Optional[int] = None
) -> float:
    h = pricing.get("human") or {}
    per = float(h.get("cost_per_rating_usd") or 0.0)
    n = int(human_n or h.get("default_annotators_per_sentence") or 1)
    return per * n
