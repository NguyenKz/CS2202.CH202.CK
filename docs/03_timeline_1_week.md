# 03 — Timeline 1 tuần

Giả định: **Ngày 1 = bắt đầu**, **Ngày 7 = sẵn sàng báo cáo**.  
Mỗi ngày có **1 mục tiêu chính** — không để việc dồn về cuối.

---

## Tổng quan

| Ngày | Focus | Owner chính | Output cuối ngày |
|---|---|---|---|
| **D1** | Đọc paper + chốt scope + setup | Cả nhóm | Scope data, Model A/B, repo sẵn |
| **D2** | Data + prompt baseline | M1, M3, M2 | JSONL + prompt v1 |
| **D3** | Chạy Model A + Pearson | M3, M2 | Bảng metrics Model A |
| **D4** | +3: Model B cùng data | M2, M3 | Bảng so sánh A vs B |
| **D5** | +1: error analysis | M1, M2 | Case study + tỷ lệ lỗi |
| **D6** | Demo + draft slide | M3 + cả nhóm | Demo OK + slide draft |
| **D7** | Rehearsal + polish | Cả nhóm | Slide final + demo ổn |

---

## Ngày 1 — Kickoff & scope

**Mục tiêu:** mọi người cùng hiểu paper và chốt biên giới công việc.

- [ ] Đọc paper (ít nhất abstract, intro, method, kết luận)
- [ ] Xem repo chính thức
- [ ] Chốt: **40–60 câu** hoặc **1–2 subset** paper
- [ ] Chốt **2–3 hiện tượng/cấu trúc** (M1)
- [ ] Chốt **Model A** (baseline) và **Model B** (+3)
- [ ] Tạo repo/folder code, env, README ngắn

**Không làm hôm nay:** chạy full experiment.

---

## Ngày 2 — Data & prompt

**Mục tiêu:** có data sạch + prompt dùng được.

- [ ] Chuẩn hóa JSONL (`sample_id`, `sentence`, `human_score`, `structure`)
- [ ] Kiểm tra human score (mean nếu có nhiều annotator)
- [ ] Viết prompt chấm 1–7 (M2)
- [ ] Smoke test 5 câu với Model A (M3)

**Done khi:** 5 câu chạy ra điểm hợp lệ trong [1, 7].

---

## Ngày 3 — Reproduce Model A (6đ core)

**Mục tiêu:** có kết quả so human cho Model A.

- [ ] Batch chấm toàn bộ tập
- [ ] Tính Pearson *r*, MAE, RMSE
- [ ] Plot scatter đơn giản (optional nhưng đẹp cho slide)
- [ ] Ghi lại prompt, model version, temperature, ngày chạy

**Done khi:** có bảng “Human vs Model A”.

---

## Ngày 4 — Extension +3đ

**Mục tiêu:** cùng data, model khác.

- [ ] Batch chấm bằng Model B
- [ ] Metrics giống Ngày 3
- [ ] Bảng so sánh Model A vs Model B vs Human
- [ ] Viết 5–8 câu nhận xét sơ bộ (ai gần human hơn, trên cấu trúc nào)

**Done khi:** đủ evidence cho slide “+3đ”.

---

## Ngày 5 — Extension +1đ

**Mục tiêu:** giải thích khác biệt bằng ngôn ngữ học + số liệu.

- [ ] Coarse: threshold (vd. &lt; 3 = implausible) — precision/recall đơn giản
- [ ] Fine: vài cặp câu cần phân biệt tinh — model đúng/sai bao nhiêu
- [ ] Gắn lỗi với hiện tượng (M1)
- [ ] Chọn **3–5 case study** (đúng nổi bật / sai thú vị)
- [ ] Viết đoạn phân tích cho slide + script nói

**Done khi:** +1 có số + ví dụ, không chỉ qualitative.

---

## Ngày 6 — Demo & slide draft

**Mục tiêu:** có thứ đem lên lớp (dù chưa perfect).

- [ ] Demo: nhập 4–6 câu → điểm model → so human
- [ ] Cache fallback nếu API chết
- [ ] Draft slide theo outline [07_demo_and_slides.md](07_demo_and_slides.md)
- [ ] Phân bổ thời gian nói: M1 / M2 / M3

**Done khi:** demo chạy 1 lần liền mạch + slide đủ nội dung.

---

## Ngày 7 — Rehearsal & lock

**Mục tiêu:** sẵn sàng bảo vệ.

- [ ] Rehearsal full **15 phút thuyết trình + 5 phút demo/Q&A**
- [ ] Cắt slide thừa, thống nhất số liệu
- [ ] Fix bug demo
- [ ] Chuẩn bị 5 câu hỏi dự kiến + câu trả lời ngắn
- [ ] Lock version: data, prompt, bảng số, slide PDF/PPT

**Done khi:** cả nhóm chạy thử 1 lần không vấp demo.

---

## Buffer / nếu trễ

| Nếu trễ ở… | Cắt gì trước |
|---|---|
| Data khó | Giảm còn ~40 câu, giữ 2 cấu trúc |
| Model B chậm | Vẫn chạy subset đại diện, ghi rõ |
| Specific prompt | Bỏ; giữ 1 prompt baseline |
| UI demo đẹp | Dùng CLI / notebook — miễn chạy được |

## Quy tắc làm việc tuần này

1. Mỗi tối (hoặc sáng hôm sau) cập nhật checklist trong file này.
2. Mọi số liệu trên slide phải khớp file kết quả đã lưu.
3. Không đổi Model A/B sau Ngày 4 trừ khi model hỏng hoàn toàn.
