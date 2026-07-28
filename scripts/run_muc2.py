#!/usr/bin/env python3
"""Mục 2 — human-likeness by linguistic condition (object-NP)."""

from __future__ import annotations

import sys
from collections import defaultdict
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
    condition_table,
    load_human_raw,
    load_ready_gpt4,
    load_runs,
    metrics_by_condition,
    paper_gpt4_by_condition,
    top_residuals,
    upsert_report_section,
    write_csv,
)
from plausibility_eval.io_utils import write_json  # noqa: E402

COND_GLOSS = {
    "all": "object khớp kỳ vọng (baseline)",
    "global": "object liên quan nhưng kém khớp ngữ cảnh",
    "animate": "đổi animate/inanimate của object",
    "plural": "object số nhiều",
    "name": "object là tên riêng",
}


def build_condition_theory_lines() -> List[str]:
    """Author-sourced condition background (Amouyal et al., EACL 2024 Findings)."""
    return [
        "",
        "### Giải thích các condition — theo paper",
        "",
        "**Nguồn:** Amouyal, Meltzer-Asscher & Berant (EACL 2024 Findings; arXiv:2402.05455), "
        "dataset *Our data* / mem_enc trong §2.1, Table 1, §4.4.",
        "",
        "#### Tại sao có các biến thể câu?",
        "",
        "Paper mô tả bộ **50 câu plausible**, cấu trúc **đơn giản** (simple transitive trong Table 1), "
        "được tạo *“for a future experiment on **similarity-based interference**”* (§2.1). "
        "Cấu trúc: **40 cặp câu**, trong đó *“one sentence is shared among 4 pairs”* — tức **10 khung câu × 5 biến thể**; "
        "mỗi câu có **40** đánh giá plausibility từ người.",
        "",
        "**Động cơ kiểm soát plausibility (§1):** khi thí nghiệm thao tác biến ngôn ngữ (ví dụ độ tương đồng NP), "
        "cần đảm bảo các câu **cùng mức hợp lý** để chênh lệch xử lý không bị lẫn bởi plausibility. "
        "Paper minh họa bằng ví dụ *photographer / contract* và trích **Ness & Meltzer-Asscher (2019)**: "
        "hai NP đều animate (1a) vs một animate + một inanimate (1b) có thể gây **similarity-based interference** khi đọc.",
        "",
        "**Pretest fine-grained (§4.4):** một cách dùng plausibility là so **cặp câu** — "
        "chạy **t-test** xem hai câu có cùng phân phối điểm không; cặp bị reject thì loại khỏi materials. "
        "Trong data repo, field `need_ttest` trên các dòng `*_all` liệt kê 4 biến thể còn lại cùng khung "
        "(ví dụ `s1_all` so với `s1_global`, `s1_animate`, `s1_plural`, `s1_name`) — **khớp mục đích §4.4**, "
        "nhưng paper **không** đặt tên các hậu tố đó.",
        "",
        "Paper cảm ơn **Tal Ness** (Acknowledgments) — tác giả làm về similarity-based interference cùng Meltzer-Asscher; "
        "paper **không** mô tả chi tiết thiết kế từng manipulation trong mem_enc ngoài hai ví dụ Table 1.",
        "",
        "#### Tại sao **4** biến thể (không phải 5–6–7 hay 1–2–3)?",
        "",
        "**Phần paper *có* trả lời — về số lượng, không phải loại manipulation:**",
        "",
        "- §2.1: *“40 sentence pairs (one sentence is shared among 4 pairs)”*.",
        "- Suy ra từ cấu trúc data: **10 khung** (`s1`–`s10`) × **4 cặp so sánh** / khung = **40 cặp**; "
        "mỗi khung có **5 câu** (1 baseline + 4 biến thể) → **50 câu** tổng.",
        "- Table 1 (Ours): hai dòng *Simple | Plaus* với số item **10** và **40** — khớp **10 baseline + 40 biến thể**.",
        "- Field `need_ttest` trên `*_all`: baseline được so t-test với **đúng 4** biến thể còn lại — khớp thiết kế pretest fine-grained §4.4.",
        "",
        "Tức paper giải thích vì sao có **4 cặp** (và do đó **4** biến thể ngoài baseline), "
        "chứ **không** nói “có thể thêm biến thể thứ 5–6–7” hay “chỉ cần 2–3”. "
        "Số 4 là **hệ quả thiết kế thí nghiệm tương lai + pretest cặp**, không phải con số tùy ý trong repo.",
        "",
        "**Phần paper *không* trả lời — vì sao đúng 4 *loại* này (`global`, `animate`, `plural`, `name`):**",
        "",
        "- Paper **không** liệt kê lý do chọn bốn thao tác object-NP này thay vì thao tác khác "
        "(vd. đổi động từ, đổi subject, thêm modifier, câu dài hơn, v.v.).",
        "- Paper **không** giải thích vì sao không thêm biến thể thứ 5 (vd. chỉ đổi definiteness *a/the*) "
        "hoặc bớt còn 2–3 — ngoài việc cố định **4 cặp/khung** như trên.",
        "- §1 trích **animacy** (Ness 2019) như **ví dụ tổng quát** về similarity NP; "
        "paper **không** nói “biến thể `animate` trong mem_enc được chọn vì lý do X”.",
        "- Thiết kế chi tiết của thí nghiệm similarity-based interference **tương lai** "
        "(mà bộ câu này phục vụ) **không** được mô tả trong paper EACL 2024 — paper chỉ dùng bộ câu để **đánh giá LLM pretest**.",
        "",
        "**Kết luận thẳng:** biết **tại sao có 4** (cấu trúc 40 cặp / pretest t-test); "
        "**không biết từ paper** tại sao 4 loại manipulation lại là global/animate/plural/name — "
        "chỉ thấy pattern đó trong `sample_id` của data tác giả công bố.",
        "",
        "#### Paper có định nghĩa `all|global|animate|plural|name` không?",
        "",
        "**Không.** §2.1 và Table 1 chỉ đưa hai ví dụ từ cùng khung *The nurse fetched …*: "
        "*…the patient.* và *…the intern.* Paper **không** giải thích nhãn `all`, `global`, `animate`, `plural`, `name`; "
        "các nhãn này đến từ **quy ước `sample_id` trong data/repo** (hậu tố sau `s1`–`s10`).",
        "",
        "**Lưu ý:** *global prompt* trong paper (§2.3, Appendix) là loại **prompt LLM** (ví dụ chung cho mọi dataset), "
        "**không** liên quan condition `global` trên object-NP.",
        "",
        "#### Từng condition — paper nói gì / không nói gì",
        "",
        "| Condition | Paper (trích ý) | Trong paper? | Quan sát từ data (repo; **không** phải định nghĩa tác giả) |",
        "|---|---|---|---|",
        "| `all` | Table 1: *The nurse fetched the patient.* | Có ví dụ; **không** gọi là `all` | Hậu tố `all`; dòng `need_ttest` → vai trò **baseline** so cặp t-test |",
        "| `global` | Table 1: *The nurse fetched the intern.* | Có ví dụ; **không** gọi là `global`, **không** giải thích vì sao *intern* khác *patient* | Cùng khung, object animate khác (thường cùng “vai”/bối cảnh nghề nghiệp) |",
        "| `animate` | §1: động cơ **animacy** / similarity NP (Ness 2019) — ngữ cảnh tổng quát | **Không** gắn suffix `animate` với mem_enc | Object đổi sang NP **vô tri** (vd. *file*, *cake*, *portrait*) |",
        "| `plural` | — | **Không có** | Object **số nhiều** (vd. *interns*, *chefs*) |",
        "| `name` | — | **Không có** | Object là **tên riêng** (vd. *Matt*, *Louis*) |",
        "",
        "Bảng *Ý nghĩa ngắn* phía trên là **diễn giải phân tích** (gloss) để đọc heatmap — "
        "chỉ `patient`/`intern` có ví dụ trực tiếp trong paper; các dòng còn lại suy từ pattern câu trong `mem_enc_exp1.jsonl`.",
        "",
    ]


def build_condition_plain_lines() -> List[str]:
    """Plain-language summary below the paper-sourced section."""
    return [
        "### Giải thích dễ hiểu",
        "",
        "**Condition là gì?** Mỗi condition là một **cách đổi tân ngữ (object)** trên **cùng một khung câu**. "
        "Chủ ngữ và động từ giữ nguyên; chỉ phần sau động từ thay đổi. "
        "Ví dụ khung `s1`: *The nurse fetched …* — chỉ đổi *patient / intern / file / interns / Matt*.",
        "",
        "**Bộ câu được tổ chức thế nào?**",
        "",
        "- **10 khung** (`s1` … `s10`) — 10 tình huống nghề nghiệp khác nhau (y tá, bồi bàn, đại lý nghệ thuật, …).",
        "- Mỗi khung có **5 câu** = 1 baseline + 4 biến thể → **50 câu** tổng.",
        "- Hậu tố trong `sample_id` (`all`, `global`, `animate`, `plural`, `name`) cho biết **đang đổi object theo kiểu nào**.",
        "",
        "**Năm biến thể — đọc qua ví dụ `s1`:**",
        "",
        "| Condition | Câu | Ý chính (dễ nhớ) |",
        "|---|---|---|",
        "| `all` | *The nurse fetched the patient.* | **Baseline** — object “đúng kỳ vọng” nhất trong khung |",
        "| `global` | *The nurse fetched the intern.* | Vẫn người, vẫn hợp ngữ cảnh bệnh viện, nhưng **vai khác** (thực tập sinh, không phải bệnh nhân) |",
        "| `animate` | *The nurse fetched the file.* | Đổi sang **đồ vật** (vô tri) — câu vẫn đúng ngữ pháp |",
        "| `plural` | *The nurse fetched the interns.* | Cùng ý với *intern* nhưng **số nhiều** |",
        "| `name` | *The nurse fetched Matt.* | Gọi **tên riêng** thay vì cụm danh từ *the …* |",
        "",
        "**Thuật ngữ tiếng Việt — `plural` và `animate` (dễ nhầm):**",
        "",
        "- **`plural`** = **số nhiều** (object chuyển từ số ít sang số nhiều). "
        "Ví dụ: *the intern* (một thực tập sinh) → *the interns* (các thực tập sinh).",
        "- **`animate`** trong ngôn ngữ học = **hữu sinh** (người, động vật); đối lập **vô sinh** / **vô tri** (đồ vật). "
        "Nhãn condition `animate` = **biến thể thao tác theo chiều animacy (hữu sinh ↔ vô sinh)**, "
        "**không** có nghĩa “object trong câu là hữu sinh”.",
        "- Trong data, `animate` thường **đổi object sang vô sinh**: "
        "`all` *…the patient* (hữu sinh) → `animate` *…the file* (vô sinh). "
        "Tên nhãn trỏ vào **loại thao tác**, không mô tả trực tiếp object ở câu đó.",
        "",
        "**Tại sao cần nhiều biến thể?** Paper nói bộ câu này chuẩn bị cho thí nghiệm tương lai về "
        "*similarity-based interference* — khi hai cụm danh từ trong câu **giống nhau** (cùng animate, cùng số, …), "
        "người đọc có thể **nhầm lẫn** khi xử lý. Trước khi chạy thí nghiệm đó, tác giả cần pretest: "
        "các biến thể phải **cùng độ hợp lý** (plausibility), không để câu này “hợp lý hơn hẳn” câu kia chỉ vì đổi từ.",
        "",
        "**Tại sao đúng 4 biến thể (ngoài baseline)?** Đơn giản: thiết kế cố định **4 cặp so sánh / khung** "
        "(baseline so với từng biến thể) → 10 × 4 = **40 cặp** để chạy t-test plausibility (§4.4). "
        "Không phải chọn ngẫu nhiên “4 hay 7”.",
        "",
        "**Tại sao lại là 4 *loại* global / animate / plural / name?** "
        "Phần này **paper không giải thích** — chỉ thấy trong data. "
        "Khi phân tích Mục 2, ta coi đây là **4 kiểu thao tác object** đã có sẵn trong bộ materials, "
        "rồi hỏi: LLM bám điểm người tốt nhất ở kiểu nào, kém nhất ở kiểu nào?",
        "",
        "**Đọc kết quả Mục 2 nghĩa là gì?** Heatmap và bảng trung bình cho biết: "
        "với cùng metric human-likeness (Pearson r / MAE), model có **ổn định** qua mọi kiểu đổi object không, "
        "hay chỉ giỏi ở baseline (`all`) / đổi vô tri (`animate`) mà **yếu** khi object liên quan nhưng lệch vai (`global`) "
        "hoặc khi dùng tên riêng (`name`)? Đó là lý do ta tách theo condition — không phải vì “chủ đề tin tức”, "
        "mà vì **loại thao tác ngôn ngữ trên object**.",
        "",
    ]

S1_SENTENCE_VI = {
    "s1_all": "Y tá đã đón bệnh nhân.",
    "s1_global": "Y tá đã đón thực tập sinh.",
    "s1_animate": "Y tá đã lấy hồ sơ.",
    "s1_plural": "Y tá đã đón các thực tập sinh.",
    "s1_name": "Y tá đã đón Matt.",
}


def _fmt(x: float | None, nd: int = 3) -> str:
    if x is None:
        return "—"
    return f"{x:.{nd}f}"


def _short(model_id: str) -> str:
    return model_id.split("/")[-1]


def mean_by_condition(
    cond_rows: Sequence[Dict[str, Any]],
    *,
    modes: Sequence[str] = ("ORIG", "T"),
) -> List[Dict[str, Any]]:
    buckets: Dict[str, Dict[str, List[float]]] = {
        c: {"pearson_r": [], "mae": []} for c in CONDS
    }
    for r in cond_rows:
        if r["mode"] not in modes:
            continue
        c = r["condition"]
        if c not in buckets:
            continue
        if r.get("pearson_r") is not None:
            buckets[c]["pearson_r"].append(float(r["pearson_r"]))
        if r.get("mae") is not None:
            buckets[c]["mae"].append(float(r["mae"]))
    out = []
    for c in CONDS:
        rs = buckets[c]["pearson_r"]
        ms = buckets[c]["mae"]
        out.append(
            {
                "condition": c,
                "gloss": COND_GLOSS.get(c, ""),
                "n_runs": len(rs),
                "mean_pearson_r": sum(rs) / len(rs) if rs else None,
                "mean_mae": sum(ms) / len(ms) if ms else None,
            }
        )
    return out


def plot_condition_heatmap(
    runs: Sequence[Dict[str, Any]],
    paper_by_c: Dict[str, Dict[str, Any]],
    out_path: Path,
) -> List[str]:
    heat_runs = [r for r in runs if r["mode"] in ("ORIG", "T")]
    heat_runs = sorted(heat_runs, key=lambda r: (-(r["pearson_r"] or -1), r["model_id"], r["mode"]))
    labels = [f"{_short(r['model_id'])} | {r['mode']}" for r in heat_runs]
    labels.append("gpt-4 (paper) | ref")
    mat: List[List[float]] = []
    for r in heat_runs:
        by_c = metrics_by_condition(r["rows"])
        mat.append([by_c[c]["pearson_r"] if by_c[c]["pearson_r"] is not None else float("nan") for c in CONDS])
    mat.append(
        [
            paper_by_c[c]["pearson_r"] if paper_by_c.get(c, {}).get("pearson_r") is not None else float("nan")
            for c in CONDS
        ]
    )
    arr = np.array(mat, dtype=float)
    fig, ax = plt.subplots(figsize=(9, max(4.5, 0.38 * len(labels) + 1.2)))
    im = ax.imshow(arr, aspect="auto", vmin=0.0, vmax=1.0, cmap="viridis")
    ax.set_xticks(range(len(CONDS)))
    ax.set_xticklabels([f"{c}" for c in CONDS])
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_title("Pearson r by object-NP condition (ORIG / T + gpt-4 paper)")
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            v = arr[i, j]
            if np.isnan(v):
                continue
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7, color="white" if v < 0.55 else "black")
    fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02, label="Pearson r")
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
    return labels


def _fmt_scores(scores: Sequence[float]) -> str:
    if not scores:
        return "—"
    return ", ".join(str(int(x) if float(x).is_integer() else x) for x in scores)


def preferred_runs_one_per_model(runs: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
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


def model_votes_for_sentence(
    runs: Sequence[Dict[str, Any]],
    sample_id: str,
) -> List[Dict[str, Any]]:
    votes: List[Dict[str, Any]] = []
    for r in preferred_runs_one_per_model(runs):
        row = next((x for x in r["rows"] if str(x.get("sample_id")) == sample_id), None)
        if not row or row.get("model_mean") is None:
            continue
        votes.append(
            {
                "model_id": r["model_id"],
                "mode": r["mode"],
                "model_mean": float(row["model_mean"]),
            }
        )
    return votes


def pick_condition_illustrations(
    ready: Sequence[Dict[str, Any]],
    runs: Sequence[Dict[str, Any]],
    human_raw: Dict[str, Dict[str, Any]],
    *,
    family: str = "s1",
) -> List[Dict[str, Any]]:
    """One sentence per condition — full human scores + one AI vote per model."""
    ready_by_sid = {str(r["sample_id"]): r for r in ready}
    out: List[Dict[str, Any]] = []
    for cond in CONDS:
        sid = f"{family}_{cond}"
        rr = ready_by_sid.get(sid)
        if not rr:
            continue
        h = human_raw.get(sid) or {}
        human_scores = [float(x) for x in (h.get("human_results") or [])]
        ai_votes = model_votes_for_sentence(runs, sid)
        ai_means = [v["model_mean"] for v in ai_votes]
        out.append(
            {
                "condition": cond,
                "sample_id": sid,
                "sentence": rr.get("sentence"),
                "sentence_vi": S1_SENTENCE_VI.get(sid, ""),
                "human_scores": human_scores,
                "human_mean": float(rr["human_mean"]),
                "human_n": len(human_scores),
                "gpt4_paper_mean": float(rr["gpt4_mean"]) if rr.get("gpt4_mean") is not None else None,
                "ai_votes": ai_votes,
                "ai_means": ai_means,
                "llm_annotators_mean": sum(ai_means) / len(ai_means) if ai_means else None,
                "gloss": COND_GLOSS.get(cond, ""),
            }
        )
    return out


def flatten_ai_votes(illustrations: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for ex in illustrations:
        for v in ex.get("ai_votes") or []:
            rows.append(
                {
                    "condition": ex["condition"],
                    "sample_id": ex["sample_id"],
                    "sentence": ex.get("sentence"),
                    "model_id": v["model_id"],
                    "mode": v["mode"],
                    "model_mean": v["model_mean"],
                }
            )
    return rows


def pick_residual_cases(
    residuals: Sequence[Dict[str, Any]],
    *,
    k_sentences: int = 3,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Pick top recurring hard sentences + a few concrete model cases."""
    by_sid: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in residuals:
        by_sid[str(r["sample_id"])].append(r)
    # rank sentences by how often they appear in top residuals + mean abs_err
    scored = []
    for sid, items in by_sid.items():
        mean_err = sum(float(x["abs_err"]) for x in items) / len(items)
        scored.append(
            {
                "sample_id": sid,
                "sentence": items[0].get("sentence"),
                "condition": items[0].get("condition"),
                "human_mean": items[0].get("human_mean"),
                "n_in_top_residuals": len(items),
                "mean_abs_err": mean_err,
                "worst_case": max(items, key=lambda x: float(x["abs_err"])),
            }
        )
    scored.sort(key=lambda x: (-x["n_in_top_residuals"], -x["mean_abs_err"]))
    top_sents = scored[:k_sentences]
    example_rows = []
    for s in top_sents:
        w = s["worst_case"]
        example_rows.append(
            {
                "sample_id": s["sample_id"],
                "condition": s["condition"],
                "sentence": s["sentence"],
                "human_mean": s["human_mean"],
                "model_id": w["model_id"],
                "mode": w["mode"],
                "model_mean": w["model_mean"],
                "abs_err": w["abs_err"],
                "n_models_in_top": s["n_in_top_residuals"],
            }
        )
    return top_sents, example_rows


def main() -> None:
    out_dir = ROOT / "results" / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    runs = load_runs(ROOT, min_n=50, exclude_smoke=True)
    ready = load_ready_gpt4(ROOT)
    human_raw = load_human_raw(ROOT)
    paper_by_c = paper_gpt4_by_condition(ready)

    cond_tbl = condition_table(runs, modes=("ORIG", "T"))
    write_csv(out_dir / "M2_by_condition.csv", cond_tbl)

    mean_tbl = mean_by_condition(cond_tbl, modes=("ORIG", "T"))
    for row in mean_tbl:
        p = paper_by_c.get(row["condition"]) or {}
        row["paper_pearson_r"] = p.get("pearson_r")
        row["paper_mae"] = p.get("mae")
    # easiest = highest mean r; hardest = lowest mean r
    by_r = sorted(mean_tbl, key=lambda x: -(x["mean_pearson_r"] or -1))
    by_mae = sorted(mean_tbl, key=lambda x: x["mean_mae"] if x["mean_mae"] is not None else 9e9)
    for i, row in enumerate(by_r, start=1):
        row["rank_by_mean_r"] = i
    write_csv(out_dir / "M2_condition_mean.csv", mean_tbl)

    chart = "M2_condition_heatmap.png"
    plot_condition_heatmap(runs, paper_by_c, out_dir / chart)

    residuals = top_residuals(runs, k=40, modes=("ORIG", "T"))
    write_csv(out_dir / "M2_top_residuals.csv", residuals)
    top_sents, examples = pick_residual_cases(residuals, k_sentences=3)
    illustrations = pick_condition_illustrations(ready, runs, human_raw, family="s1")
    write_csv(out_dir / "M2_hard_sentences.csv", top_sents)
    write_csv(out_dir / "M2_residual_examples.csv", examples)
    write_csv(
        out_dir / "M2_condition_examples.csv",
        [
            {
                "condition": ex["condition"],
                "sample_id": ex["sample_id"],
                "sentence": ex["sentence"],
                "human_mean": ex["human_mean"],
                "human_n": ex["human_n"],
                "human_scores": _fmt_scores(ex["human_scores"]),
                "gpt4_paper_mean": ex["gpt4_paper_mean"],
                "llm_annotators_mean": ex["llm_annotators_mean"],
                "n_ai_annotators": len(ex["ai_votes"]),
            }
            for ex in illustrations
        ],
    )
    write_csv(out_dir / "M2_condition_ai_votes.csv", flatten_ai_votes(illustrations))
    write_json(out_dir / "M2_condition_examples_detail.json", illustrations)
    write_json(
        out_dir / "M2_summary.json",
        {
            "easiest_by_mean_r": by_r[0] if by_r else None,
            "hardest_by_mean_r": by_r[-1] if by_r else None,
            "easiest_by_mean_mae": by_mae[0] if by_mae else None,
            "hardest_by_mean_mae": by_mae[-1] if by_mae else None,
            "paper_by_condition": paper_by_c,
            "hard_sentences": top_sents,
            "condition_illustrations": illustrations,
        },
    )

    easiest, hardest = by_r[0], by_r[-1]
    easiest_mae, hardest_mae = by_mae[0], by_mae[-1]

    lines: List[str] = [
        "Điều kiện = manipulation **object-NP** trên cùng khung câu (hậu tố `sample_id`), "
        "**không** phải topic tin tức. Mỗi điều kiện ≈ 10 câu.",
        "",
        "| Condition | Ý nghĩa ngắn |",
        "|---|---|",
    ]
    for c in CONDS:
        lines.append(f"| `{c}` | {COND_GLOSS[c]} |")

    lines += build_condition_theory_lines()
    lines += build_condition_plain_lines()

    lines += [
        "### Heatmap Pearson r (ORIG / T + gpt-4 paper)",
        "",
        f"![Pearson r by condition]({chart})",
        "",
        "### Trung bình qua zoo ORIG+T (và so paper)",
        "",
        "| Rank (r) | Condition | mean r | mean MAE | paper r | paper MAE |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for row in by_r:
        lines.append(
            f"| {row['rank_by_mean_r']} | `{row['condition']}` | {_fmt(row['mean_pearson_r'])} | "
            f"{_fmt(row['mean_mae'])} | {_fmt(row['paper_pearson_r'])} | {_fmt(row['paper_mae'])} |"
        )

    lines += [
        "",
        "### Minh họa từng condition (cùng khung câu `s1`)",
        "",
        "Cùng khung *The nurse fetched …* — đổi object-NP theo condition. "
        "Dưới đây: **toàn bộ điểm người chấm** (raw crowdsource) và **mỗi LLM = 1 annotator** "
        "(`model_mean` trên câu đó; ưu tiên MODE ORIG, không có thì T; không gồm gpt-4 paper).",
        "",
        "| Condition | Câu | human mean | llm_annotators mean | gpt-4 paper |",
        "|---|---|---:|---:|---:|",
    ]
    for ex in illustrations:
        sent = (ex.get("sentence") or "").replace("|", "\\|")
        vi = (ex.get("sentence_vi") or "").replace("|", "\\|")
        cell = f"*{sent}*<br>→ *{vi}*" if vi else f"*{sent}*"
        lines.append(
            f"| `{ex['condition']}` | {cell} | {_fmt(ex['human_mean'], 2)} | "
            f"{_fmt(ex['llm_annotators_mean'], 2)} | {_fmt(ex['gpt4_paper_mean'], 2)} |"
        )

    for ex in illustrations:
        sent = ex.get("sentence") or ""
        vi = ex.get("sentence_vi") or ""
        lines += [
            "",
            f"#### `{ex['condition']}` — *{sent}* (`{ex['sample_id']}`)",
            "",
            f"*→ {vi}*" if vi else "",
            "",
            f"**Human (n={ex['human_n']}, mean={_fmt(ex['human_mean'], 2)}):** "
            f"{_fmt_scores(ex['human_scores'])}",
            "",
            f"**AI annotators (n={len(ex['ai_votes'])}, mean={_fmt(ex['llm_annotators_mean'], 2)}):**",
            "",
            "| Model | MODE | mean |",
            "|---|---|---:|",
        ]
        for v in ex["ai_votes"]:
            lines.append(
                f"| `{_short(v['model_id'])}` | `{v['mode']}` | {_fmt(v['model_mean'], 2)} |"
            )

    lines += [
        "",
        "**Ghi chú nhanh:**",
        "- `all` / *patient*: baseline; human & AI đều cao.",
        "- `global` / *intern*: human thấp hơn; nhiều AI vẫn ~5.",
        "- `animate` / *file*: human cao; AI bám khá.",
        "- `plural` / *interns*: human ~5.5; AI hơi cao.",
        "- `name` / *Matt*: human thấp nhất (~4.9); nhiều AI **over-rate** (~5–6).",
        "",
        "### Case residual điển hình (nhiều model lệch cùng câu)",
        "",
        "| sample_id | cond | sentence | human | worst model | mode | model | abs err |",
        "|---|---|---|---:|---|---|---:|---:|",
    ]
    for ex in examples:
        sent = (ex.get("sentence") or "").replace("|", "\\|")
        lines.append(
            f"| `{ex['sample_id']}` | `{ex['condition']}` | {sent} | {_fmt(ex['human_mean'], 2)} | "
            f"`{_short(str(ex['model_id']))}` | `{ex['mode']}` | {_fmt(ex['model_mean'], 2)} | "
            f"{_fmt(ex['abs_err'], 2)} |"
        )

    lines += [
        "",
        "### Nhận định",
        "",
        f"- **Dễ bám người nhất (mean r cao):** `{easiest['condition']}` "
        f"(mean r={_fmt(easiest['mean_pearson_r'])}) — {COND_GLOSS.get(easiest['condition'], '')}.",
        f"- **Khó nhất (mean r thấp):** `{hardest['condition']}` "
        f"(mean r={_fmt(hardest['mean_pearson_r'])}) — {COND_GLOSS.get(hardest['condition'], '')}.",
        f"- Theo **MAE** (thấp = gần điểm người hơn): dễ `{easiest_mae['condition']}` "
        f"(mean MAE={_fmt(easiest_mae['mean_mae'])}); khó `{hardest_mae['condition']}` "
        f"(mean MAE={_fmt(hardest_mae['mean_mae'])}).",
        f"- Paper GPT-4 cũng yếu hơn ở `{min(paper_by_c, key=lambda c: paper_by_c[c]['pearson_r'] or 9)}` "
        f"(r={_fmt(min((paper_by_c[c]['pearson_r'] for c in CONDS), default=None))}) "
        f"và mạnh ở `{max(paper_by_c, key=lambda c: paper_by_c[c]['pearson_r'] or -1)}` "
        f"(r={_fmt(max((paper_by_c[c]['pearson_r'] for c in CONDS), default=None))}) — cùng hướng zoo.",
        "",
    ]
    if examples:
        ex0 = examples[0]
        lines.append(
            f"- Ví dụ lệch lớn: `{ex0['sample_id']}` *“{ex0.get('sentence')}”* — "
            f"human≈{_fmt(ex0['human_mean'], 2)} nhưng "
            f"`{_short(str(ex0['model_id']))}`/{ex0['mode']}≈{_fmt(ex0['model_mean'], 2)} "
            f"(|err|≈{_fmt(ex0['abs_err'], 2)}); xuất hiện trong top residual của "
            f"**{ex0['n_models_in_top']}** run → lỗi mang tính **điều kiện/câu**, không chỉ 1 model."
        )

    lines += [
        "",
        "### Artifact",
        "",
        f"- `{chart}`",
        "- `M2_by_condition.csv`, `M2_condition_mean.csv`",
        "- `M2_top_residuals.csv`, `M2_hard_sentences.csv`, `M2_residual_examples.csv`",
        "- `M2_condition_examples.csv`, `M2_condition_ai_votes.csv`, `M2_condition_examples_detail.json`",
        "- `M2_summary.json`",
        "",
    ]
    upsert_report_section(out_dir / "report.md", "Mục 2 — Theo điều kiện câu", "\n".join(lines))
    print(f"easiest={easiest['condition']} r={easiest['mean_pearson_r']:.3f}")
    print(f"hardest={hardest['condition']} r={hardest['mean_pearson_r']:.3f}")
    print(f"Wrote → {out_dir / 'report.md'}")


if __name__ == "__main__":
    main()
