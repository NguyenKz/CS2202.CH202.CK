# 02 — Main tasks (chia việc 3 thành viên)

Mỗi người **owner** phần của mình; vẫn review chéo trước ngày rehearsal.

---

## M1 — CL / Linguistics

**Mục tiêu:** nhóm hiểu và kể được *vì sao đây là bài toán CL*.

### Việc chính

- [ ] Đọc kỹ phần Introduction + datasets/linguistic structures của paper
- [ ] Viết ngắn (1–2 trang hoặc slides tương đương):
  - Psycholinguistic pretesting là gì
  - Vì sao phải kiểm soát plausibility
  - Vì sao đây là CL, không chỉ NLP
- [ ] Chốt **2–3 hiện tượng / cấu trúc câu** dùng trong thí nghiệm nhóm (vd. relative clause, animacy, similarity-based interference…)
- [ ] Cùng M3 chọn/làm sạch tập câu + nhãn human
- [ ] Lead phần **+1**: gắn lỗi model với hiện tượng ngôn ngữ cụ thể
- [ ] Soạn phần CL trong slide + dự kiến câu hỏi GV

### Done khi

- Có outline CL rõ cho 4–5 phút thuyết trình
- Có danh sách hiện tượng + ví dụ câu gắn với error analysis

---

## M2 — Method / NLP / Metrics

**Mục tiêu:** method + số liệu đúng, đủ để lấy 6đ và hỗ trợ +3/+1.

### Việc chính

- [ ] **Lấy prompt từ paper** (Appendix A) — không invent từ đầu; chốt dùng **global** và/hoặc **specific**
- [ ] Adapt nhẹ nếu cần (model mới, format parse dễ hơn); ghi rõ chỗ khác paper
- [ ] (Nếu kịp) so **global prompt** vs **specific prompt** như paper
- [ ] Định nghĩa và tính:
  - Pearson *r*
  - MAE, RMSE
  - Coarse filter (threshold)
  - Fine-grained check (pairwise / discriminative)
- [ ] Lead **+3**: chạy/so sánh **Model B** trên cùng data với Model A
- [ ] Viết bảng kết quả + nhận xét ngắn cho slide
- [ ] Cùng M1 hoàn thiện phân tích +1 (tỷ lệ lỗi, case study)

### Done khi

- Có bảng số Model A vs human
- Có bảng Model A vs Model B (+3)
- Có 3–5 case study cho +1

---

## M3 — Implement / Demo

**Mục tiêu:** pipeline chạy được end-to-end + demo sống.

### Việc chính

- [ ] Setup repo / môi trường (Python, API key hoặc model local)
- [ ] Format data **JSONL**: `sample_id`, `sentence`, `human_score` (mean), metadata cấu trúc nếu có
- [ ] Script gọi LLM → parse điểm 1–7 → lưu CSV/JSON
- [ ] Script/notebook tính metrics (dùng công thức M2 chốt)
- [ ] Demo: nhập câu → hiện điểm model (+ human nếu có)
- [ ] Fallback demo offline (cache vài câu đã chấm) nếu API lỗi
- [ ] Hỗ trợ chạy batch Model A và Model B

### Done khi

- Một lệnh (hoặc notebook) chạy được trên tập data nhóm
- Demo 2 phút ổn định khi rehearsal

---

## Việc chung (cả nhóm)

| Việc | Deadline trong tuần |
|---|---|
| Chốt scope data (40–60 câu / 1–2 subset) | Ngày 1 |
| Chốt Model A và Model B | Ngày 1–2 |
| Sync tiến độ ngắn (15 phút) | Mỗi ngày hoặc cách ngày |
| Rehearsal full 20 phút | Ngày 7 |

## Ma trận trách nhiệm nhanh

| Hạng mục | M1 | M2 | M3 |
|---|---|---|---|
| Background CL | Owner | Review | — |
| Prompt + metrics | Review | Owner | Support |
| Code / data pipeline | Support | Review | Owner |
| +3 đổi model | Support | Owner | Support |
| +1 giải thích | Owner | Co-owner | Support |
| Demo | — | Support | Owner |
| Slide tổng | Co | Co | Co |
