# 06 — Hướng phát triển (+3đ và +1đ)

Mục tiêu: sau mini-reproduction (6đ), lấy thêm **+3** và **+1** để đủ **10đ**.

---

## +3đ — Đánh giá mở rộng (hướng đã chốt)

**Chọn hướng:** cùng **dataset / tập câu của nhóm**, đánh giá trên **model khác**.

| | Model A (baseline) | Model B (so sánh) |
|---|---|---|
| Vai trò | Gần tinh thần paper / model mạnh hoặc model nhóm chọn làm mốc | Model khác hẳn (family hoặc size khác) |
| Ví dụ | GPT-4o / Claude / model paper-like | Qwen, Gemini, Llama nhỏ, GPT-3.5-class… |
| Điều kiện | Cùng prompt, cùng data, cùng cách parse | Giống Model A |

### Việc phải nộp trên slide

1. Bảng metrics A vs B (Pearson, MAE, RMSE, coarse/fine nếu có)
2. 1 slide nhận xét: model nào gần human hơn, trên cấu trúc nào
3. Ghi rõ tên model + version (không ghi chung “GPT”)

### Không làm (tránh phình scope)

- Train / finetune
- Đổi cùng lúc cả model lẫn dataset (khó giải thích)
- Quá nhiều model (&gt;2) nếu chưa xong demo

---

## +1đ — Giải thích khác biệt

Rubric môn muốn kiểu: **hiện tượng / lỗi cụ thể + tỷ lệ + ví dụ**.

### Khung phân tích cố định

1. **Chia theo cấu trúc ngôn ngữ** (do M1 chốt):  
   relative clause / animacy / interference / …
2. Với mỗi cấu trúc, so:
   - *r* hoặc MAE của Model A vs Model B
   - coarse fail rate
   - fine pair fail rate
3. Chọn **3–5 case study**:

| ID | Câu (rút gọn) | Human | Model A | Model B | Hiện tượng | Nhận xét |
|---|---|---:|---:|---:|---|---|
| | | | | | | |

### Câu hỏi cần trả lời trên slide +1

- Model nào giải quyết được hiện tượng X mà model kia không?
- Lệch chủ yếu ở coarse hay fine-grained?
- Có pattern lỗi lặp lại không? (vd. câu cú pháp ổn nhưng nghĩa lạ vẫn bị chấm cao)

### Ví dụ cách viết đạt (mẫu)

> Trên 12 cặp fine-grained thuộc nhóm relative clause, Model A đúng chiều human 9/12 (75%), Model B đúng 5/12 (42%). Model B thường over-rate câu có animate subject dù overall proposition kém hợp lý (ví dụ sample_id=…).

---

## Thứ tự ưu tiên nếu thiếu thời gian

1. Xong bảng A vs B (+3) trên **toàn bộ** data nhỏ
2. Xong **ít nhất 3 case study** + 1 bảng tỷ lệ theo 1 cấu trúc (+1 tối thiểu)
3. Mới mở rộng thêm cấu trúc thứ 2–3

## Checklist đóng gói +3/+1

- [ ] Model A và B chạy trên cùng `sentences.jsonl`
- [ ] Prompt giống nhau
- [ ] Bảng số trên slide = file output đã lưu
- [ ] +1 có **số** (tỷ lệ) + **ví dụ**
- [ ] Có câu kết: LLM dùng được cho pretest mức nào (coarse vs fine)
