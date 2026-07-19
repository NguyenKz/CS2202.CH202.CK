# 07 — Demo & slides

## Demo (~2 phút)

### Mục tiêu demo

Cho thấy pipeline sống: **câu → điểm plausibility 1–7 → so với human (nếu có)**.

### Kịch bản cố định

1. Mở tool (CLI / notebook / UI nhẹ)
2. Chạy **4–6 câu đã chuẩn bị**:
   - 2 câu LLM gần human
   - 1–2 câu LLM lệch (phục vụ thảo luận +1)
   - 1 câu “rất implausible” để minh họa coarse filter
3. Với mỗi câu hiện: `model_score`, `human_score` (nếu có), `structure`
4. Kết: chỉ ra 1 case đúng + 1 case sai trong &lt; 30 giây

### Fallback bắt buộc

Nếu API lỗi khi bảo vệ:

- Dùng **cache** điểm đã chạy sẵn cho bộ câu demo
- Vẫn thao tác “nhập/chọn câu → hiện điểm” để không đứng hình

### Checklist demo Ngày 6–7

- [ ] Chạy thử trên máy trình bày
- [ ] Font/terminal đủ lớn
- [ ] Không phụ thuộc path máy khác
- [ ] Có người backup bấm demo nếu speaker chính quên thao tác

---

## Outline slide (15 phút thuyết trình)

Tổng ~10–14 slides. Phân bổ thời gian gợi ý:

| Phút | Ai | Nội dung |
|---:|---|---|
| 0–1 | Mở đầu | Paper, vì sao chọn, mục tiêu đồ án |
| 1–5 | **M1** | CL background: pretest, plausibility, hiện tượng ngôn ngữ |
| 5–9 | **M2** | Method: prompt, metrics, kết quả Model A, +3 Model B |
| 9–12 | **M1+M2** | +1 error analysis + case study |
| 12–14 | **M3** | Demo |
| 14–15 | Cả nhóm | Kết luận + hạn chế + hỏi đáp chuyển tiếp |

### Danh sách slide đề xuất

1. Title (tên paper, nhóm, môn)
2. Problem: psycholinguistic pretesting
3. Research question: LLM thay human được không?
4. Vì sao đây là CL (không chỉ NLP)
5. Method overview (prompt 1–7, so human)
6. Setup nhóm (data size, structures, models)
7. Results Model A (Pearson / MAE / RMSE)
8. +3: Model B trên cùng data
9. Coarse vs fine-grained
10. +1: bảng lỗi theo hiện tượng + case studies
11. Demo slide (screenshot hoặc “live next”)
12. Kết luận + hạn chế + việc làm thêm (nếu có)
13. Q&A / References

---

## Kết luận nên nói (1 câu)

> LLM (đặc biệt model mạnh) **hữu ích cho coarse plausibility filtering**, nhưng **chưa thay được human** khi cần phán xét fine-grained trong pretest psycholinguistics.

---

## Câu hỏi GV có thể hỏi (chuẩn bị sẵn)

| Câu hỏi | Hướng trả lời ngắn |
|---|---|
| Sao không train? | Paper/method chính là zero-shot rating; finetune paper cũng không transfer tốt. |
| Pearson cao có nghĩa dùng thay người được không? | Không đủ; cần xem coarse vs fine. |
| +3 các bạn đổi gì? | Đổi model, giữ nguyên dataset và prompt. |
| Lỗi điển hình của model? | Nêu 1 hiện tượng + 1 ví dụ đã chuẩn bị. |
| Data lấy ở đâu? | Paper subset / tự thu — nói đúng nguồn nhóm dùng. |
| Temperature / prompt ảnh hưởng? | Đã cố định temperature thấp; ghi version prompt. |

---

## Rehearsal Ngày 7

- [ ] Chạy đúng 15 phút (bấm giờ)
- [ ] Demo không vượt 2–2.5 phút
- [ ] Mỗi người biết slide nào mình nói
- [ ] Thống nhất thuật ngữ: plausibility, coarse, fine-grained, pretest
- [ ] Export slide PDF backup
