# Data — human ratings + machine ratings

Nguồn: repo paper [`samsam3232/llm_pretesting`](https://github.com/samsam3232/llm_pretesting).

## Dùng nhanh (khuyến nghị)

Folder [`ready/`](ready/): mỗi câu có sẵn `human_mean` + `gpt4_mean` (+ `gpt35_mean` nếu có).

| File | Dataset trong paper |
|---|---|
| `ready/tal_human_and_gpt.jsonl` | Chow et al. (Tal) |
| `ready/matt_human_and_gpt.jsonl` | Rich et al. (Matt) |
| `ready/mem_enc_human_and_gpt.jsonl` | Ours (mem_enc) |
| `ready/SAP_human_and_gpt.jsonl` | Huang et al. (SAP/Brian naming) |
| `ready/all_human_and_gpt.jsonl` | Gộp tất cả |

Ví dụ 1 dòng:

```json
{
  "sample_id": "tal_61_a",
  "sentence": "...",
  "human_mean": 5.87,
  "human_n": 31,
  "gpt4_mean": 6.45,
  "gpt4_run": "gpt_4__prompt_1##tal##num_ex#3__temp_1.5",
  "dataset": "tal"
}
```

## Raw từ tác giả

| Folder | Nội dung |
|---|---|
| [`human/`](human/) | Chỉ câu + `human_results` (list điểm người 1–7) |
| [`machine_merged/`](machine_merged/) | Câu + `human_results` + `model_results` (nhiều model/prompt) |
| [`machine_parsed/`](machine_parsed/) | CSV đã parse sẵn |

Bản gốc đầy đủ còn nằm ở [`../llm_pretesting/data/`](../llm_pretesting/data/).

## Mapping tên file ↔ paper

| Paper | Human file | Merged (máy) |
|---|---|---|
| Chow et al. | `human/tals_pretest_data.jsonl` | `machine_merged/tals_data.jsonl` |
| Rich et al. | `human/matts_pretest_data.jsonl` | `machine_merged/matts_data.jsonl` |
| Huang et al. | `human/brians_pretest_data.jsonl` | `machine_merged/SAP_data.jsonl` |
| Ours | `human/mem_enc_exp1.jsonl` | `machine_merged/mem_enc_data.jsonl` |
