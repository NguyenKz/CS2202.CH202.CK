#!/usr/bin/env python3
"""Mục 6 — trọng điểm GPT-4 (paper) vs model zoo."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from plausibility_eval.analysis import (  # noqa: E402
    CONDS,
    calibration_stats,
    compare_to_paper_gpt4,
    load_ready_gpt4,
    load_runs,
    paper_gpt4_by_condition,
    paper_gpt4_metrics,
    ranking_with_gpt4,
    residual_overlap_vs_gpt4,
    upsert_report_section,
    write_csv,
)
from plausibility_eval.io_utils import write_json  # noqa: E402

COMPARE_MODELS: Tuple[str, ...] = (
    "gpt-5.6-luna",
    "gpt-5.6-sol",
    "moonshotai/kimi-k3",
    "google/gemma-3-12b-it",
    "openai/gpt-4.1-mini",
)

CALIBRATION_ROWS: Tuple[Tuple[str, str], ...] = (
    ("gpt-4 (paper)", "ref"),
    ("gpt-5.6-luna", "ORIG"),
    ("gpt-5.6-sol", "ORIG"),
    ("moonshotai/kimi-k3", "ORIG"),
    ("openai/gpt-4.1-mini", "ORIG"),
)

COND_GLOSS = {
    "all": "object khớp kỳ vọng (baseline)",
    "global": "object liên quan nhưng kém khớp ngữ cảnh",
    "animate": "đổi animate/inanimate của object",
    "plural": "object số nhiều",
    "name": "object là tên riêng",
}


def _fmt(x: float | None, nd: int = 3) -> str:
    if x is None:
        return "—"
    return f"{x:.{nd}f}"


def _short(model_id: str) -> str:
    return model_id.split("/")[-1] if "/" in model_id else model_id


def plot_calibration_compare(rows: Sequence[Dict[str, Any]], out_path: Path) -> None:
    labels = [f"{_short(r['model_id'])}\n{r.get('mode', '')}" for r in rows]
    biases = [r.get("bias_model_minus_human") or 0.0 for r in rows]
    fig, ax = plt.subplots(figsize=(max(7, len(labels) * 1.2), 4.5))
    colors = ["#E45756" if "paper" in r["model_id"] else "#4C78A8" for r in rows]
    ax.bar(range(len(labels)), biases, color=colors)
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("bias (model − human)")
    ax.set_title("Calibration: GPT-4 paper vs modern models (ORIG)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def build_plain_explanation_lines() -> List[str]:
    return [
        "### Giải thích dễ hiểu",
        "",
        "**GPT-4 (paper)** không phải model API trong zoo — là **điểm trung bình GPT-4** tác giả paper chạy "
        "trên cùng 50 câu mem_enc (`gpt4_mean` trong `data/ready/`), cùng tinh thần prompt ORIG.",
        "",
        "**Vì sao vẫn “mạnh”?** Trên n=50:",
        "",
        "- **MAE thấp nhất** trong nhóm top (~0.58) → sai số tuyệt đối từng câu nhỏ.",
        "- **Bias thấp nhất** (+0.06) → **ít bơm điểm** (xem thuật ngữ Mục 5) so luna/sol (+0.3–0.4).",
        "- **Không #1 Pearson:** luna ORIG/T **vượt r** (~0.78) — thắng **thứ tự câu**, không thắng **calibration mức điểm**.",
        "",
        "**Cấm nhầm:** `openai/gpt-4.1-mini` (run zoo, r≈0.53) **≠** GPT-4 paper (r≈0.75). "
        "Nhãn “GPT-4” trên API không đảm bảo giống baseline paper.",
        "",
    ]


def build_summary_lines(paper: Dict[str, Any], compare_rows: Sequence[Dict[str, Any]]) -> List[str]:
    luna = next((r for r in compare_rows if r["model_id"] == "gpt-5.6-luna"), None)
    mini = next((r for r in compare_rows if r["model_id"] == "openai/gpt-4.1-mini"), None)
    lines = [
        "### Tổng hợp",
        "",
        f"**GPT-4 paper vẫn mạnh ở đâu?** r≈**{_fmt(paper.get('pearson_r'))}**, MAE≈**{_fmt(paper.get('mae'))}**, "
        f"bias≈**{_fmt(paper.get('bias_model_minus_human'))}** — **elite calibration** (ít bơm, MAE tốt) trong top zoo.",
        "",
        "**Yếu / không bất bại ở đâu?**",
        "",
    ]
    if luna:
        lines.append(
            f"- **luna** r cao hơn paper (Δr={_fmt(luna.get('delta_r_vs_paper'), 4)}) "
            f"nhưng bias lớn hơn (Δbias={_fmt(luna.get('delta_bias_vs_paper'), 4)}) → trade-off thứ tự vs mức điểm."
        )
    lines += [
        "- **Không #1 Pearson** trên mem_enc — narrative “GPT-4 vô đối” cần chỉnh.",
        "- Residual overlap: model mới vẫn **thắng paper trên một số câu** (|err|<1 vs human).",
    ]
    if mini:
        lines.append(
            f"- **gpt-4.1-mini** r≈{_fmt(mini.get('pearson_r'))} — chứng minh nhãn GPT-4 ≠ GPT-4 paper data."
        )
    lines += [
        "",
        "*Giả thuyết (chưa chứng minh từ n=50):* era huấn luyện/align “chat-rating / plausibility” (GPT-4 paper) "
        "calibrate Likert tốt hơn model coding/agent (luna/sol) — data ủng hộ **câu chuyện bias/MAE**, không chứng minh mixture.",
        "",
        "**Liên hệ Mục 5:** frontier thua Gemma-3 là paradox **quy mô ≠ likeness**; Mục 6 là case **baseline paper era** "
        "vẫn elite về **MAE + ít bơm** dù model mới thắng **r**.",
        "",
    ]
    return lines


def main() -> None:
    out_dir = ROOT / "results" / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    runs = load_runs(ROOT, min_n=50, exclude_smoke=True)
    ready = load_ready_gpt4(ROOT)

    g4 = paper_gpt4_metrics(ready)
    fake_rows = [
        {"human_mean": r["human_mean"], "model_mean": r["gpt4_mean"]}
        for r in ready
        if r.get("gpt4_mean") is not None
    ]
    cal4 = calibration_stats(fake_rows)
    paper_payload = {
        **g4,
        "bias_model_minus_human": cal4.get("bias_model_minus_human"),
        "slope": cal4.get("slope"),
        "source": "data/ready/mem_enc_human_and_gpt.jsonl → gpt4_mean",
        "warning": "NOT openai/gpt-4.1-mini from zoo runs",
    }
    write_json(out_dir / "M6_gpt4_paper_metrics.json", paper_payload)

    compare_rows = compare_to_paper_gpt4(
        runs, ready, compare_models=COMPARE_MODELS, mode="ORIG"
    )
    write_csv(out_dir / "M6_compare_vs_paper.csv", compare_rows)

    by_cond = paper_gpt4_by_condition(ready)
    cond_rows = [
        {"condition": c, **by_cond.get(c, {}), "gloss": COND_GLOSS.get(c, "")}
        for c in CONDS
    ]
    write_csv(out_dir / "M6_gpt4_by_condition.csv", cond_rows)

    overlap = residual_overlap_vs_gpt4(runs, ready, mode="ORIG", err_thresh=1.0)
    write_csv(out_dir / "M6_residual_overlap.csv", overlap)

    rank = ranking_with_gpt4(runs, ready, modes=("ORIG", "T"))
    rank_orig = [x for x in rank if x["mode"] in ("ORIG", "ORIG*")]
    paper_rank = next(
        (i + 1 for i, x in enumerate(rank_orig) if x["model_id"] == "gpt-4 (paper)"),
        None,
    )

    cal_chart_rows: List[Dict[str, Any]] = [
        {
            "model_id": "gpt-4 (paper)",
            "mode": "ref",
            "bias_model_minus_human": cal4.get("bias_model_minus_human"),
        }
    ]
    rank_by = {(x["model_id"], x["mode"]): x for x in rank}
    for mid, mode in CALIBRATION_ROWS[1:]:
        row = rank_by.get((mid, mode))
        if row:
            cal_chart_rows.append(row)

    chart = "M6_calibration_compare.png"
    plot_calibration_compare(cal_chart_rows, out_dir / chart)

    summary_payload = {
        "paper": paper_payload,
        "paper_rank_orig": paper_rank,
        "compare_vs_paper": compare_rows,
        "gpt4_by_condition": by_cond,
        "residual_overlap": overlap,
    }
    write_json(out_dir / "M6_summary.json", summary_payload)

    # --- report ---
    pr = paper_payload.get("pearson_r")
    pm = paper_payload.get("mae")
    pb = paper_payload.get("bias_model_minus_human")
    ps = paper_payload.get("slope")

    lines: List[str] = [
        "**Câu hỏi slide:** Vì sao GPT-4 (paper) vẫn rất mạnh so với nhiều model mới?",
        "",
        "**Nguồn:** `data/ready/mem_enc_human_and_gpt.jsonl` → `gpt4_mean` (Amouyal et al.; resample paper). "
        "**Không** dùng `openai/gpt-4.1-mini` trong zoo.",
        "",
        f"**Neo GPT-4 paper:** r≈**{_fmt(pr)}**, MAE≈**{_fmt(pm)}**, bias≈**{_fmt(pb)}**, độ dốc≈**{_fmt(ps)}** "
        f"(hạng Pearson ORIG-like: **#{paper_rank}** / {len(rank_orig)}).",
        "",
        "### Bảng so sánh vs GPT-4 paper (ORIG)",
        "",
        "| Model | r | Δr | MAE | ΔMAE | bias | Δbias |",
        "|---|---:|---:|---:|---:|---:|---:|",
        f"| **`gpt-4 (paper)`** | {_fmt(pr)} | — | {_fmt(pm)} | — | {_fmt(pb)} | — |",
    ]
    for row in compare_rows:
        if row["model_id"] not in ("gpt-5.6-luna", "gpt-5.6-sol", "moonshotai/kimi-k3"):
            continue
        lines.append(
            f"| `{_short(row['model_id'])}` | {_fmt(row['pearson_r'])} | "
            f"{_fmt(row['delta_r_vs_paper'], 4)} | {_fmt(row['mae'])} | "
            f"{_fmt(row['delta_mae_vs_paper'])} | {_fmt(row['bias_model_minus_human'])} | "
            f"{_fmt(row['delta_bias_vs_paper'])} |"
        )

    lines.append("")
    lines += build_plain_explanation_lines()

    lines += [
        "### Calibration — bias (model − human)",
        "",
        "| Model | MODE | r | MAE | bias | độ dốc |",
        "|---|---|---:|---:|---:|---:|",
        f"| `gpt-4 (paper)` | ref | {_fmt(pr)} | {_fmt(pm)} | {_fmt(pb)} | {_fmt(ps)} |",
    ]
    for mid, mode in CALIBRATION_ROWS[1:]:
        row = rank_by.get((mid, mode))
        if row:
            lines.append(
                f"| `{_short(mid)}` | `{mode}` | {_fmt(row['pearson_r'])} | {_fmt(row['mae'])} | "
                f"{_fmt(row['bias_model_minus_human'])} | {_fmt(row['slope'])} |"
            )

    lines += [
        "",
        f"![Calibration compare]({chart})",
        "",
        "**Nhận định:** GPT-4 paper **ít bơm điểm nhất** (+0.06); luna/sol **+0.31–0.36** — "
        "thắng thứ tự câu (r) nhưng **lệch mức crowdsource** hơn paper.",
        "",
        "### GPT-4 paper theo condition",
        "",
        "| condition | n | r | MAE |",
        "|---|---:|---:|---:|",
    ]
    for row in cond_rows:
        lines.append(
            f"| `{row['condition']}` ({row.get('gloss', '')}) | {row.get('n', '—')} | "
            f"{_fmt(row.get('pearson_r'))} | {_fmt(row.get('mae'))} |"
        )

    lines += [
        "",
        "GPT-4 paper **ổn trên mọi condition** (r ≥ ~0.62); MAE cao nhất ở `global` (~0.71) — khớp Mục 2 (condition khó).",
        "",
        "### Residual overlap (|err−human| < 1.0, ORIG)",
        "",
        "Đếm câu mà **GPT-4 paper gần human hơn** model (`gpt4_ok_model_bad`) vs ngược lại (`model_ok_gpt4_bad`):",
        "",
        "| Model | GPT-4 tốt hơn | Model tốt hơn GPT-4 | Cả hai đều lệch |",
        "|---|---:|---:|---:|",
    ]
    focus_overlap = [r for r in overlap if r["model_id"] in COMPARE_MODELS[:3]]
    for row in focus_overlap:
        lines.append(
            f"| `{_short(row['model_id'])}` | {row['gpt4_ok_model_bad']} | "
            f"{row['model_ok_gpt4_bad']} | {row['both_bad']} |"
        )

    lines += [
        "",
        "luna: paper thua model trên vài câu (3) nhưng paper thắng model trên **8** câu (threshold 1.0) — "
        "không phủ định paper baseline; cho thấy model mới **không dominate mọi câu**.",
        "",
        "### Cảnh báo: gpt-4.1-mini",
        "",
    ]
    mini_row = next((r for r in compare_rows if r["model_id"] == "openai/gpt-4.1-mini"), None)
    if mini_row:
        lines.append(
            f"| `{_short(mini_row['model_id'])}` | r={_fmt(mini_row['pearson_r'])} | "
            f"Δr vs paper={_fmt(mini_row['delta_r_vs_paper'], 4)} | MAE={_fmt(mini_row['mae'])} | "
            f"bias={_fmt(mini_row['bias_model_minus_human'])} |"
        )
        lines.append("")
        lines.append(
            "→ Run zoo **gpt-4.1-mini** (r≈0.53) **không thay thế** GPT-4 paper (r≈0.75) khi nói baseline paper."
        )
    lines.append("")

    lines += build_summary_lines(paper_payload, compare_rows)

    lines += [
        "### Câu kết luận slide",
        "",
        f"> GPT-4 paper đạt r≈{_fmt(pr)} / MAE≈{_fmt(pm)} / bias≈+{_fmt(pb, 2)}; "
        "luna cao hơn Pearson (≈0.778) nhưng bias lớn hơn (+0.31). "
        "*Giả thuyết:* model era coding/agent thắng **thứ tự câu** nhưng mất **calibration Likert** so baseline chat-rating; "
        "paper GPT-4 vẫn elite **MAE + ít bơm**. Xem thêm [Mục 5](report.md) (frontier vs Gemma-3).",
        "",
        "### Artifact",
        "",
        f"- `{chart}`",
        "- `M6_gpt4_paper_metrics.json`",
        "- `M6_compare_vs_paper.csv`",
        "- `M6_gpt4_by_condition.csv`",
        "- `M6_residual_overlap.csv`",
        "- `M6_summary.json`",
        "- `E_orig_ranking_with_gpt4.png` (ranking tổng từ full analysis)",
        "",
    ]

    upsert_report_section(
        out_dir / "report.md",
        "Mục 6 — Trọng điểm GPT-4 paper",
        "\n".join(lines),
    )
    print(f"GPT-4 paper r={pr:.4f} rank=#{paper_rank}")
    print(f"Wrote → {out_dir / 'report.md'}")


if __name__ == "__main__":
    main()
