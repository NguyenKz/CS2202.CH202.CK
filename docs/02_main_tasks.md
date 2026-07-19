# 02 — Công việc thực tế (chia theo giai đoạn)

Chia theo **phase**, không chia kiểu “một người chỉ CL / một người chỉ code mãi”.  
Cả nhóm cùng hiểu paper trước; experiment làm song song theo **model**; slide/báo cáo chia sau khi đã có số.

---

## Phase 0 — Cả nhóm cùng hiểu paper (bắt buộc)

Làm **chung**, không giao 1 người đọc hộ.

- [ ] Đọc abstract, intro, method, kết luận
- [ ] Sync 30–45 phút: paper đang giải quyết gì? coarse vs fine là gì?
- [ ] Chốt chung:
  - Dùng **nhãn human của paper** (không tự chấm dataset mới làm gold)
  - Prompt lấy từ paper / `llm_pretesting/llm_pretest/prompts/`
  - Subset data nào (vd. 1 file trong `data/ready/` hoặc 80–150 câu)
  - Metrics: Pearson, MAE/RMSE (+ coarse/fine nếu kịp)

**Done khi:** cả 3 người giải thích được bài toán bằng lời của mình.

---

## Phase 1 — Setup notebook chung + thử model

Một người dựng khung trước cũng được, nhưng **cả nhóm cùng smoke-test**.

- [ ] Tạo notebook chung (vd. `notebooks/run_models.ipynb`)
  - load câu + `human_mean`
  - gọi prompt paper
  - parse điểm 1–7
  - tính Pearson / MAE trên subset nhỏ (5–10 câu)
- [ ] Thử vài API/model để xem cái nào chạy được thật
- [ ] Chốt **3–4 model** dùng cho thí nghiệm (+3đ = so nhiều model trên cùng data)

**Done khi:** notebook chạy ổn trên 5–10 câu với ít nhất 1 model.

---

## Phase 2 — Chia model: mỗi người 1–2 model

Đây là phần song song chính.

| Thành viên | Việc |
|---|---|
| **P1** | Chạy model #1 (và #2 nếu 4 model) trên full subset đã chốt |
| **P2** | Chạy model #3 (và #4 nếu có) |
| **P3** | Chạy model còn lại + giữ notebook/metrics helper ổn định |

Mỗi người **tự**:

1. Chạy batch → lưu vào `results/<ten_model>/`
2. Tính metrics vs human
3. Viết nhận xét ngắn (½–1 trang hoặc bullet):
   - *r* / MAE thế nào
   - câu nào model gần human
   - câu nào lệch; đoán lý do (coarse/fine, kiểu câu…)

**Done khi:** có file kết quả + note nhận xét của từng model; không thiếu model đã chốt.

Gợi ý đặt tên:

```text
results/
  gpt4o/
    scores.jsonl
    metrics.json
    notes.md
  qwen/
    ...
```

---

## Phase 3 — Gộp số liệu + phân tích nhóm (+1đ)

Sau khi từng người chạy xong:

- [ ] Gộp bảng tổng: Human vs Model1 vs Model2 vs …
- [ ] So coarse vs fine (nếu làm)
- [ ] Chọn 3–5 case study chung
- [ ] Thống nhất câu kết luận nhóm sẽ nói trên lớp

**Done khi:** có **một** bảng số chuẩn để đưa lên slide (không ai dùng số khác nhau).

---

## Phase 4 — Slide, thuyết trình, báo cáo (chia sau khi có số)

Không làm slide nghiêm túc khi chưa có số.

| Vai trò thuyết trình / deliverable | Ai | Việc |
|---|---|---|
| **Speaker A — Intro / lý thuyết / overview** | 1 người | Bài toán pretest, plausibility, CL, paper hỏi gì, setup thí nghiệm nhóm |
| **Speaker B — Kết quả thực nghiệm + demo nhanh** | 1 người | Bảng số các model, nhận xét, case study, demo 1–2 phút |
| **Editor — Tổng hợp báo cáo viết** | 1 người | Gộp note + số liệu thành báo cáo / README kết quả; thống nhất slide wording |

Cả 3 vẫn cùng rehearsal. Speaker A/B không “biết mỗi phần mình”: vẫn phải hiểu số liệu chung.

---

## Việc cố ý KHÔNG làm

- Thu annotator mới làm nhãn chuẩn (đổi hệ quy chiếu)
- Train/finetune
- Invent prompt từ đầu
- Chia việc kiểu một người ngồi chờ người kia xong hết mới bắt đầu đọc paper

---

## Checklist tổng

- [ ] Phase 0: cả nhóm hiểu paper
- [ ] Phase 1: notebook chung chạy được
- [ ] Phase 2: mỗi người xong 1–2 model + notes
- [ ] Phase 3: bảng tổng + case study
- [ ] Phase 4: slide + demo + báo cáo + rehearsal
