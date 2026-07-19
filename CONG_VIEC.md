# Công việc nhóm sẽ làm

Đã chốt. Chi tiết theo ngày/phase: [`docs/02_main_tasks.md`](docs/02_main_tasks.md), [`docs/03_timeline_1_week.md`](docs/03_timeline_1_week.md).

## Nguyên tắc

- Dùng **nhãn người của paper** (`data/`) — không tự annotate gold mới
- Prompt lấy từ paper — không invent từ đầu
- Không train
- **Cả nhóm** đọc hiểu paper trước; experiment chia theo **model**; slide/báo cáo chia **sau khi có số**

## Các bước

1. **Cả nhóm đọc hiểu paper**  
   Pretest plausibility là gì, paper hỏi gì, coarse vs fine.

2. **Notebook chung + thử model**  
   Load data, gọi prompt, smoke-test → chốt **3–4 model**.

3. **Mỗi người chạy 1–2 model**  
   Batch trên cùng subset → `results/<model>/` (scores + metrics + notes nhận xét riêng).

4. **Gộp số liệu**  
   Bảng tổng Human vs các model + 3–5 case study (+3/+1).

5. **Mới chia deliverable cuối**
   - **Speaker A:** giới thiệu, lý thuyết, overview  
   - **Speaker B:** phân tích kết quả thực nghiệm + demo nhanh  
   - **Editor:** tổng hợp viết báo cáo  

6. **Rehearsal** 15 phút thuyết trình + demo/Q&A.

## Không làm

- Dataset người chấm mới làm hệ quy chiếu chính  
- Chia silo kiểu một người chỉ lý thuyết, người kia chỉ code từ đầu chí cuối  
- Làm slide số liệu khi chưa có kết quả chạy model  
