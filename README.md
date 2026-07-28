# CS2202 — Đồ án Plausibility Pretesting

Repo **riêng cho nhóm** (private). Teammate clone repo này để làm việc / push kết quả.

Paper: *Large Language Models for Psycholinguistic Plausibility Pretesting* (Findings of EACL 2024)

## Cấu trúc

| Path | Nội dung |
|---|---|
| [`docs/`](docs/) | Kế hoạch 1 tuần, chia việc, metrics, demo |
| [`llm_pretesting/`](llm_pretesting/) | Code + data human ratings từ repo paper |
| [`data/`](data/) | Human + machine ratings (đã kéo về, xem `data/README.md`) |
| [`configs/`](configs/) | `experiment.yaml`, `pricing.yaml` (cost sau), `model_coverage.yaml` |
| [`src/plausibility_eval/`](src/plausibility_eval/) | Helpers: MODE, prompt, parse, raw logger, summary |
| [`notebooks/`](notebooks/) | Deploy llama.cpp, eval (MODEL/TOKEN/BASE_URL/MODE), summary |
| [`results/`](results/) | Output thí nghiệm của nhóm (push vào đây) |

### Chạy thí nghiệm nhanh

```bash
pip install -r requirements-eval.txt
# Mở notebooks/eval/10_eval_plausibility.ipynb
# Điền MODEL, TOKEN, BASE_URL, MODE ∈ {ORIG,S,T,ST,ST-E}
# Sau khi có results/: mở notebooks/20_compare_summary.ipynb
```

Eval **không** ghi USD — chỉ tokens + raw `calls/`. Cost = summary × `configs/pricing.yaml`.

Bắt đầu đọc: [`CONG_VIEC.md`](CONG_VIEC.md) → [`docs/02_main_tasks.md`](docs/02_main_tasks.md)

## Cách làm (thực tế)

1. Cả nhóm đọc hiểu paper  
2. Notebook chung → chốt 3–4 model  
3. Mỗi người chạy 1–2 model + tự nhận xét → `results/`  
4. Có số xong mới chia: Speaker A (intro/lý thuyết), Speaker B (kết quả + demo), Editor (báo cáo)

## Hướng đóng góp chính (đã chốt)

Trên **cùng 1 model + cùng base prompt**, ablation vs pipeline gốc:

| ID | Schema | Thinking | Examples |
|---|---|---|---|
| ORIG | Không | Không | Có |
| S | Có | Không | Có |
| T | Không | Có | Có |
| ST | Có | Có | Có |
| ST−E | Có | Có | Không |

Chi tiết: [`docs/08_ablation_json_thinking.md`](docs/08_ablation_json_thinking.md)

**Budget (báo cáo ban đầu):** model lớn/đắt chỉ đánh giá **ORIG + ST**; full 5 MODE dành cho model rẻ / self-host. Xem [`CONG_VIEC.md`](CONG_VIEC.md).

## Data human (không cần tự chấm)

Dùng [`data/`](data/) — lấy `human_mean` / `mean(human_results)`. Không tự annotate gold mới.

## Quy ước làm việc

1. Commit rõ tên / model đang phụ trách  
2. Không commit `.env` / API key  
3. Kết quả để trong `results/<model>/`  
4. Prompt: paper / `llm_pretesting/llm_pretest/prompts/`

## Upstream

Xem [`llm_pretesting/UPSTREAM.md`](llm_pretesting/UPSTREAM.md)
