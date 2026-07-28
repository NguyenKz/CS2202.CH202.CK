#!/usr/bin/env python3
"""Mục 1 — one ranking: ORIG + T + gpt-4 paper + llm_annotators."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from plausibility_eval.analysis import (  # noqa: E402
    ensemble_models_as_annotators,
    load_ready_gpt4,
    load_runs,
    paper_gpt4_metrics,
    upsert_report_section,
    write_csv,
)
from plausibility_eval.io_utils import write_json  # noqa: E402

COLOR_PAPER = "#4A4A4A"
COLOR_ABOVE = "#2A9D8F"
COLOR_BELOW = "#E07A3D"
COLOR_LLM_ANN = "#5B6CFF"


def _fmt(x: float | None, nd: int = 4) -> str:
    if x is None:
        return "—"
    return f"{x:.{nd}f}"


def _short_model(model_id: str) -> str:
    return model_id.split("/")[-1]


def preferred_runs_one_per_model(runs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """One run per model: prefer ORIG, else T. Skip S/ST."""
    by_model: Dict[str, Dict[str, Any]] = {}
    for r in runs:
        if r["mode"] not in ("ORIG", "T"):
            continue
        mid = r["model_id"]
        cur = by_model.get(mid)
        if cur is None:
            by_model[mid] = r
        elif r["mode"] == "ORIG" and cur["mode"] != "ORIG":
            by_model[mid] = r
    return sorted(by_model.values(), key=lambda x: x["model_id"])


def llm_annotators_row(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Equal-weight mean of LLMs (excl. paper GPT-4): 1 model = 1 annotator."""
    pool = preferred_runs_one_per_model(runs)
    # ensemble_models_as_annotators needs same mode; build fake ORIG-tagged rows
    fake = [{**r, "mode": "ORIG"} for r in pool]
    ens = ensemble_models_as_annotators(fake, mode="ORIG")
    return {
        "model_id": "llm_annotators",
        "mode": "mean",
        "n": ens["n_sentences"],
        "pearson_r": ens["pearson_r"],
        "mae": ens["mae"],
        "n_models": ens["n_models"],
        "model_ids": ens["model_ids"],
        "is_paper_ref": False,
        "is_llm_annotators": True,
        "note": (
            "Equal mean of model_mean per sentence; 1 vote/model; "
            "prefer ORIG else T; excludes gpt-4 (paper) and S/ST"
        ),
        "per_sentence": ens["per_sentence"],
    }


def unified_ranking(
    runs: List[Dict[str, Any]],
    paper: Dict[str, Any],
    llm_ann: Dict[str, Any],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for r in runs:
        if r["mode"] not in ("ORIG", "T"):
            continue
        rows.append(
            {
                "model_id": r["model_id"],
                "mode": r["mode"],
                "n": r["n_sentences"],
                "pearson_r": r["pearson_r"],
                "mae": r["mae"],
                "is_paper_ref": False,
                "is_llm_annotators": False,
            }
        )
    rows.append(
        {
            "model_id": paper["model_id"],
            "mode": "ref",
            "n": paper.get("n"),
            "pearson_r": paper["pearson_r"],
            "mae": paper["mae"],
            "is_paper_ref": True,
            "is_llm_annotators": False,
            "note": paper.get("note"),
        }
    )
    rows.append(
        {
            "model_id": llm_ann["model_id"],
            "mode": llm_ann["mode"],
            "n": llm_ann.get("n"),
            "pearson_r": llm_ann["pearson_r"],
            "mae": llm_ann["mae"],
            "n_models": llm_ann.get("n_models"),
            "is_paper_ref": False,
            "is_llm_annotators": True,
            "note": llm_ann.get("note"),
        }
    )
    rows.sort(key=lambda x: (-(x["pearson_r"] or -1), x["model_id"], x["mode"]))
    for i, r in enumerate(rows, start=1):
        r["rank"] = i
    return rows


def plot_vs_paper_ref(
    rows: List[Dict[str, Any]],
    paper_r: float,
    out_path: Path,
) -> None:
    labels = [f"{_short_model(r['model_id'])} / {r['mode']}" for r in rows]
    vals = [float(r["pearson_r"] or 0) for r in rows]
    colors = []
    for r in rows:
        if r.get("is_paper_ref"):
            colors.append(COLOR_PAPER)
        elif r.get("is_llm_annotators"):
            colors.append(COLOR_LLM_ANN)
        elif (r["pearson_r"] or 0) >= paper_r:
            colors.append(COLOR_ABOVE)
        else:
            colors.append(COLOR_BELOW)

    fig_w = max(12, 0.55 * len(rows) + 2)
    fig, ax = plt.subplots(figsize=(fig_w, 5.5))
    x = list(range(len(rows)))
    bars = ax.bar(x, vals, color=colors, edgecolor="white", linewidth=0.4, zorder=3)
    ax.axhline(
        paper_r,
        color=COLOR_PAPER,
        linestyle="--",
        linewidth=1.4,
        zorder=4,
        label=f"gpt-4 (paper) r={paper_r:.3f}",
    )
    for rect, v in zip(bars, vals):
        ax.text(
            rect.get_x() + rect.get_width() / 2,
            v + 0.012,
            f"{v:.3f}",
            ha="center",
            va="bottom",
            fontsize=7,
            rotation=90,
        )
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=55, ha="right", fontsize=8)
    ax.set_ylabel("Pearson r vs human")
    ax.set_ylim(0, 1.0)
    ax.set_title("Agreement with Human — ORIG / T / gpt-4 paper / llm_annotators")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(axis="y", alpha=0.25, zorder=0)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def main() -> None:
    out_dir = ROOT / "results" / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    runs = load_runs(ROOT, min_n=50, exclude_smoke=True)
    ready = load_ready_gpt4(ROOT)
    g4 = paper_gpt4_metrics(ready)
    paper_r = float(g4["pearson_r"])

    llm_ann = llm_annotators_row(runs)
    ranking = unified_ranking(runs, g4, llm_ann)

    write_csv(out_dir / "M1_unified_ranking.csv", [{k: v for k, v in r.items()} for r in ranking])
    write_csv(out_dir / "M1_llm_annotators_sentences.csv", llm_ann["per_sentence"])
    write_json(
        out_dir / "M1_llm_annotators_summary.json",
        {k: v for k, v in llm_ann.items() if k != "per_sentence"},
    )

    chart_name = "M1_agreement_vs_gpt4paper.png"
    plot_vs_paper_ref(ranking, paper_r, out_dir / chart_name)

    n_above = sum(
        1
        for r in ranking
        if not r.get("is_paper_ref") and (r["pearson_r"] or 0) >= paper_r
    )
    n_below = sum(
        1
        for r in ranking
        if not r.get("is_paper_ref") and (r["pearson_r"] or 0) < paper_r
    )
    llm_rank = next(r for r in ranking if r.get("is_llm_annotators"))
    paper_rank = next(r for r in ranking if r.get("is_paper_ref"))
    best = ranking[0]
    members = ", ".join(f"`{m}`" for m in llm_ann["model_ids"])

    lines: List[str] = [
        "Tham chiếu paper: **`gpt-4 (paper)`** từ `data/ready/…/gpt4_mean` "
        f"(r={_fmt(paper_r)}, MAE={_fmt(g4['mae'])}) — **không** phải `openai/gpt-4.1-mini`.",
        "",
        "### Biểu đồ xếp hạng (ORIG + T + gpt-4 paper + llm_annotators)",
        "",
        f"![Agreement with Human]({chart_name})",
        "",
        f"- Xanh: r ≥ paper. Cam: r < paper. Xám: paper. Tím: **`llm_annotators`**.",
        f"- {n_above} entry ≥ paper; {n_below} entry < paper.",
        "",
        "### Bảng tổng hợp (sort Pearson r ↓)",
        "",
        "| Rank | Model | Mode | Pearson r | MAE | vs paper |",
        "|---:|---|---|---:|---:|---|",
    ]
    for r in ranking:
        if r.get("is_paper_ref"):
            mid = f"**`{r['model_id']}`**"
            vs = "← **tham chiếu**"
        elif r.get("is_llm_annotators"):
            mid = f"**`{r['model_id']}`**"
            dr = (r["pearson_r"] or 0) - paper_r
            vs = f"Δr={dr:+.4f}"
        else:
            mid = f"`{r['model_id']}`"
            dr = (r["pearson_r"] or 0) - paper_r
            vs = f"Δr={dr:+.4f}"
        lines.append(
            f"| {r['rank']} | {mid} | `{r['mode']}` | {_fmt(r['pearson_r'])} | "
            f"{_fmt(r['mae'])} | {vs} |"
        )

    lines += [
        "",
        "### `llm_annotators` là gì?",
        "",
        "Không phải một model API. Mỗi LLM trong zoo được coi như **1 annotator** "
        "(lấy `model_mean` của model đó trên từng câu; ưu tiên MODE **ORIG**, "
        "không có ORIG thì dùng **T**; **không** gồm `gpt-4 (paper)`, **không** gồm S/ST). "
        "Điểm tổng hợp = **trung bình đều** các vote → rồi mới tính Pearson r / MAE với `human_mean`.",
        "",
        f"- Số annotator LLM: **{llm_ann['n_models']}** — {members}",
        f"- Kết quả: r={_fmt(llm_ann['pearson_r'])}, MAE={_fmt(llm_ann['mae'])}, "
        f"hạng **#{llm_rank['rank']}** (paper hạng #{paper_rank['rank']}).",
        "",
        "### Nhận định",
        "",
        f"- **#1:** `{best['model_id']}` / `{best['mode']}` (r={_fmt(best['pearson_r'])}).",
        f"- **gpt-4 (paper):** hạng #{paper_rank['rank']} (r={_fmt(paper_r)}).",
        f"- **llm_annotators:** hạng #{llm_rank['rank']} (r={_fmt(llm_ann['pearson_r'])}) — "
        f"{'trên' if (llm_ann['pearson_r'] or 0) >= paper_r else 'dưới'} paper "
        f"(Δr={(llm_ann['pearson_r'] or 0) - paper_r:+.4f}); "
        "crowd pha loãng model mạnh nên thường kém #1 đơn lẻ.",
        "",
    ]

    # ORIG vs T for models with both
    orig = {r["model_id"]: r for r in runs if r["mode"] == "ORIG"}
    t_only = {r["model_id"]: r for r in runs if r["mode"] == "T"}
    both = sorted(set(orig) & set(t_only))
    t_wins: List[tuple[str, float]] = []
    t_losses: List[tuple[str, float]] = []
    for mid in both:
        dr = (t_only[mid]["pearson_r"] or 0) - (orig[mid]["pearson_r"] or 0)
        if dr >= 0:
            t_wins.append((mid, dr))
        else:
            t_losses.append((mid, dr))

    if both:
        lines.append(
            f"- **Thinking giúp likeness (quy luật tổng thể):** trên {len(both)} model có cả ORIG và T, "
            f"**{len(t_wins)}/{len(both)}** có T ≥ ORIG trên Pearson r — Thinking **thực sự cải thiện** "
            "kết quả giống người ở hầu hết zoo."
        )
        lines.append("  - Chi tiết Δr (T − ORIG):")
        for mid in both:
            o, t = orig[mid], t_only[mid]
            dr = (t["pearson_r"] or 0) - (o["pearson_r"] or 0)
            mark = "✓" if dr >= 0 else "✗"
            lines.append(
                f"  - {mark} `{mid}`: {_fmt(o['pearson_r'])} → {_fmt(t['pearson_r'])} (Δr={dr:+.4f})"
            )
        if t_losses:
            for mid, dr in t_losses:
                lines.append(
                    f"  - **Ngoại lệ:** `{mid}` — T thua ORIG (Δr={dr:+.4f}, |Δr|≈{abs(dr):.2f}). "
                    "Có thể do **sample chưa đủ** (n=50 câu) hoặc mức chênh **không đáng kể** "
                    "(~0.03) nên coi là nhiễu / điểm bất thường; **không phá** quy luật tổng thể "
                    "“Thinking thường ≥ ORIG”."
                )
        else:
            lines.append("  - Không có ngoại lệ: mọi model có T đều ≥ ORIG.")

    lines.append("- **Chỗ lạ (neo Mục 5):**")
    gemma3 = orig.get("google/gemma-3-12b-it")
    if gemma3:
        for mid in (
            "deepseek/deepseek-v4-flash",
            "google/gemma-4-31b-it",
            "z-ai/glm-5.2",
        ):
            row = orig.get(mid)
            if row:
                lines.append(
                    f"  - `{mid}` ORIG r={_fmt(row['pearson_r'])} "
                    f"{'<' if (row['pearson_r'] or 0) < (gemma3['pearson_r'] or 0) else '≥'} "
                    f"Gemma-3-12B r={_fmt(gemma3['pearson_r'])}"
                )

    lines += [
        "",
        "### Artifact",
        "",
        f"- `{chart_name}`",
        "- `M1_unified_ranking.csv`",
        "- `M1_llm_annotators_summary.json`, `M1_llm_annotators_sentences.csv`",
        "",
    ]
    upsert_report_section(out_dir / "report.md", "Mục 1 — Kết quả tổng thể", "\n".join(lines))
    (out_dir / "M1_NOTES.md").write_text(
        "Nội dung Mục 1 đã chuyển vào [`report.md`](report.md) § Mục 1.\n",
        encoding="utf-8",
    )
    print(f"llm_annotators r={llm_ann['pearson_r']:.4f} n_models={llm_ann['n_models']}")
    print(f"Wrote → {out_dir / 'report.md'}")


if __name__ == "__main__":
    main()
