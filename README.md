# CS2202 — Đồ án Plausibility Pretesting

Repo **riêng cho nhóm** (private). Teammate clone repo này để làm việc / push kết quả.

Paper: *Large Language Models for Psycholinguistic Plausibility Pretesting* (Findings of EACL 2024)

## Cấu trúc

| Path | Nội dung |
|---|---|
| [`docs/`](docs/) | Kế hoạch 1 tuần, chia việc, metrics, demo |
| [`llm_pretesting/`](llm_pretesting/) | Code + data human ratings từ repo paper |
| [`results/`](results/) | Output thí nghiệm của nhóm (push vào đây) |

Bắt đầu đọc: [`docs/README.md`](docs/README.md) → [`docs/01_overview.md`](docs/01_overview.md)

## Data human (không cần tự chấm)

Nằm sẵn trong:

`llm_pretesting/data/llm_pretest_data/*.jsonl`

Field `human_results` = list điểm người 1–7. Khi tính metrics lấy **mean**.

## Quy ước làm việc

1. Làm trên branch riêng hoặc commit rõ ràng theo tên
2. Không commit `.env` / API key
3. Kết quả batch/metrics để trong `results/`
4. Prompt: lấy từ paper / `llm_pretesting/llm_pretest/prompts/`

## Upstream

Xem [`llm_pretesting/UPSTREAM.md`](llm_pretesting/UPSTREAM.md)
