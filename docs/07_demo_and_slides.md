# 07 — Demo, slide & báo cáo

Làm **sau Phase 2–3** (đã có số từng model + bảng tổng).

---

## Vai trò deliverable (3 người)

| Vai trò | Trên lớp / nộp | Việc |
|---|---|---|
| **Speaker A** | Thuyết trình phần đầu | Giới thiệu, lý thuyết pretest/plausibility, overview paper, setup thí nghiệm nhóm |
| **Speaker B** | Thuyết trình phần sau + demo | Phân tích kết quả các model, case study, demo nhanh 1–2 phút |
| **Editor** | Báo cáo viết | Tổng hợp notes + metrics thành báo cáo; so số liệu trên slide cho khớp |

Cả nhóm cùng rehearsal. Editor không “không cần hiểu thí nghiệm”.

---

## Demo (~1–2 phút)

Speaker B chạy:

1. Chọn 3–5 câu đã cache
2. Hiện human_mean vs điểm 1–2 model tiêu biểu
3. Chỉ nhanh 1 case gần human + 1 case lệch

Fallback: không gọi API live nếu mạng/API rủi ro — dùng output đã lưu trong `results/`.

---

## Outline slide (15 phút)

| Phút | Ai | Nội dung |
|---:|---|---|
| 0–6 | Speaker A | Bài toán, paper, data/prompt, setup nhóm |
| 6–13 | Speaker B | Bảng kết quả multi-model, phân tích, +1, demo |
| 13–15 | A hoặc B | Kết luận + hạn chế; Editor nhắc Q&A đã chuẩn bị |

### Slide đề xuất

1. Title  
2. Vấn đề pretest plausibility  
3. Câu hỏi paper + kết luận chính của paper  
4. Setup nhóm (data, prompt, 3–4 model, ai chạy model nào)  
5–7. Kết quả từng model / bảng tổng  
8. Case study + coarse/fine  
9. Demo  
10. Kết luận  
11. References / Q&A  

---

## Báo cáo viết (Editor)

Gợi ý mục:

1. Giới thiệu bài toán & paper  
2. Data & protocol (human paper, prompt paper, models)  
3. Kết quả (bảng + plot nếu có)  
4. Thảo luận / khác biệt giữa models (+1)  
5. Kết luận & hạn chế  
6. Phân công & link `results/`

Nguồn: `results/*/notes.md` + `results/summary_table.*` — không bịa số.

---

## Câu hỏi GV thường gặp

| Câu hỏi | Trả lời ngắn |
|---|---|
| Sao không tự annotate? | Giữ hệ quy chiếu human của paper. |
| +3 là gì? | Cùng data, nhiều model khác nhau. |
| Kết luận chính? | Coarse khá ổn; fine vẫn yếu (đối chiếu paper + số nhóm). |
| Ai chạy model nào? | Nêu đúng phân công Phase 2. |
