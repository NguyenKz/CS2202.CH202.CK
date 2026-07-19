# 03 — Timeline 1 tuần (thực tế)

Flow: **cùng hiểu paper → notebook chung → mỗi người chạy model → có số mới làm slide/báo cáo**.

---

## Tổng quan

| Ngày | Việc | Ai |
|---|---|---|
| **D1** | Cùng đọc paper + chốt data/prompt/metrics | Cả nhóm |
| **D2** | Làm notebook chung, thử vài model, chốt 3–4 model | Cả nhóm |
| **D3–D4** | Mỗi người chạy 1–2 model trên subset + tự viết notes | Song song |
| **D5** | Gộp bảng số, case study, thống nhất kết luận (+1) | Cả nhóm |
| **D6** | Chia: Speakers làm slide/demo; Editor viết báo cáo | Theo vai trò Phase 4 |
| **D7** | Rehearsal 15+5, chốt số liệu, fallback demo | Cả nhóm |

---

## D1 — Cả nhóm đọc hiểu paper

- [ ] Đọc chung (hoặc đọc riêng rồi họp sync)
- [ ] Trả lời nhanh: paper giải quyết gì? dùng data gì? kết luận coarse/fine?
- [ ] Chốt subset (`data/ready/...` hoặc 1–2 file human/machine)
- [ ] Chốt: dùng human paper, không tự annotate gold mới

**Output:** note chung 5–10 bullet “hiểu paper”.

---

## D2 — Notebook + chọn model

- [ ] Notebook load data + prompt paper + chấm 5–10 câu
- [ ] Thử thực tế 4–6 candidate model (cái nào fail thì loại)
- [ ] Chốt **3–4 model**; chia mỗi người **1–2 model**
- [ ] Thống nhất format `results/<model>/`

**Output:** notebook chạy được + danh sách model + người phụ trách.

---

## D3–D4 — Chạy model song song

Mỗi người:

- [ ] Batch full subset đã chốt
- [ ] `scores.jsonl` + `metrics.json`
- [ ] `notes.md` nhận xét riêng

Cuối D4:

- [ ] Push lên repo team
- [ ] Báo nhanh trong group: *r*, MAE, 1 ví dụ đúng, 1 ví dụ sai

**Không** bắt đầu viết slide dài ở phase này.

---

## D5 — Gộp & phân tích chung

- [ ] Một bảng tổng Human vs tất cả model
- [ ] 3–5 case study dùng chung
- [ ] Chuẩn bị ý +1: model nào kém ở kiểu câu nào / coarse vs fine
- [ ] Giao luôn ai là Speaker A / Speaker B / Editor

**Output:** `results/summary_table.md` (hoặc CSV) = nguồn sự thật duy nhất.

---

## D6 — Slide / demo / báo cáo

| Ai | Việc hôm nay |
|---|---|
| Speaker A | Slide intro + lý thuyết + overview + setup |
| Speaker B | Slide kết quả + case study + chuẩn bị demo nhanh |
| Editor | Báo cáo viết: gộp notes + bảng số + kết luận |

- [ ] Demo chỉ cần ngắn (notebook / cache câu sẵn)
- [ ] Số trên slide = đúng file summary

---

## D7 — Rehearsal

- [ ] Full 15 phút nói + ~2 phút demo + Q&A
- [ ] Cắt slide thừa
- [ ] Fallback nếu API chết
- [ ] Lock PDF slide + link results

---

## Nếu trễ

| Trễ ở | Cắt gì |
|---|---|
| Model chậm / API lỗi | Giảm còn 2–3 model; subset nhỏ hơn |
| Chưa kịp fine-grained | Giữ Pearson + vài case study |
| Demo UI | Notebook + cache là đủ |

## Quy tắc

1. Không chia “một người chỉ đọc lý thuyết từ đầu chí cuối trong khi người khác mới được chạy model”.
2. Experiment xong mới khóa slide số liệu.
3. Mỗi model phải có owner rõ trong D2.
