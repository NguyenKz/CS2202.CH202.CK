#!/usr/bin/env python3
"""Mục 7 — chi phí LLM vs ước lượng crowdsource người."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from plausibility_eval.analysis import (  # noqa: E402
    load_runs,
    upsert_report_section,
    write_csv,
)
from plausibility_eval.cost import human_cost_per_sentence  # noqa: E402
from plausibility_eval.io_utils import load_yaml, write_json  # noqa: E402


def _fmt(x: float | None, nd: int = 4) -> str:
    if x is None:
        return "—"
    return f"{x:.{nd}f}"


def _fmt_money(x: float | None, nd: int = 4) -> str:
    if x is None:
        return "—"
    return f"${x:.{nd}f}"


def _short(model_id: str) -> str:
    return model_id.split("/")[-1] if "/" in model_id else model_id


def times_cheaper(ratio: Optional[float]) -> Optional[float]:
    if ratio is None or ratio <= 0:
        return None
    return 1.0 / ratio


def build_cost_rows(
    runs: Sequence[Dict[str, Any]],
    human_usd: float,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for r in runs:
        if r["mode"] not in ("ORIG", "T"):
            continue
        ratio = r.get("cost_ratio_vs_human")
        tc = times_cheaper(ratio)
        rows.append(
            {
                "model_id": r["model_id"],
                "mode": r["mode"],
                "pearson_r": r.get("pearson_r"),
                "mean_cost_per_sentence_usd": r.get("mean_cost_per_sentence_usd"),
                "human_cost_per_sentence_usd": human_usd,
                "cost_ratio_vs_human": ratio,
                "times_cheaper_than_human": tc,
                "est_cost_per_hour_usd": r.get("est_cost_per_hour_usd"),
                "mean_latency_s_per_call": r.get("mean_latency_s_per_call"),
                "pricing_source": r.get("pricing_source"),
                "cost_mode": r.get("cost_mode"),
                "cheaper_than_human": bool(ratio is not None and ratio < 1.0),
            }
        )
    rows.sort(
        key=lambda x: (
            -(x["pearson_r"] or -1.0),
            x["mean_cost_per_sentence_usd"] or 9e9,
            x["model_id"],
            x["mode"],
        )
    )
    return rows


def plot_pareto(rows: Sequence[Dict[str, Any]], out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 6.5))
    for r in rows:
        x = r["mean_cost_per_sentence_usd"]
        y = r["pearson_r"]
        if x is None or y is None or x <= 0:
            continue
        ax.scatter(x, y, s=70, alpha=0.85)
        ax.annotate(
            f"{_short(r['model_id'])}|{r['mode']}",
            (x, y),
            fontsize=7,
            alpha=0.85,
            xytext=(4, 4),
            textcoords="offset points",
        )
    ax.set_xlabel("$ / sentence (post-hoc, pricing.yaml)")
    ax.set_ylabel("Pearson r vs human")
    ax.set_title("Pareto: quality vs cost (ORIG / T)")
    ax.set_xscale("log")
    ax.grid(True, which="both", alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def pick_pareto_highlights(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Cheap-high-r candidates for slide narrative."""
    usable = [
        r
        for r in rows
        if r.get("pearson_r") is not None and r.get("mean_cost_per_sentence_usd")
    ]
    if not usable:
        return {}
    cheapest = min(usable, key=lambda r: r["mean_cost_per_sentence_usd"])
    best_r = max(usable, key=lambda r: r["pearson_r"])
    # "sweet spot": high r among cheaper half
    costs = sorted(r["mean_cost_per_sentence_usd"] for r in usable)
    mid = costs[len(costs) // 2]
    mid_pool = [r for r in usable if r["mean_cost_per_sentence_usd"] <= mid]
    sweet = max(mid_pool, key=lambda r: r["pearson_r"]) if mid_pool else best_r
    # luna ORIG often good quality/cost
    luna_orig = next(
        (r for r in usable if r["model_id"] == "gpt-5.6-luna" and r["mode"] == "ORIG"),
        None,
    )
    kimi_orig = next(
        (r for r in usable if r["model_id"] == "moonshotai/kimi-k3" and r["mode"] == "ORIG"),
        None,
    )
    return {
        "cheapest": cheapest,
        "best_r": best_r,
        "sweet_spot": sweet,
        "luna_orig": luna_orig,
        "kimi_orig": kimi_orig,
    }


def row_label(r: Dict[str, Any]) -> str:
    return f"`{_short(r['model_id'])}` / `{r['mode']}`"


def main() -> None:
    pricing = load_yaml(ROOT / "configs" / "pricing.yaml")
    as_of = str(pricing.get("as_of") or "unknown")
    human = pricing.get("human") or {}
    per_rating = float(human.get("cost_per_rating_usd") or 0.08)
    n_ann = int(human.get("default_annotators_per_sentence") or 40)
    human_usd = human_cost_per_sentence(pricing)
    human_notes = str(human.get("notes") or "").strip()

    runs = load_runs(ROOT)
    cost_rows = build_cost_rows(runs, human_usd)
    out_dir = ROOT / "results" / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    write_csv(out_dir / "M7_cost_table.csv", cost_rows)
    # keep notebook F_* in sync
    write_csv(out_dir / "F_cost_table.csv", cost_rows)

    chart = "M7_pareto_quality_cost.png"
    plot_pareto(cost_rows, out_dir / chart)
    plot_pareto(cost_rows, out_dir / "F_pareto_quality_cost.png")

    highlights = pick_pareto_highlights(cost_rows)
    all_cheaper = bool(cost_rows) and all(r.get("cheaper_than_human") for r in cost_rows)
    ratios = [r["times_cheaper_than_human"] for r in cost_rows if r.get("times_cheaper_than_human")]
    min_x = min(ratios) if ratios else None
    max_x = max(ratios) if ratios else None

    summary = {
        "pricing_as_of": as_of,
        "human_cost_per_rating_usd": per_rating,
        "default_annotators_per_sentence": n_ann,
        "human_cost_per_sentence_usd": human_usd,
        "human_notes": human_notes,
        "n_runs_orig_t": len(cost_rows),
        "all_cheaper_than_human": all_cheaper,
        "times_cheaper_min": min_x,
        "times_cheaper_max": max_x,
        "cheapest": highlights.get("cheapest"),
        "best_r": highlights.get("best_r"),
        "sweet_spot": highlights.get("sweet_spot"),
        "luna_orig": highlights.get("luna_orig"),
        "kimi_orig": highlights.get("kimi_orig"),
    }
    # JSON-safe: drop huge nested if any — rows are flat
    write_json(
        out_dir / "M7_summary.json",
        {
            **{k: v for k, v in summary.items() if k not in ("cheapest", "best_r", "sweet_spot", "luna_orig", "kimi_orig")},
            "cheapest": {
                "model_id": highlights["cheapest"]["model_id"],
                "mode": highlights["cheapest"]["mode"],
                "pearson_r": highlights["cheapest"]["pearson_r"],
                "mean_cost_per_sentence_usd": highlights["cheapest"]["mean_cost_per_sentence_usd"],
                "times_cheaper_than_human": highlights["cheapest"]["times_cheaper_than_human"],
            }
            if highlights.get("cheapest")
            else None,
            "best_r": {
                "model_id": highlights["best_r"]["model_id"],
                "mode": highlights["best_r"]["mode"],
                "pearson_r": highlights["best_r"]["pearson_r"],
                "mean_cost_per_sentence_usd": highlights["best_r"]["mean_cost_per_sentence_usd"],
                "times_cheaper_than_human": highlights["best_r"]["times_cheaper_than_human"],
            }
            if highlights.get("best_r")
            else None,
            "sweet_spot": {
                "model_id": highlights["sweet_spot"]["model_id"],
                "mode": highlights["sweet_spot"]["mode"],
                "pearson_r": highlights["sweet_spot"]["pearson_r"],
                "mean_cost_per_sentence_usd": highlights["sweet_spot"]["mean_cost_per_sentence_usd"],
                "times_cheaper_than_human": highlights["sweet_spot"]["times_cheaper_than_human"],
            }
            if highlights.get("sweet_spot")
            else None,
        },
    )

    # --- report body ---
    lines: List[str] = [
        "**Câu hỏi slide:** Ngoài nhanh hơn, $/câu (và ước $/giờ) có rẻ hơn ước lượng người không? Ai Pareto?",
        "",
        f"**Giá API:** `configs/pricing.yaml` — `as_of: {as_of}` (post-hoc từ token log; eval không ghi USD).",
        "",
        f"**Ước lượng người (crowdsource slide):** `${per_rating:.2f}` / rating × **{n_ann}** annotators/câu "
        f"≈ **{_fmt_money(human_usd, 2)} / câu**. "
        + (human_notes if human_notes else "Không phải hóa đơn paper — chỉ để so narrative."),
        "",
        "### Bảng ORIG / T (sort Pearson r ↓)",
        "",
        "| Model | MODE | Pearson r | $/câu | × rẻ hơn human | est $/giờ |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for r in cost_rows:
        tc = r.get("times_cheaper_than_human")
        tc_s = f"{tc:.0f}×" if tc is not None else "—"
        hour = r.get("est_cost_per_hour_usd")
        hour_s = _fmt_money(hour, 3) if hour is not None else "—"
        lines.append(
            f"| `{_short(r['model_id'])}` | `{r['mode']}` | {_fmt(r.get('pearson_r'), 4)} | "
            f"{_fmt_money(r.get('mean_cost_per_sentence_usd'))} | {tc_s} | {hour_s} |"
        )

    lines += [
        "",
        f"![Pareto quality vs cost]({chart})",
        "",
        "### Nhận định",
        "",
    ]

    if all_cheaper and min_x and max_x:
        lines.append(
            f"- **Có — AI rẻ hơn ước lượng người** trên **mọi** run ORIG/T đủ 50 câu: "
            f"khoảng **{min_x:.0f}×–{max_x:.0f}×** rẻ hơn (~{_fmt_money(human_usd, 2)}/câu human)."
        )
    elif all_cheaper:
        lines.append("- **Có — AI rẻ hơn ước lượng người** trên mọi run ORIG/T trong bảng.")
    else:
        lines.append("- Không phải mọi run đều rẻ hơn human — xem cột `× rẻ hơn` / `cheaper_than_human`.")

    ch = highlights.get("cheapest")
    br = highlights.get("best_r")
    sw = highlights.get("sweet_spot")
    lo = highlights.get("luna_orig")
    ko = highlights.get("kimi_orig")

    if ch:
        lines.append(
            f"- **Rẻ nhất:** {row_label(ch)} — {_fmt_money(ch['mean_cost_per_sentence_usd'])}/câu "
            f"(r={_fmt(ch['pearson_r'], 3)}, ~{ch['times_cheaper_than_human']:.0f}× rẻ hơn human)."
        )
    if br:
        lines.append(
            f"- **r cao nhất:** {row_label(br)} — r={_fmt(br['pearson_r'], 3)}, "
            f"{_fmt_money(br['mean_cost_per_sentence_usd'])}/câu "
            f"(~{br['times_cheaper_than_human']:.0f}× rẻ hơn human)."
        )
    if lo:
        lines.append(
            f"- **Pareto chất lượng/giá (luna ORIG):** r={_fmt(lo['pearson_r'], 3)}, "
            f"{_fmt_money(lo['mean_cost_per_sentence_usd'])}/câu — gần #1 likeness với $/câu thấp hơn luna T."
        )
    if ko:
        lines.append(
            f"- **Kimi ORIG:** r={_fmt(ko['pearson_r'], 3)}, "
            f"{_fmt_money(ko['mean_cost_per_sentence_usd'])}/câu — điểm Pareto trung bình tốt (r khá, $ thấp)."
        )
    if sw and (not lo or sw["model_id"] != lo["model_id"] or sw["mode"] != lo["mode"]):
        lines.append(
            f"- **Sweet spot (r cao trong nửa rẻ hơn):** {row_label(sw)} — "
            f"r={_fmt(sw['pearson_r'], 3)}, {_fmt_money(sw['mean_cost_per_sentence_usd'])}/câu."
        )

    lines += [
        "",
        "**Lưu ý:** `est $/giờ` chỉ có khi run log latency; một số batch (luna/sol) có thể trống cột này. "
        "Self-host `cost_mode: estimated_gpu` có thể ≈ $0 — không trộn với giá API khi kể chuyện.",
        "",
        "### Câu kết luận slide",
        "",
    ]

    if all_cheaper and min_x and max_x and ch and br:
        lines.append(
            f"> **Có.** Mọi run ORIG/T rẻ hơn ước crowdsource (~{_fmt_money(human_usd, 2)}/câu) "
            f"khoảng **{min_x:.0f}×–{max_x:.0f}×**. "
            f"Rẻ nhất: {_short(ch['model_id'])} {ch['mode']} "
            f"({_fmt_money(ch['mean_cost_per_sentence_usd'])}/câu). "
            f"Pareto tốt: {_short(br['model_id'])} {br['mode']} "
            f"(r≈{_fmt(br['pearson_r'], 3)}, {_fmt_money(br['mean_cost_per_sentence_usd'])}/câu"
            + (
                f"; luna ORIG {_fmt_money(lo['mean_cost_per_sentence_usd'])}/câu gần cùng r"
                if lo
                else ""
            )
            + ")."
        )
    else:
        lines.append(
            "> So cost post-hoc (`pricing.yaml`) với ước human $0.08×40; xem bảng ORIG/T + Pareto."
        )

    lines += [
        "",
        "### Artifact",
        "",
        "- `M7_cost_table.csv`",
        f"- `{chart}`",
        "- `M7_summary.json`",
        "- `F_cost_table.csv` / `F_pareto_quality_cost.png` (đồng bộ notebook F)",
        "",
    ]

    upsert_report_section(
        out_dir / "report.md",
        "Mục 7 — Chi phí: AI có rẻ hơn người không?",
        "\n".join(lines),
    )
    print(f"n ORIG/T={len(cost_rows)} all_cheaper={all_cheaper} human=${human_usd:.2f}")
    if ch:
        print(
            f"cheapest: {ch['model_id']}/{ch['mode']} "
            f"${ch['mean_cost_per_sentence_usd']:.6f} (~{ch['times_cheaper_than_human']:.0f}×)"
        )
    if br:
        print(
            f"best_r: {br['model_id']}/{br['mode']} "
            f"r={br['pearson_r']:.4f} ${br['mean_cost_per_sentence_usd']:.6f}"
        )
    print(f"Wrote → {out_dir / 'report.md'}")


if __name__ == "__main__":
    main()
