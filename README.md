# CS2202.CH202.CK — Plausibility Pretesting

Đồ án cuối kỳ môn CS2202: đánh giá LLM làm **pretest độ hợp lý (plausibility) câu tiếng Anh** (thang 1–7), so với nhãn người của paper.

**Paper:** [Large Language Models for Psycholinguistic Plausibility Pretesting](https://arxiv.org/abs/2402.05455) (Findings of EACL 2024) — Amouyal, Meltzer-Asscher, Berant  
**Repo GitHub:** [NguyenKz/CS2202.CH202.CK](https://github.com/NguyenKz/CS2202.CH202.CK)  
**Upstream code/data:** [`llm_pretesting/`](llm_pretesting/) ← [samsam3232/llm_pretesting](https://github.com/samsam3232/llm_pretesting)

---

## Đóng góp chính

Trên **cùng model + cùng base prompt**, ablation 5 MODE so với pipeline gốc paper:

| MODE | JSON Schema | Thinking | Few-shot examples |
|------|:-----------:|:--------:|:-----------------:|
| **ORIG** | — | — | ✓ |
| **S** | ✓ | — | ✓ |
| **T** | — | ✓ | ✓ |
| **ST** | ✓ | ✓ | ✓ |
| **ST−E** | ✓ | ✓ | — |

Metric chính: **Pearson r** / MAE giữa `model_mean` và `human_mean` trên subset **`mem_enc`** (50 câu, `n_samples=20`).

Chi tiết: [`docs/08_ablation_json_thinking.md`](docs/08_ablation_json_thinking.md)

---

## Kết quả nhanh (đã chạy)

| Hạng | Model × MODE | Pearson r | Ghi chú |
|-----:|---|----------:|---|
| 1 | `gpt-5.6-luna` **T** | **0.785** | Vượt GPT-4 paper |
| 2 | `gpt-5.6-luna` ORIG | 0.778 | |
| 3 | GPT-4 (paper, ref) | 0.755 | `gpt4_mean` trong data — không phải gpt-4.1-mini |
| … | … | … | Xem bảng đầy đủ |
| | `llm_annotators` (mean 9 LLM) | 0.727 | Crowd pha loãng model mạnh |

- **Thinking thường giúp:** 5/6 model có cả ORIG+T thì **T ≥ ORIG** trên Pearson r (ngoại lệ nhỏ: `gpt-5.6-sol`).
- Bảng đầy đủ + cost: [`results/SUMMARY.md`](results/SUMMARY.md)
- Narrative phân tích (Mục 1–7): [`results/analysis/report.md`](results/analysis/report.md)

---

## Cấu trúc repo

```text
doan/
├── configs/               # experiment.yaml, pricing.yaml, model_coverage.yaml
├── data/                  # human + machine ratings (paper) — không tự annotate
├── docs/                  # kế hoạch, metrics, ablation, demo/slides
├── llm_pretesting/        # upstream paper (prompts, data gốc)
├── notebooks/             # deploy llama.cpp + eval + compare summary
├── scripts/               # run_muc*.py (phân tích), run_gemma_eval, …
├── src/plausibility_eval/ # MODE, prompt, parse, metrics, cost, analysis
├── results/
│   ├── <model>/<MODE>/    # calls/*.json, scores.jsonl, metrics.json, …
│   ├── SUMMARY.md         # leaderboard + cost
│   └── analysis/          # report.md + CSV/PNG Mục 1–7
├── CONG_VIEC.md           # checklist nhóm đã chốt
└── kehoach_pt.md          # kế hoạch phân tích cho slide/báo cáo
```

Mỗi run: `results/<model_dirname>/<MODE>/` với `calls/` (raw), `scores.jsonl`, `metrics.json`, `run_meta.json`.  
`model_dirname`: `/` → `__` (vd. `deepseek/deepseek-v4-flash` → `deepseek__deepseek-v4-flash`).

---

## Setup & chạy eval

```bash
cd doan
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-eval.txt
pip install -e .

# API key (không commit .env)
export OPENAI_API_KEY=...   # hoặc token OpenRouter / Gemini tùy notebook
```

**Cách 1 — Notebook**

1. Mở [`notebooks/eval/10_eval_plausibility.ipynb`](notebooks/eval/10_eval_plausibility.ipynb)
2. Điền `MODEL`, `TOKEN`, `BASE_URL`, `MODE` ∈ `{ORIG, S, T, ST, ST-E}`
3. Sau khi có `results/`: mở [`notebooks/20_compare_summary.ipynb`](notebooks/20_compare_summary.ipynb)
4. Báo cáo phân tích: [`notebooks/30_analysis_report.ipynb`](notebooks/30_analysis_report.ipynb)

**Cách 2 — Script phân tích (đã có raw results)**

```bash
python scripts/run_muc1.py   # ranking tổng thể
python scripts/run_muc2.py   # theo điều kiện câu
python scripts/run_muc3.py   # dispersion / disagreement
python scripts/run_muc5.py   # thinking delta / calibration
python scripts/run_muc6.py   # so với GPT-4 paper
# hoặc gộp:
python scripts/run_analysis.py
```

Eval **không** ghi USD lúc chạy — chỉ log tokens + raw `calls/`. Cost = token × [`configs/pricing.yaml`](configs/pricing.yaml) (sau, qua summary).

Protocol lock: [`configs/experiment.yaml`](configs/experiment.yaml) (`subset: mem_enc`, `n_samples: 20`, temperature paper-aligned).

---

## Model đã đánh giá

| Model | MODE đã chạy |
|---|---|
| gpt-5.6-luna | ORIG, T |
| gpt-5.6-sol | ORIG, T |
| moonshotai/kimi-k3 | ORIG, T |
| z-ai/glm-5.2 | ORIG, T |
| deepseek/deepseek-v4-flash | ORIG, S, T, ST |
| google/gemma-4-31b-it | ORIG, S, T, ST |
| google/gemma-3-12b-it | ORIG, S |
| google/gemini-3.6-flash | T (và smoke ORIG) |
| openai/gpt-4.1-mini | ORIG |

Ma trận budget: [`configs/model_coverage.yaml`](configs/model_coverage.yaml) — model đắt ưu tiên ORIG+ST/T; model rẻ/self-host full matrix khi đủ budget.

---

## Đọc gì trước

| Thứ tự | File | Mục đích |
|-------:|---|---|
| 1 | [`CONG_VIEC.md`](CONG_VIEC.md) | Việc nhóm đã chốt |
| 2 | [`docs/01_overview.md`](docs/01_overview.md) | Bài toán + mục tiêu điểm |
| 3 | [`docs/08_ablation_json_thinking.md`](docs/08_ablation_json_thinking.md) | Đóng góp ablation |
| 4 | [`results/analysis/report.md`](results/analysis/report.md) | Số + nhận định cho slide |
| 5 | [`kehoach_pt.md`](kehoach_pt.md) | Outline phân tích / slide |

---

## Quy ước

- Dùng nhãn người trong [`data/`](data/) — **không** tự annotate gold mới; **không** train.
- Không commit `.env` / API key.
- Commit rõ model/MODE đang phụ trách; kết quả vào `results/<model>/`.
- Prompt lấy từ paper / `llm_pretesting/llm_pretest/prompts/`.
