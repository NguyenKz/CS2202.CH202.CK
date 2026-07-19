# Đồ án CS2202 — Paper A (Plausibility Pretesting)

Kế hoạch **1 tuần**, nhóm **3 người**.  
Chia theo **phase thực tế**, không chia silo “một người chỉ lý thuyết / một người chỉ code”.

## Paper đã chọn

| | |
|---|---|
| **Tên** | Large Language Models for Psycholinguistic Plausibility Pretesting |
| **Venue** | Findings of EACL 2024 |
| **PDF** | Repo lớp (owner) hoặc [ACL](https://aclanthology.org/2024.findings-eacl.12/) |
| **Code upstream** | [samsam3232/llm_pretesting](https://github.com/samsam3232/llm_pretesting) |
| **Data sẵn** | [`../data/`](../data/) (human + machine) |

## Mục lục

| File | Nội dung |
|---|---|
| [01_overview.md](01_overview.md) | Tổng quan, mục tiêu điểm |
| [02_main_tasks.md](02_main_tasks.md) | **Công việc theo phase (đọc cái này trước)** |
| [03_timeline_1_week.md](03_timeline_1_week.md) | Lịch D1→D7 |
| [04_implementation_steps.md](04_implementation_steps.md) | Notebook / gọi LLM |
| [05_metrics_and_eval.md](05_metrics_and_eval.md) | Pearson, MAE, coarse/fine |
| [06_extension_plus3_plus1.md](06_extension_plus3_plus1.md) | Nhiều model = +3; phân tích = +1 |
| [07_demo_and_slides.md](07_demo_and_slides.md) | Slide, demo, báo cáo |

## Flow làm việc (tóm tắt)

1. **Cả nhóm** đọc hiểu paper  
2. Làm **notebook chung**, thử model, chốt 3–4 model  
3. **Mỗi người 1–2 model** → chạy + tự nhận xét → push `results/`  
4. Gộp bảng số + case study  
5. Mới chia deliverable cuối:
   - Speaker A: intro / lý thuyết / overview  
   - Speaker B: phân tích kết quả + demo nhanh  
   - Editor: tổng hợp báo cáo viết  

Chi tiết: [02_main_tasks.md](02_main_tasks.md)

## Checklist xong

- [ ] Cả nhóm hiểu paper  
- [ ] Notebook chạy được  
- [ ] ≥3 model có metrics vs human  
- [ ] Bảng tổng + nhận xét (+3/+1)  
- [ ] Slide + demo + báo cáo + rehearsal  
