#!/usr/bin/env python3
"""Mục 3 — human disagreement vs LLM score dispersion."""

from __future__ import annotations

import sys
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from plausibility_eval.analysis import (  # noqa: E402
    _std,
    disagreement_table,
    dispersion_stats_for_run,
    dispersion_summary_rows,
    load_human_raw,
    load_runs,
    plot_disagreement_histograms,
    upsert_report_section,
    write_csv,
)
from plausibility_eval.io_utils import write_json  # noqa: E402

CASE_MODELS = (
    ("gpt-5.6-luna", "ORIG"),
    ("google/gemma-3-12b-it", "ORIG"),
)
TOP_K = 15
REPORT_TOP = 10
CASE_DETAIL = 2


def build_header_glossary_lines() -> List[str]:
    return [
        "### Chú giải header bảng",
        "",
        "**Bảng *Top câu disagreement* — chỉ điểm người** (tìm câu crowdsource bất đồng nhất):",
        "",
        "| Header | Nghĩa |",
        "|---|---|",
        "| `Rank` | Thứ hạng disagreement: sort `human_std` ↓, hòa thì `human_range` ↓ |",
        "| `sample_id` | ID câu (vd. `s4_all` = khung `s4`, condition `all`) |",
        "| `cond` | Condition object-NP — xem Mục 2 |",
        "| `human mean` | Trung bình điểm người (thang 1–7, ~40 annotator/câu) |",
        "| `human std` | Độ lệch chuẩn điểm người — **cao = người càng không đồng ý** |",
        "| `range` | max − min điểm người (vd. 6 = có người cho 1 và người cho 7) |",
        "| `% cực (1/7)` | Tỷ lệ annotator cho điểm **1 hoặc 7** |",
        "",
        "Dòng *So nhanh… model_std* (dưới bảng): trung bình phân tán LLM trên cùng tập câu — so với `human std` ~2.0.",
        "",
        "**Bảng *Collapse* — so phân tán LLM vs người trên top-15 disagreement** (mỗi dòng = model × MODE):",
        "",
        "| Header | Nghĩa |",
        "|---|---|",
        "| `Model` / `MODE` | Model và cách prompt (`ORIG` / `T`) |",
        "| `collapse rate` | Tỷ lệ câu mà `model_std < 0.5 × human_std` — model “co” phân tán. 1.00 = collapse trên cả 15 câu |",
        "| `mean model_std (top-15)` | Trung bình độ lệch chuẩn **20 lần resample** LLM trên 15 câu đó |",
        "| `mean ratio (top-15)` | Trung bình `model_std / human_std` — ~0.2 nghĩa là model chỉ ~20% độ spread của người |",
        "| `r(std_h, std_m)` | Pearson: câu người càng tranh cãi (`human_std` cao) thì model có phân tán theo không? Gần 0/âm → không |",
        "",
        "**Case chi tiết:** `n` = số điểm; `mean` / `std` / `range` (chỉ human) như trên; danh sách số = raw scores để thấy người trải 1–7 còn model dồn quanh 5–6.",
        "",
    ]


def build_paper_alignment_lines() -> List[str]:
    return [
        "### Paper nói gì / nhóm bổ sung gì",
        "",
        "**Paper có nghiên cứu & giải thích (Amouyal et al., EACL 2024):**",
        "",
        "- **Abstract / §1:** LLM ổn cho pretest **coarse-grained**; **kém fine-grained** (vd. hai câu cùng mức plausibility).",
        "- **§4.4:** pretest cặp câu bằng **t-test** trên điểm người; với LM khó vì *(trích §5)* **variance LM thấp hơn người rất nhiều** → thay bằng ngưỡng chênh mean, vẫn kém (Figure 6–7).",
        "- **§5 — *Variance of Humans vs. LMs*:** human variance **≫** LM dù sampling temp=1.5; resample LM cho điểm **gần giống nhau** (**Figure 8**: std trung bình GPT-4/GPT-3.5 vs người, 4 dataset).",
        "- **Giải thích §5:** output LM như trung bình của *N* lượt người → var_LM ≈ σ²/*N*; ước *N* bằng ratio `var_human / var_LM` **trên từng câu**.",
        "",
        "**Paper không làm (phần dưới là mở rộng của nhóm trên mem_enc):**",
        "",
        "| Phân tích nhóm (Mục 3) | Trong paper? |",
        "|---|---|",
        "| Top 10–15 câu **disagreement cao** (`human_std`, range) | Không — paper báo **std trung bình** theo dataset |",
        "| Metric **`collapse rate`** (model_std < 0.5 × human_std) | Không — thuật ngữ & ngưỡng của nhóm |",
        "| Zoo model (luna, gemma, …) | Chủ yếu GPT-4 / GPT-3.5 |",
        "| Histogram **từng câu** + raw scores | Figure 8 = bar std **trung bình** |",
        "| `r(std_h, std_m)` trên top-15 | Không |",
        "",
        "**Đọc Mục 3:** cùng câu hỏi với paper §5 (LM ít phân tán); nhóm **drill-down** trên câu người bất đồng nhất + nhiều model. "
        "Kết quả collapse ~0.91 **khớp hướng paper**, không phải metric paper định nghĩa sẵn.",
        "",
    ]


def build_paper_plain_lines() -> List[str]:
    return [
        "#### Giải thích dễ hiểu",
        "",
        "Hai lớp câu hỏi khác nhau:",
        "",
        "1. **Trung bình có khớp không?** (Mục 1 — Pearson r, MAE) — LLM cho *điểm trung bình* gần người không?",
        "2. **Phân tán có khớp không?** (Mục 3) — Gọi LLM nhiều lần trên **cùng một câu**, điểm có **lan** như nhiều người chấm không?",
        "",
        "**Paper trả lời lớp 2 — có, và khá đầy đủ:**",
        "",
        "- Người chấm **không đồng ý nhau** (variance cao). GPT resample **gần như cho cùng một số** (variance thấp) — dù bật temperature cao (§5).",
        "- Hệ quả thực tế: LLM **lọc câu quá dở / quá ổn** (coarse) thì được; nhưng **so hai câu xem plausibility có ngang nhau không** (fine-grained, t-test §4.4) thì **không tin được** — vì LM “phẳng” quá, chênh mean nhỏ khó phản ánh sự bất đồng của người.",
        "",
        "##### Giải thích thuật ngữ — plausibility, lọc câu, coarse vs fine-grained",
        "",
        "**Plausibility (mức hợp lý / tự nhiên):** Người (hoặc LLM) đọc một câu và cho điểm **1–7** — câu nghe *tự nhiên, hợp lý trong đời thực* đến mức nào. "
        "Không phải đúng/sai ngữ pháp: trong mem_enc **mọi câu đều đúng ngữ pháp**; điểm phản ánh “có believable không” (vd. *The nurse fetched the patient* cao, *The teacher scolded the shoe* thấp).",
        "",
        "**Pretest là gì?** Trước thí nghiệm chính (vd. đo thời gian đọc), tác giả **pretest** materials bằng plausibility judgments để **chọn hoặc loại câu** — tránh hiệu ứng xử lý bị lẫn vì câu quá vô lý hoặc hai câu so sánh không cùng “độ hợp lý”.",
        "",
        "**“Lọc câu” (coarse-grained) — lọc câu gì?** Paper §4.2–4.3, ba kiểu dùng plausibility; hai kiểu **lọc từng câu một** (coarse):",
        "",
        "| Kiểu lọc | Lọc câu nào? | Ví dụ |",
        "|---|---|---|",
        "| Lọc **implausible** (§4.2) | Bỏ câu **quá vô lý** (mean thấp, dưới ngưỡng) | Câu kiểu *The teacher scolded the shoe* — mean ≈ 1–2 |",
        "| Lọc **plausible** (§4.3) | Bỏ câu **quá hợp lý** khi thí nghiệm *cần* câu vô lý | Giữ lại câu implausible cho stimulus |",
        "",
        "Chỉ cần **một con số trung bình** / ngưỡng: “câu này quá dở hay quá ổn?” → LLM thường làm **tốt** (paper Figure 4–5).",
        "",
        "**“So hai câu ngang plausibility không?” (fine-grained) — là gì, tại sao cần?** Paper §4.4 — kiểu thứ ba:",
        "",
        "- So **cặp câu** (không phải từng câu lẻ): hai câu cùng khung, khác một thao tác (vd. *…the patient* vs *…the intern*).",
        "- **Mục tiêu:** mean plausibility **tương đương** — không để câu A “hợp lý hơn hẳn” câu B khi thí nghiệm chính chỉ muốn so hiệu ứng **ngôn ngữ** (vd. similarity-based interference ở Mục 2), không phải hiệu ứng “câu này dễ chấp nhận hơn”.",
        "- **mem_enc:** 40 cặp; field `need_ttest` (vd. `s1_all` so với `s1_global`, …) — **đúng use case fine-grained** này.",
        "- **Cách làm với người:** thu điểm cả hai câu → **t-test** — H₀: hai câu cùng phân phối plausibility. Nếu **reject** → người thấy hai câu **khác mức** → **loại cặp** khỏi materials.",
        "",
        "**t-test (§4.4) — một câu:** Kiểm định “hai câu có cùng ‘độ hợp lý’ theo người không?”. Khác với lọc coarse (một ngưỡng trên **một** câu), fine-grained hỏi **quan hệ giữa hai câu** — tinh hơn, khó hơn.",
        "",
        "**LM “phẳng” (variance thấp) — vì sao fine-grained hỏng?**",
        "",
        "- Gọi LLM 20 lần trên **cùng câu** → điểm **dồn quanh mean** (Mục 3: collapse).",
        "- Gọi trên **hai câu** → hai mean cũng **ổn định, chênh ít** → LLM hay kết luận “ngang nhau” dù **người** t-test **reject** (paper Figure 7: chênh mean là feature tốt với người, kém với LM).",
        "- Tức Pearson mean (Mục 1) có thể cao, nhưng LM **không bắt được** “cặp này phải loại vì plausibility lệch” — cần người hoặc metric khác.",
        "",
        "- Paper minh họa bằng **std trung bình** trên cả dataset (Figure 8) và lý do: LM như đã **lấy trung bình sẵn** của rất nhiều “ý kiến ảo” → mỗi lần gọi chỉ dao động nhẹ quanh mean.",
        "",
        "**Nhóm bổ sung thêm — paper không làm chi tiết này:**",
        "",
        "- Không dừng ở std trung bình: tìm **câu người tranh cãi nhất** (std ≈ 2, có người 1 có người 7) rồi hỏi: *trên đúng những câu đó*, LLM có “feel” tranh cãi không?",
        "- Thử **nhiều model** (luna, gemma, …), không chỉ GPT-4/3.5.",
        "- Đặt tên **`collapse`**: model_std quá nhỏ so với human_std → resample **không mô phỏng** crowd disagreement.",
        "",
        "**Một câu tóm:** Paper chứng minh LM **ít phân tán** (§5); Mục 3 **chỉ ra chỗ đau** — trên câu người bất đồng nhất, hầu hết model vẫn **dồn điểm** (collapse ~0.91) → giải thích vì sao Mục 1 có thể đẹp (mean khớp) mà pretest fine-grained vẫn cần người.",
        "",
    ]


def _fmt(x: float | None, nd: int = 3) -> str:
    if x is None:
        return "—"
    return f"{x:.{nd}f}"


def _short(model_id: str) -> str:
    return model_id.split("/")[-1]


def _fmt_scores(scores: Sequence[float]) -> str:
    if not scores:
        return "—"
    return ", ".join(str(int(x) if float(x).is_integer() else x) for x in scores)


def find_run(runs: Sequence[Dict[str, Any]], model_id: str, mode: str) -> Optional[Dict[str, Any]]:
    for r in runs:
        if r["model_id"] == model_id and r["mode"] == mode:
            return r
    return None


def enrich_summary_rows(
    summaries: Sequence[Dict[str, Any]],
    runs: Sequence[Dict[str, Any]],
    human_raw: Dict[str, Dict[str, Any]],
    sent_rows: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    high_ids = [s["sample_id"] for s in sent_rows]
    by_mm = {(r["model_id"], r["mode"]): r for r in runs}
    out: List[Dict[str, Any]] = []
    for s in summaries:
        run = by_mm.get((s["model_id"], s["mode"]))
        if not run:
            continue
        all_stats = dispersion_stats_for_run(run, human_raw)
        model_stds_high: List[float] = []
        human_stds_high: List[float] = []
        ratios: List[float] = []
        by_sid = {str(x.get("sample_id")): x for x in run["rows"]}
        for sid in high_ids:
            h = human_raw.get(sid)
            row = by_sid.get(sid)
            if not h or not row:
                continue
            ms = [float(x) for x in (row.get("model_scores") or []) if x is not None]
            mstd = _std(ms)
            hstd = h.get("human_std")
            if mstd is not None:
                model_stds_high.append(float(mstd))
            if hstd is not None:
                human_stds_high.append(float(hstd))
            if hstd and mstd and float(hstd) > 0:
                ratios.append(float(mstd) / float(hstd))
        out.append(
            {
                **s,
                "mean_human_std_all50": all_stats["mean_human_std"],
                "mean_model_std_all50": all_stats["mean_model_std"],
                "mean_std_ratio_all50": all_stats["mean_std_ratio"],
                "mean_model_std_top15": mean(model_stds_high) if model_stds_high else None,
                "mean_std_ratio_top15": mean(ratios) if ratios else None,
            }
        )
    out.sort(key=lambda x: -(x.get("collapse_rate_on_high_disagreement") or -1))
    return out


def main() -> None:
    out_dir = ROOT / "results" / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    runs = load_runs(ROOT, min_n=50, exclude_smoke=True)
    human_raw = load_human_raw(ROOT)

    sent_rows, disp_rows = disagreement_table(
        runs, human_raw, top_k_human=TOP_K, modes=("ORIG", "T")
    )
    summaries = enrich_summary_rows(
        dispersion_summary_rows(disp_rows), runs, human_raw, sent_rows
    )

    write_csv(out_dir / "M3_high_disagreement_sentences.csv", sent_rows)
    write_csv(out_dir / "M3_dispersion.csv", disp_rows)
    write_csv(out_dir / "M3_dispersion_summary.csv", summaries)

    case_runs: List[Dict[str, Any]] = []
    for mid, mode in CASE_MODELS:
        r = find_run(runs, mid, mode)
        if r:
            case_runs.append(r)
    if not case_runs:
        case_runs = [r for r in runs if r["mode"] == "ORIG"][:2]

    chart = "M3_case_histograms.png"
    written = plot_disagreement_histograms(
        sent_rows,
        human_raw,
        case_runs,
        out_dir / chart,
        max_sentences=3,
        title=None,
        target_n=20,
        also_per_panel=True,
    )
    print(f"[M3] histograms: {len(written)} files → {out_dir / chart} + M3_histograms/")

    all_human_stds = [
        float(h["human_std"]) for h in human_raw.values() if h.get("human_std") is not None
    ]
    mean_human_std_50 = mean(all_human_stds) if all_human_stds else None

    luna_run = find_run(runs, "gpt-5.6-luna", "ORIG")
    gemma_run = find_run(runs, "google/gemma-3-12b-it", "ORIG")

    summary_payload = {
        "top_k_disagreement": TOP_K,
        "mean_human_std_all50": mean_human_std_50,
        "top_disagreement_sentences": sent_rows[:5],
        "dispersion_summaries": summaries,
        "case_models": [{"model_id": r["model_id"], "mode": r["mode"]} for r in case_runs],
    }
    write_json(out_dir / "M3_summary.json", summary_payload)

    # --- report ---
    collapse_rates = [
        float(s["collapse_rate_on_high_disagreement"])
        for s in summaries
        if s.get("collapse_rate_on_high_disagreement") is not None
    ]
    mean_collapse = mean(collapse_rates) if collapse_rates else None
    n_full_collapse = sum(1 for c in collapse_rates if c >= 0.99)

    lines: List[str] = [
        "**Câu hỏi:** Câu người chấm 1, người khác 7 — LLM resample có phân tán giống người hay luôn dồn quanh một điểm?",
        "",
        "**Caveat:** `human_std` = ~40 annotator/câu; `model_std` = 20 lần gọi API/câu — so **ý nghĩa phân tán**, không phải thí nghiệm đối chứng cùng *n*.",
        "",
        f"**Neo paper (§5, Figure 8):** variance điểm LM **thấp hơn người rất nhiều** dù resample nhiều lần; "
        "§4.4: điều này làm **t-test fine-grained** (so cặp câu cùng plausibility) kém với người.",
        "",
        f"Trên mem_enc: mean `human_std` (50 câu) ≈ **{_fmt(mean_human_std_50, 2)}**. "
        f"Top **{TOP_K}** câu disagreement cao nhất (sort `human_std`, rồi `human_range`).",
        "",
    ]
    lines += build_paper_alignment_lines()
    lines += build_paper_plain_lines()
    lines += build_header_glossary_lines()
    lines += [
        "### Top câu disagreement (người)",
        "",
        "| Rank | sample_id | cond | human mean | human std | range | % cực (1/7) |",
        "|---:|---|---|---:|---:|---:|---:|",
    ]
    for i, row in enumerate(sent_rows[:REPORT_TOP], start=1):
        lines.append(
            f"| {i} | `{row['sample_id']}` | `{row['condition']}` | {_fmt(row['human_mean'], 2)} | "
            f"{_fmt(row['human_std'], 2)} | {_fmt(row['human_range'], 0)} | "
            f"{_fmt((row['pct_extreme'] or 0) * 100, 0)}% |"
        )

    if luna_run and gemma_run:
        lines += [
            "",
            f"**So nhanh trên top-{REPORT_TOP}** — `model_std` trung bình:",
            f"- `{_short(luna_run['model_id'])}` ORIG: "
            f"{_fmt(next((s['mean_model_std_top15'] for s in summaries if s['model_id']==luna_run['model_id'] and s['mode']=='ORIG'), None), 2)}",
            f"- `{_short(gemma_run['model_id'])}` ORIG: "
            f"{_fmt(next((s['mean_model_std_top15'] for s in summaries if s['model_id']==gemma_run['model_id'] and s['mode']=='ORIG'), None), 2)}",
        ]

    lines += [
        "",
        "### Collapse trên top disagreement (model_std < 0.5 × human_std)",
        "",
        "| Model | MODE | collapse rate | mean model_std (top-15) | mean ratio (top-15) | r(std_h, std_m) |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for s in sorted(summaries, key=lambda x: (-(x.get("collapse_rate_on_high_disagreement") or -1), x["model_id"])):
        lines.append(
            f"| `{_short(s['model_id'])}` | `{s['mode']}` | "
            f"{_fmt(s.get('collapse_rate_on_high_disagreement'), 2)} | "
            f"{_fmt(s.get('mean_model_std_top15'), 2)} | "
            f"{_fmt(s.get('mean_std_ratio_top15'), 2)} | "
            f"{_fmt(s.get('corr_human_model_std'), 2)} |"
        )

    lines += [
        "",
        f"![Human vs model dispersion]({chart})",
        "",
        f"*Hàng:* top-3 câu disagreement. *Cột:* "
        + ", ".join(f"`{_short(r['model_id'])}` {r['mode']}" for r in case_runs)
        + ". Xanh = người; cam = model.",
        "",
        "### Case chi tiết (top disagreement)",
        "",
    ]

    for hrow in sent_rows[:CASE_DETAIL]:
        sid = hrow["sample_id"]
        h = human_raw[sid]
        lines += [
            f"#### `{sid}` — *{hrow.get('sentence')}* (`{hrow['condition']}`)",
            "",
            f"**Human (n={h['human_n']}, mean={_fmt(h['human_mean'], 2)}, std={_fmt(h['human_std'], 2)}, "
            f"range={_fmt(h['human_range'], 0)}):** {_fmt_scores(h['human_results'])}",
            "",
        ]
        for run in case_runs:
            row = next((x for x in run["rows"] if str(x.get("sample_id")) == sid), None)
            if not row:
                continue
            ms = [float(x) for x in (row.get("model_scores") or []) if x is not None]
            mstd = _std(ms)
            lines.append(
                f"**`{_short(run['model_id'])}` / `{run['mode']}`** "
                f"(n={len(ms)}, mean={_fmt(row.get('model_mean'), 2)}, std={_fmt(mstd, 2)}): "
                f"{_fmt_scores(ms)}"
            )
            lines.append("")

    lines += [
        "### Nhận định",
        "",
    ]
    if mean_collapse is not None:
        lines.append(
            f"- Trên top-{TOP_K} disagreement: **collapse rate trung bình ≈ {_fmt(mean_collapse, 2)}** "
            f"({n_full_collapse}/{len(collapse_rates)} run ≥ 0.99) — LLM **ít phân tán hơn người** trên câu người bất đồng."
        )
    if summaries:
        worst = min(summaries, key=lambda x: x.get("mean_std_ratio_top15") or 9)
        best = max(summaries, key=lambda x: x.get("mean_std_ratio_top15") or -1)
        lines.append(
            f"- Ratio `model_std/human_std` trên top-{TOP_K}: thấp nhất "
            f"`{_short(worst['model_id'])}`/{worst['mode']} ≈ {_fmt(worst.get('mean_std_ratio_top15'), 2)}; "
            f"cao nhất `{_short(best['model_id'])}`/{best['mode']} ≈ {_fmt(best.get('mean_std_ratio_top15'), 2)} "
            f"(vẫn thường ≪ 1)."
        )
    lines.append(
        "- **Kết luận:** Hầu hết model **collapse** — resample ổn định quanh mean, không tái hiện disagreement người. "
        "Khớp paper §5; giải thích vì sao Pearson cao (Mục 1) vẫn **không đủ** cho pretest fine-grained (t-test cặp câu)."
    )

    lines += [
        "",
        "### Kết luận đối chiếu paper — vẫn đúng ở thời điểm hiện tại?",
        "",
        "**Có** — về **hướng và kết luận chính**, paper (Amouyal et al., EACL 2024) **vẫn đứng** trên zoo model hiện tại + mem_enc. "
        "Phân tích nhóm **ủng hộ** paper hơn là bác bỏ; **không** đưa ra kết luận trái paper, chỉ **reproduce + định lượng** (collapse, case cụ thể).",
        "",
        "| Kết luận paper | Trên data nhóm |",
        "|---|---|",
        "| LLM bám **mean** người khá tốt (GPT-4 mạnh) | **Đúng** — xem Mục 1 (vd. luna T r cao; gpt-4 paper vẫn baseline MAE/bias tốt) |",
        "| **Coarse** pretest (lọc câu quá dở/ổn) LLM làm được | Nhóm **không replicate** Figure 4–5; **không** có bằng chứng ngược |",
        "| **Fine-grained** (so cặp câu cùng plausibility) LLM **yếu** | **Đúng hướng** — collapse ~0.91 (Mục 3) → LM “phẳng”, khó thay t-test người |",
        "| Variance LM **≪** người khi resample (§5) | **Đúng** — `model_std` ~0.2–0.5 vs `human_std` ~2 trên top disagreement |",
        "",
        "**Tinh chỉnh (không phải bác paper):**",
        "",
        "- Model **mới** (luna, sol, …) có thể **hơn** gpt-4 paper về Pearson — paper không claim GPT-4 #1 mãi mãi; claim *mean OK, variance không* — **vẫn đúng**.",
        "- Model mới **không phá** quy luật variance: hầu hết vẫn collapse trên câu disagreement.",
        "- **Ngoại lệ:** `glm-5.2`/T (collapse ≈ 0) — không đảo kết luận chung; chưa chứng minh fine-grained ngang người.",
        "- **Phạm vi:** nhóm chỉ đủ trên **mem_enc** (50 câu), không replicate 4 dataset của paper.",
        "",
        "**Một câu slide:** *Paper EACL 2024 vẫn valid — mean correlate tốt, variance thấp, coarse được / fine-grained chưa; "
        "chúng em xác nhận trên model 2025–26, Mục 3 khớp §5 (collapse ~91%).*",
        "",
    ]

    lines += [
        "",
        "### Artifact",
        "",
        f"- `{chart}` (gộp) + `M3_histograms/*.png` (từng ô; model hist scale → n=20 nếu thiếu)",
        "- `M3_high_disagreement_sentences.csv`",
        "- `M3_dispersion.csv`, `M3_dispersion_summary.csv`",
        "- `M3_summary.json`",
        "",
    ]

    upsert_report_section(
        out_dir / "report.md",
        "Mục 3 — Disagreement người vs phân tán LLM",
        "\n".join(lines),
    )
    print(f"mean_collapse={mean_collapse:.3f}" if mean_collapse else "mean_collapse=—")
    print(f"Wrote → {out_dir / 'report.md'}")


if __name__ == "__main__":
    main()
