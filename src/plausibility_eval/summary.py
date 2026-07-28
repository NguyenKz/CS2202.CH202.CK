"""Aggregate results/ + apply pricing.yaml (no LLM calls)."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional

from .cost import human_cost_per_sentence, lookup_price, tokens_to_usd
from .io_utils import find_repo_root, load_yaml, read_jsonl, write_json
from .metrics import coarse_accuracy, compute_metrics


def discover_runs(results_root: Path) -> List[Path]:
    runs = []
    if not results_root.is_dir():
        return runs
    for model_dir in sorted(results_root.iterdir()):
        if not model_dir.is_dir() or model_dir.name.startswith(("_", ".")):
            continue
        for mode_dir in sorted(model_dir.iterdir()):
            if (mode_dir / "scores.jsonl").is_file():
                runs.append(mode_dir)
    return runs


def summarize_all(
    *,
    repo: Optional[Path] = None,
    pricing_path: Optional[Path] = None,
    coarse_threshold: float = 3.0,
) -> Dict[str, Any]:
    repo = Path(repo) if repo else find_repo_root()
    pricing_path = Path(pricing_path) if pricing_path else repo / "configs" / "pricing.yaml"
    pricing = load_yaml(pricing_path)
    results_root = repo / "results"
    runs = discover_runs(results_root)

    table: List[Dict[str, Any]] = []
    for run_dir in runs:
        rows = read_jsonl(run_dir / "scores.jsonl")
        meta = {}
        meta_path = run_dir / "run_meta.json"
        if meta_path.exists():
            import json

            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        metrics = compute_metrics(rows)
        model_id = meta.get("model") or run_dir.parent.name.replace("__", "/")
        mode = meta.get("mode") or run_dir.name
        price = lookup_price(pricing, model_id)
        usage = metrics.get("usage_totals") or {}
        cost = tokens_to_usd(usage, price)
        # human cost: mean of per-row if available
        human_costs = [
            human_cost_per_sentence(pricing, r.get("human_n_annotators"))
            for r in rows
            if r.get("human_mean") is not None
        ]
        mean_human = sum(human_costs) / len(human_costs) if human_costs else human_cost_per_sentence(pricing)
        n_sent = max(metrics.get("n_scored") or 1, 1)
        mean_llm = cost["total"] / n_sent
        ratio = (mean_llm / mean_human) if mean_human else None

        with_cost = {
            **metrics,
            "model_id": model_id,
            "mode": mode,
            "cost_usd_total": cost["total"],
            "mean_cost_per_sentence_usd": mean_llm,
            "mean_human_cost_per_sentence_usd": mean_human,
            "cost_ratio_vs_human": ratio,
            "pricing_as_of": pricing.get("as_of"),
            "pricing_source": cost.get("pricing_source"),
            "cost_mode": cost.get("cost_mode"),
            "coarse_acc": coarse_accuracy(rows, coarse_threshold),
            "cost_breakdown": cost,
        }
        write_json(run_dir / "metrics_with_cost.json", with_cost)
        table.append(with_cost)

    # write SUMMARY
    summary_md = repo / "results" / "SUMMARY.md"
    summary_csv = repo / "results" / "SUMMARY.csv"
    lines = [
        "# Experiment summary (quality + post-hoc cost)",
        "",
        f"Pricing as_of: `{pricing.get('as_of')}`",
        "",
        "| Model | Mode | n | Pearson r | MAE | RMSE | Parse fail rate | Tokens | $/sentence | vs human | Coarse acc |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for t in table:
        ut = t.get("usage_totals") or {}
        lines.append(
            "| {model} | {mode} | {n} | {r} | {mae} | {rmse} | {pfr} | {tok} | {cps} | {ratio} | {coarse} |".format(
                model=t.get("model_id"),
                mode=t.get("mode"),
                n=t.get("n_scored"),
                r=_fmt(t.get("pearson_r")),
                mae=_fmt(t.get("mae")),
                rmse=_fmt(t.get("rmse")),
                pfr=_fmt(t.get("parse_fail_rate")),
                tok=ut.get("total_tokens"),
                cps=_fmt(t.get("mean_cost_per_sentence_usd"), 6),
                ratio=_fmt(t.get("cost_ratio_vs_human"), 4),
                coarse=_fmt(t.get("coarse_acc")),
            )
        )
    lines.extend(
        [
            "",
            "Notes:",
            "- USD computed **after** eval from token logs × `configs/pricing.yaml`.",
            "- Raw `calls/` and `scores.jsonl` are not modified.",
            "- Self-host rows may have `cost_mode: estimated_gpu` (often $0 placeholder).",
            "",
        ]
    )
    summary_md.write_text("\n".join(lines), encoding="utf-8")

    fieldnames = [
        "model_id",
        "mode",
        "n_scored",
        "pearson_r",
        "mae",
        "rmse",
        "parse_fail_rate",
        "total_tokens",
        "mean_cost_per_sentence_usd",
        "cost_ratio_vs_human",
        "coarse_acc",
        "pricing_as_of",
    ]
    with summary_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for t in table:
            ut = t.get("usage_totals") or {}
            w.writerow(
                {
                    "model_id": t.get("model_id"),
                    "mode": t.get("mode"),
                    "n_scored": t.get("n_scored"),
                    "pearson_r": t.get("pearson_r"),
                    "mae": t.get("mae"),
                    "rmse": t.get("rmse"),
                    "parse_fail_rate": t.get("parse_fail_rate"),
                    "total_tokens": ut.get("total_tokens"),
                    "mean_cost_per_sentence_usd": t.get("mean_cost_per_sentence_usd"),
                    "cost_ratio_vs_human": t.get("cost_ratio_vs_human"),
                    "coarse_acc": t.get("coarse_acc"),
                    "pricing_as_of": t.get("pricing_as_of"),
                }
            )

    return {"n_runs": len(table), "table": table, "summary_md": str(summary_md), "summary_csv": str(summary_csv)}


def _fmt(x: Any, nd: int = 4) -> str:
    if x is None:
        return ""
    try:
        return f"{float(x):.{nd}f}"
    except (TypeError, ValueError):
        return str(x)
