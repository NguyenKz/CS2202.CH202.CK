# 01 — Overview

## Bài toán

Trong psycholinguistics, trước khi chạy thí nghiệm đọc hiểu, nhà nghiên cứu phải **pretest** độ hợp lý (*plausibility*) của câu — thường nhờ người chấm scale **1–7**.

**Câu hỏi nghiên cứu của paper:** LLM có thể thay người ở bước pretest này không?

## Paper

| | |
|---|---|
| **Tên** | Large Language Models for Psycholinguistic Plausibility Pretesting |
| **Tác giả** | Amouyal, Meltzer-Asscher, Berant |
| **Venue** | Findings of EACL 2024 |
| **Nguồn** | ACL Anthology (đúng yêu cầu môn) |
| **LLM** | Có (GPT-4, GPT-3.5, các LM open-source…) |
| **Code** | [samsam3232/llm_pretesting](https://github.com/samsam3232/llm_pretesting) |

### Kết luận chính của paper (để nhớ khi báo cáo)

- GPT-4 **tương quan cao** với human trên nhiều cấu trúc.
- LLM **ổn cho coarse filtering** (lọc câu rất kém hợp lý).
- LLM **chưa đủ** khi cần **fine-grained** discrimination (phân biệt tinh hai câu gần nhau).

## Vì sao chọn paper này

- **CL chính:** bài toán judgment ngôn ngữ / pretest thí nghiệm.
- **NLP phụ:** LLM chỉ là công cụ chấm điểm.
- **Không cần train:** prompt → lấy điểm → so human.
- Dễ demo, dễ chia việc 3 người, dễ lấy +3/+1.

## Mục tiêu điểm đồ án

| Điểm | Việc phải làm |
|---|---|
| **6đ** | Đọc paper, mini-reproduce, slide, báo cáo 15 phút + demo |
| **+3đ** | Cùng dataset, đánh giá trên **model khác** (hoặc dataset khác — nhóm chốt hướng đổi model) |
| **+1đ** | Giải thích vì sao kết quả khác: hiện tượng ngôn ngữ, lỗi cụ thể, tỷ lệ |

**Target nhóm: 10/10.**

## Scope (mini-reproduction)

Làm đủ đẹp trong 1 tuần — **không** reproduce full mọi model/dataset của paper.

1. Chọn **1–2 subset** hoặc **40–60 câu** theo 2–3 cấu trúc/hiện tượng.
2. Có **human ratings** 1–7 (reuse data paper hoặc tự thu).
3. Prompt **Model A** chấm cùng scale.
4. Tính Pearson, MAE/RMSE + vài ví dụ đúng/sai.
5. Chạy **Model B** trên cùng data (+3).
6. Phân tích khác biệt (+1).
7. Demo + slide.

## Deliverables cuối tuần

| Deliverable | Owner chính |
|---|---|
| Data JSONL (câu + human score) | M1 + M3 |
| Script gọi LLM + parse score | M3 |
| Bảng metrics (Model A, Model B) | M2 |
| Error analysis / case study (+1) | M1 + M2 |
| Demo chạy được | M3 |
| Slide + script thuyết trình | Cả nhóm |

## Rủi ro cần tránh

- Cố reproduce full paper → trễ timeline.
- Không ghi rõ model version / prompt → khó bảo vệ.
- Demo phụ thuộc mạng/API không có fallback.
- +1 chỉ nói chung chung, thiếu số liệu và ví dụ.
