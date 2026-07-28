#!/usr/bin/env python3
"""Mục 5 — ai tốt / ai tệ + nghịch lý frontier vs Gemma-3-12B."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from plausibility_eval.analysis import (  # noqa: E402
    CONDS,
    calibration_stats,
    condition_delta_vs_baseline,
    head_to_head_cases,
    load_runs,
    paradox_vs_baseline,
    thinking_deltas,
    upsert_report_section,
    write_csv,
)
from plausibility_eval.io_utils import write_json  # noqa: E402

BASELINE_MODEL = "google/gemma-3-12b-it"
BASELINE_MODE = "ORIG"

FOCUS_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("deepseek/deepseek-v4-flash", "ORIG"),
    ("google/gemma-4-31b-it", "ORIG"),
    ("z-ai/glm-5.2", "ORIG"),
    ("moonshotai/kimi-k3", "ORIG"),
)

CALIBRATION_MODELS: Tuple[Tuple[str, str], ...] = (
    ("gpt-5.6-luna", "ORIG"),
    (BASELINE_MODEL, BASELINE_MODE),
    ("deepseek/deepseek-v4-flash", "ORIG"),
    ("google/gemma-4-31b-it", "ORIG"),
    ("z-ai/glm-5.2", "ORIG"),
    ("moonshotai/kimi-k3", "ORIG"),
    ("deepseek/deepseek-v4-flash", "T"),
    ("google/gemma-4-31b-it", "T"),
)

CASE_CHALLENGERS: Tuple[Tuple[str, str], ...] = (
    ("deepseek/deepseek-v4-flash", "ORIG"),
    ("google/gemma-4-31b-it", "ORIG"),
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
    return model_id.split("/")[-1]


def find_run(runs: Sequence[Dict[str, Any]], model_id: str, mode: str) -> Optional[Dict[str, Any]]:
    for r in runs:
        if r["model_id"] == model_id and r["mode"] == mode:
            return r
    return None


def plot_calibration_bias_slope(
    rows: Sequence[Dict[str, Any]],
    out_path: Path,
) -> None:
    labels = [f"{_short(r['model_id'])}\n{r['mode']}" for r in rows]
    biases = [r.get("bias_model_minus_human") or 0.0 for r in rows]
    slopes = [r.get("slope") or 0.0 for r in rows]
    x = np.arange(len(labels))
    width = 0.35
    fig, ax = plt.subplots(figsize=(max(8, len(labels) * 1.1), 5))
    ax.bar(x - width / 2, biases, width, label="bias (model−human)", color="#4C72B0")
    ax.bar(x + width / 2, slopes, width, label="slope (model~human)", color="#DD8452")
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.axhline(1, color="gray", linewidth=0.8, linestyle="--", alpha=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("Value")
    ax.set_title("Calibration vs Gemma-3 baseline context (frontier subset)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def build_plain_explanation_lines() -> List[str]:
    return [
        "### Giải thích dễ hiểu",
        "",
        "**Câu hỏi thực tế:** Model “mạnh”, “frontier”, nhiều tỷ tham số — sao lại **thua** Gemma-3-12B "
        "trên *giống người* (Pearson r với mean crowdsource)?",
        "",
        "Không phải vì model “kém thông minh”. Trên mem_enc, **human-likeness** đo khả năng **bám thang Likert 1–7 "
        "của ~40 người/câu — khác benchmark coding/reasoning.",
        "",
        "Bốn cơ chế có số trong repo:",
        "",
        "1. **Calibration / bias:** Model cho cảnh “tự nhiên hơn” người (bias dương lớn) → Pearson/MAE xấu dù “hiểu” câu.",
        "2. **Slope thấp:** Model ít **theo biến thiên** điểm người (câu dễ vs khó) — chỉ bám vùng mean.",
        "3. **Lỗi theo condition:** Thua rõ ở `global` / `plural` / `name` (Mục 2) — không đều trên 50 câu.",
        "4. **r vs MAE:** Gemma-3 có r tốt nhưng MAE cao → bám **thứ hạng** câu khá ổn, nhưng **lệch tuyệt đối** từng điểm.",
        "",
        "*Giả thuyết phụ (không chứng minh từ data này):* model huấn luyện cho coding/agent có thể mất calibration "
        "“everyday plausibility” so với era chat-rating (GPT-4 paper — xem Mục 6).",
        "",
    ]


def build_discussion_summary_lines() -> List[str]:
    """Tổng hợp ngắn từ thảo luận — thuật ngữ + ý chính Mục 5."""
    return [
        "### Tổng hợp",
        "",
        "**Mục 5 giải thích gì?** Trên mem_enc, model **to / frontier / mới** không chắc **giống người chấm** "
        "(~40 người/câu, thang 1–7) hơn model **nhỏ / cũ hơn** (Gemma-3-12B). Metric chính: **Pearson r** — "
        "model có **bám thứ tự** câu dễ ↔ khó như crowdsource không. **Không** kết luận model thua vì “kém thông minh”.",
        "",
        "**Chuẩn so sánh — crowdsource:** trung bình điểm ~40 người chấm/câu (`human_mean`). "
        "Model “giống người” khi điểm model **gần** và **cùng chiều cao–thấp** với chuẩn đó.",
        "",
        "**Thuật ngữ (trong report):**",
        "",
        "| Thuật ngữ | Số trong data | Ý nghĩa dễ hiểu |",
        "|---|---|---|",
        "| **Bơm điểm** | `bias = model − human` **dương** | Model **hay cho cao hơn** mức người (vd. người ≈ 3.5, model ≈ 5) |",
        "| **+0.59** (Gemma-4) | bias trung bình 50 câu | Cao hơn người **~0.6 điểm** trên thang 1–7 — **bơm mạnh** |",
        "| **+0.19** (Gemma-3) | cùng công thức | Vẫn hơi bơm, nhưng **ít hơn** Gemma-4/GLM (~+0.57–0.59) |",
        "| **Độ dốc (slope)** | hồi quy model ~ human | Người tăng 1 điểm → model tăng bao nhiêu; **≈1** = bám tốt; **≈0.5** = **phản ứng yếu**, hay dồn ~5–6 |",
        "| **Biên độ cao–thấp** | spread điểm 1–7 | Người chênh câu dễ vs khó nhiều; model **biên hẹp** = không tách rõ câu lạ vs câu ổn |",
        "",
        "**“Thằng nào cũng bơm à?”** — **Hầu hết có**, nhưng **mức khác nhau**: GPT-4 paper **+0.06** (gần như không); "
        "Kimi **+0.13**; Gemma-3 / DeepSeek ORIG **~+0.19**; luna **+0.31**; Gemma-4 / GLM ORIG **~+0.57–0.59**. "
        "Ngoại lệ: GLM **T** bias **−0.70** (hay cho **thấp hơn** người). "
        "Thua/thắng không phải “có bơm hay không” mà **bơm bao nhiêu** + **độ dốc** + **lỗi ở câu khó**.",
        "",
        "**Vì sao model mới / lớn thua Gemma-3?** (có số)",
        "",
        "1. **Bơm mạnh hơn** — Gemma-4, GLM ~+0.6 vs Gemma-3 ~+0.2.",
        "2. **Độ dốc thấp** — DeepSeek / Gemma-4 ~0.47–0.49: người chấm thấp/cao chênh nhiều, model vẫn dồn quanh 5–6.",
        "3. **Sập ở câu khó** — `global`, `plural` (Gemma-4 `global` r ≈ 0 / âm).",
        "4. **Thắng sai chỗ metric** — một số model MAE tốt hơn Gemma-3 nhưng **thứ tự câu** sai → r thấp hơn.",
        "5. **Thinking chưa cứu hết** — DeepSeek T vẫn dưới Gemma-3 ORIG; Gemma-4 T mới sát baseline.",
        "",
        "**Gemma-3 / GPT-4 paper bám người hơn — biết gì từ số?**",
        "",
        "- **GPT-4 (paper)** r ≈ **0.75**, bias **+0.06** — **ít bơm nhất**, bám crowdsource tốt (xem Mục 6).",
        "- **Gemma-3** r ≈ **0.64**, bias **+0.19**, độ dốc **~1.14** — cũng bơm nhẹ nhưng **co giãn theo người** tốt hơn Gemma-4.",
        "- **Gemma-4** r ≈ **0.49**, bias **~+0.59**, độ dốc **~0.49** — bơm mạnh + phẳng → thua dù **lớn hơn**.",
        "",
        "*Giả thuyết (chưa chứng minh từ mem_enc n=50):* model era “chấm điểm / hội thoại” (GPT-4 paper) "
        "hoặc tune ít lệch mức (Gemma-3) **calibrate** tốt hơn model tối ưu coding/agent — **không** suy ra mixture huấn luyện cụ thể.",
        "",
    ]


def main() -> None:
    out_dir = ROOT / "results" / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    runs = load_runs(ROOT, min_n=50, exclude_smoke=True)
    baseline_run = find_run(runs, BASELINE_MODEL, BASELINE_MODE)
    if not baseline_run:
        raise SystemExit(f"Baseline run not found: {BASELINE_MODEL} / {BASELINE_MODE}")

    paradox_rows = paradox_vs_baseline(
        runs, BASELINE_MODEL, BASELINE_MODE, modes=("ORIG", "T")
    )
    write_csv(out_dir / "M5_paradox_table.csv", paradox_rows)

    cal_rows: List[Dict[str, Any]] = []
    for mid, mode in CALIBRATION_MODELS:
        r = find_run(runs, mid, mode)
        if not r:
            continue
        cal = calibration_stats(r["rows"])
        cal_rows.append(
            {
                "model_id": r["model_id"],
                "mode": r["mode"],
                "pearson_r": r.get("pearson_r"),
                "mae": r.get("mae"),
                "bias_model_minus_human": cal.get("bias_model_minus_human"),
                "slope": cal.get("slope"),
            }
        )
    write_csv(out_dir / "M5_calibration.csv", cal_rows)

    cond_delta_rows: List[Dict[str, Any]] = []
    for mid, mode in FOCUS_PAIRS:
        r = find_run(runs, mid, mode)
        if r:
            cond_delta_rows.extend(condition_delta_vs_baseline(r, baseline_run))
    write_csv(out_dir / "M5_condition_delta.csv", cond_delta_rows)

    case_rows: List[Dict[str, Any]] = []
    for mid, mode in CASE_CHALLENGERS:
        challenger = find_run(runs, mid, mode)
        if challenger:
            case_rows.extend(
                head_to_head_cases(challenger, baseline_run, k=5, min_advantage=0.5)
            )
    case_rows.sort(key=lambda x: -x["err_advantage_baseline"])
    write_csv(out_dir / "M5_head_to_head_cases.csv", case_rows)

    think_rows = thinking_deltas(runs)
    write_csv(out_dir / "M5_thinking_delta.csv", think_rows)

    chart = "M5_calibration_bias_slope.png"
    plot_calibration_bias_slope(cal_rows, out_dir / chart)

    base_row = next(
        (r for r in paradox_rows if r["model_id"] == BASELINE_MODEL and r["mode"] == BASELINE_MODE),
        None,
    )
    base_r = base_row["pearson_r"] if base_row else baseline_run.get("pearson_r")
    base_mae = base_row["mae"] if base_row else baseline_run.get("mae")

    losers_orig = [
        r for r in paradox_rows
        if r["mode"] == "ORIG" and r["model_id"] != BASELINE_MODEL and not r["beats_baseline"]
    ]
    winners_orig = [
        r for r in paradox_rows
        if r["mode"] == "ORIG" and r["model_id"] != BASELINE_MODEL and r["beats_baseline"]
    ]

    summary_payload = {
        "baseline": {"model_id": BASELINE_MODEL, "mode": BASELINE_MODE, "pearson_r": base_r, "mae": base_mae},
        "losers_orig": losers_orig,
        "winners_orig": winners_orig,
        "top_cases": case_rows[:3],
        "thinking_deltas": think_rows,
    }
    write_json(out_dir / "M5_summary.json", summary_payload)

    # --- report ---
    lines: List[str] = [
        "**Câu hỏi slide:** Kimi-K3, GLM-5.2, DeepSeek-v4-flash… là frontier / rất lớn — "
        "sao có cái **thua hoặc không hơn** Gemma-3-12B trên giống người?",
        "",
        f"**Baseline:** `{BASELINE_MODEL}` / `{BASELINE_MODE}` — r≈**{_fmt(base_r)}**, MAE≈**{_fmt(base_mae)}**.",
        "",
        "### Bảng nghịch lý (vs Gemma-3-12B ORIG)",
        "",
        "| Model | MODE | r | Δr | MAE | bias | slope | vs baseline |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]

    highlight_ids = {mid for mid, _ in FOCUS_PAIRS} | {"gpt-5.6-luna"}
    for r in paradox_rows:
        if r["mode"] != "ORIG" and r["model_id"] not in {
            "deepseek/deepseek-v4-flash",
            "google/gemma-4-31b-it",
        }:
            continue
        if r["model_id"] == BASELINE_MODEL:
            continue
        if r["model_id"] not in highlight_ids and r["mode"] != "T":
            continue
        tag = "✓ hơn" if r["beats_baseline"] else "✗ thua"
        if r["model_id"] in highlight_ids or r["mode"] == "T":
            lines.append(
                f"| `{_short(r['model_id'])}` | `{r['mode']}` | {_fmt(r['pearson_r'])} | "
                f"{_fmt(r['delta_r'], 4)} | {_fmt(r['mae'])} | {_fmt(r['bias_model_minus_human'])} | "
                f"{_fmt(r['slope'])} | {tag} |"
            )

    lines += [
        "",
        "**Neo số (ORIG):**",
        "",
    ]
    for mid, mode in FOCUS_PAIRS:
        row = next((r for r in paradox_rows if r["model_id"] == mid and r["mode"] == mode), None)
        if row:
            lines.append(
                f"- `{_short(mid)}`: r={_fmt(row['pearson_r'])} (Δr={_fmt(row['delta_r'], 4)}), "
                f"bias={_fmt(row['bias_model_minus_human'])}, slope={_fmt(row['slope'])}"
            )
    luna = next((r for r in paradox_rows if r["model_id"] == "gpt-5.6-luna" and r["mode"] == "ORIG"), None)
    if luna:
        lines.append(
            f"- `luna` (mốc tốt hơn): r={_fmt(luna['pearson_r'])} (Δr={_fmt(luna['delta_r'], 4)})"
        )

    lines.append("")
    lines += build_plain_explanation_lines()

    lines += [
        "### Calibration — frontier có “bơm” điểm cao hơn người?",
        "",
        "| Model | MODE | r | bias (model−human) | slope |",
        "|---|---|---:|---:|---:|",
    ]
    for r in cal_rows:
        lines.append(
            f"| `{_short(r['model_id'])}` | `{r['mode']}` | {_fmt(r['pearson_r'])} | "
            f"{_fmt(r['bias_model_minus_human'])} | {_fmt(r['slope'])} |"
        )

    lines += [
        "",
        f"![Calibration bias/slope]({chart})",
        "",
        "**Nhận định:**",
        "",
        "- **Gemma-4 / GLM** bias ≈ **+0.57–0.59** — **bơm điểm** (cho cao hơn người ~0.6 điểm, hệ thống).",
        "- **DeepSeek** bias gần Gemma-3 (~+0.19) nhưng **độ dốc ≈ 0.47** — ít bám biên độ cao–thấp của người.",
        "- **Gemma-3** slope ≈ **1.14** — bám xu hướng human mean tốt hơn dù MAE cao.",
        "- **Kimi** bias thấp (+0.13) + slope 0.82 → hơn Gemma-3 về r; vẫn dưới luna.",
        "",
        "### Breakdown theo condition (Δr vs Gemma-3 ORIG)",
        "",
        "Condition — xem [Mục 2](report.md#mục-2--human-likeness-theo-điều-kiện-câu-object-np).",
        "",
    ]

    for mid, mode in ("deepseek/deepseek-v4-flash", "ORIG"), ("google/gemma-4-31b-it", "ORIG"):
        subset = [r for r in cond_delta_rows if r["model_id"] == mid and r["mode"] == mode]
        if not subset:
            continue
        lines.append(f"**`{_short(mid)}` / `{mode}`:**")
        lines.append("")
        lines.append("| condition | r (model) | r (Gemma-3) | Δr | MAE Δ |")
        lines.append("|---|---:|---:|---:|---:|")
        for row in subset:
            gloss = COND_GLOSS.get(row["condition"], "")
            lines.append(
                f"| `{row['condition']}` ({gloss}) | {_fmt(row['pearson_r'])} | "
                f"{_fmt(row['baseline_pearson_r'])} | {_fmt(row['delta_r'], 4)} | "
                f"{_fmt(row['delta_mae'])} |"
            )
        lines.append("")

    glm_global = next(
        (
            r for r in cond_delta_rows
            if r["model_id"] == "z-ai/glm-5.2" and r["condition"] == "global"
        ),
        None,
    )
    kimi_global = next(
        (
            r for r in cond_delta_rows
            if r["model_id"] == "moonshotai/kimi-k3" and r["condition"] == "global"
        ),
        None,
    )
    glm_plural = next(
        (
            r for r in cond_delta_rows
            if r["model_id"] == "z-ai/glm-5.2" and r["condition"] == "plural"
        ),
        None,
    )
    kimi_name = next(
        (
            r for r in cond_delta_rows
            if r["model_id"] == "moonshotai/kimi-k3" and r["condition"] == "name"
        ),
        None,
    )
    if glm_global or kimi_global or glm_plural or kimi_name:
        lines.append("**GLM / Kimi — điểm yếu thêm:**")
        if glm_plural:
            lines.append(
                f"- GLM `plural`: r={_fmt(glm_plural['pearson_r'])} (Δr={_fmt(glm_plural['delta_r'], 4)})"
            )
        if kimi_global:
            lines.append(
                f"- Kimi `global`: r={_fmt(kimi_global['pearson_r'])} (Δr={_fmt(kimi_global['delta_r'], 4)})"
            )
        if kimi_name:
            lines.append(
                f"- Kimi `name`: r={_fmt(kimi_name['pearson_r'])} (Δr={_fmt(kimi_name['delta_r'], 4)})"
            )
        lines.append("")

    lines += [
        "### Case studies — frontier lệch, Gemma-3 gần human",
        "",
    ]
    for i, case in enumerate(case_rows[:3], 1):
        lines.append(
            f"**Case {i} — `{case['sample_id']}`** (`{case['condition']}`): "
            f"*“{case['sentence']}”*"
        )
        lines.append(
            f"- Human mean ≈ **{_fmt(case['human_mean'], 2)}**"
        )
        lines.append(
            f"- `{_short(case['challenger_model'])}`: **{_fmt(case['challenger_mean'], 2)}** "
            f"(|err|≈{_fmt(case['challenger_abs_err'], 2)})"
        )
        lines.append(
            f"- `gemma-3-12b-it`: **{_fmt(case['baseline_mean'], 2)}** "
            f"(|err|≈{_fmt(case['baseline_abs_err'], 2)}; advantage Δ|err|≈{_fmt(case['err_advantage_baseline'], 2)})"
        )
        lines.append("")

    lines += [
        "### Thinking có cứu không? (`T − ORIG`)",
        "",
        "| Model | r ORIG | r T | Δr | ΔMAE |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in think_rows:
        lines.append(
            f"| `{_short(row['model_id'])}` | {_fmt(row['orig_pearson_r'])} | "
            f"{_fmt(row['t_pearson_r'])} | {_fmt(row['delta_r'], 4)} | {_fmt(row['delta_mae'])} |"
        )

    ds_t = next((r for r in paradox_rows if r["model_id"] == "deepseek/deepseek-v4-flash" and r["mode"] == "T"), None)
    g4_t = next((r for r in paradox_rows if r["model_id"] == "google/gemma-4-31b-it" and r["mode"] == "T"), None)
    lines += [
        "",
        "**Kết luận Thinking:**",
        "",
    ]
    if ds_t:
        lines.append(
            f"- DeepSeek T: r={_fmt(ds_t['pearson_r'])} — cải thiện {ds_t['delta_r']:+.4f} so ORIG "
            f"nhưng **vẫn dưới** Gemma-3 ORIG ({_fmt(base_r)})."
        )
    if g4_t:
        lines.append(
            f"- Gemma-4 T: r={_fmt(g4_t['pearson_r'])} — vượt Gemma-3 ORIG nhưng chỉ sau reasoning; "
            f"ORIG vẫn thua rõ (Δr={_fmt(next((x['delta_r'] for x in paradox_rows if x['model_id']=='google/gemma-4-31b-it' and x['mode']=='ORIG'), None), 4)})."
        )
    lines.append(
        "- Thinking **không đảm bảo** human-likeness; cải thiện không đồng đều giữa model."
    )
    lines.append("")

    lines += build_discussion_summary_lines()

    lines += [
        "### 3 bullet slide (vì sao — gắn số)",
        "",
        "1. **Bơm điểm + calibration:** Gemma-4/GLM bias **+0.57–0.59**; DeepSeek độ dốc **~0.47** → không bám biên độ người.",
        "2. **Condition:** Gemma-4 thua mạnh ở `global` (r≈−0.04 vs Gemma-3); Kimi yếu `global`/`name` dù tổng thể hơn Gemma-3.",
        "3. **Metric nuance:** Gemma-3 thắng **Pearson** (rank) nhưng MAE **~1.19** — frontier thua vì lệch calibration, không vì “kém hiểu tiếng Anh”.",
        "",
        "### Câu kết luận slide",
        "",
        "> Trên mem_enc, quy mô/frontier không đảm bảo likeness: DeepSeek/Gemma-4 thua Gemma-3-12B chủ yếu vì "
        "**bias cao / slope thấp / lỗi tập trung ở condition khó** (`global`, `plural`), không vì “kém thông minh hơn”. "
        "Thinking cải thiện một phần (DeepSeek T +0.046 r) nhưng chưa vượt baseline nhỏ. "
        "*Giả thuyết phụ:* SOTA coding/reasoning ≠ giống crowdsource Likert 1–7.",
        "",
        "### Artifact",
        "",
        f"- `{chart}`",
        "- `M5_paradox_table.csv`",
        "- `M5_calibration.csv`",
        "- `M5_condition_delta.csv`",
        "- `M5_head_to_head_cases.csv`",
        "- `M5_thinking_delta.csv`",
        "- `M5_summary.json`",
        "",
    ]

    upsert_report_section(
        out_dir / "report.md",
        "Mục 5 — Ai tốt / ai tệ + nghịch lý frontier vs Gemma-3-12B",
        "\n".join(lines),
    )
    print(f"Baseline Gemma-3 r={base_r:.4f}; losers ORIG={len(losers_orig)}")
    print(f"Wrote → {out_dir / 'report.md'}")


if __name__ == "__main__":
    main()
