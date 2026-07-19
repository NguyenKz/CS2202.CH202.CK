# Đồ án CS2202 — Paper A (Plausibility Pretesting)

Kế hoạch làm trong **1 tuần** cho nhóm **3 người**.

## Paper đã chọn

| | |
|---|---|
| **Tên** | Large Language Models for Psycholinguistic Plausibility Pretesting |
| **Venue** | Findings of EACL 2024 |
| **PDF** | Paper PDF: xem repo lớp (owner) hoặc ACL Anthology |
| **ACL** | [2024.findings-eacl.12](https://aclanthology.org/2024.findings-eacl.12/) |
| **Code** | [samsam3232/llm_pretesting](https://github.com/samsam3232/llm_pretesting) |

## Mục lục tài liệu

| File | Nội dung |
|---|---|
| [01_overview.md](01_overview.md) | Tổng quan đề tài, mục tiêu điểm, deliverables |
| [02_main_tasks.md](02_main_tasks.md) | Việc chính theo 3 thành viên |
| [03_timeline_1_week.md](03_timeline_1_week.md) | Lịch ngày 1 → 7 |
| [04_implementation_steps.md](04_implementation_steps.md) | Các bước kỹ thuật |
| [05_metrics_and_eval.md](05_metrics_and_eval.md) | Độ đo + tiêu chuẩn đánh giá |
| [06_extension_plus3_plus1.md](06_extension_plus3_plus1.md) | Hướng lấy +3đ và +1đ |
| [07_demo_and_slides.md](07_demo_and_slides.md) | Demo + outline slide |

## Vai trò nhanh

| Thành viên | Vai trò | Công việc chính |
|---|---|---|
| **M1** | CL / Linguistics | Background pretest & plausibility; chọn 2–3 hiện tượng/cấu trúc câu; lead phân tích +1 (lỗi ↔ hiện tượng ngôn ngữ); phần CL trên slide |
| **M2** | Method / NLP / Metrics | Lấy/adapt prompt từ paper (Appendix A); tính Pearson / MAE / RMSE; lead +3 (chạy Model B cùng data); bảng kết quả + nhận xét số liệu |
| **M3** | Implement / Demo | Chuẩn hóa data JSONL; script gọi LLM + parse điểm; pipeline metrics; demo sống (có fallback cache); hỗ trợ chạy batch Model A/B |

Chi tiết checklist từng người: [02_main_tasks.md](02_main_tasks.md).

## Checklist “xong khi nào”

- [ ] Mini-reproduction chạy được (LLM chấm 1–7 + so human)
- [ ] Bảng Pearson / MAE / RMSE
- [ ] +3đ: cùng data, ít nhất 2 model
- [ ] +1đ: phân tích khác biệt + ví dụ lỗi
- [ ] Demo sống ~2 phút
- [ ] Slide + rehearsal 15 phút thuyết trình + 5 phút Q&A
