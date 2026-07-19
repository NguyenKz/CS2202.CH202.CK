# 05 — Metrics & tiêu chuẩn đánh giá

## Độ đo chính (bắt buộc)

### 1. Pearson correlation (*r*) — primary

So sánh **human_score** với **model_score** trên cùng tập câu.

- *r* gần 1 → model xếp hạng plausibility giống người
- Báo cáo *r* cho Model A và Model B
- (Optional) p-value nếu dùng scipy; không bắt buộc trên slide nếu thiếu thời gian

### 2. MAE — secondary

\[
\mathrm{MAE} = \frac{1}{n}\sum_i |y_i - \hat{y}_i|
\]

Độ lệch tuyệt đối trung bình trên scale 1–7.

### 3. RMSE — secondary

\[
\mathrm{RMSE} = \sqrt{\frac{1}{n}\sum_i (y_i - \hat{y}_i)^2}
\]

Phạt mạnh hơn các lệch lớn.

---

## Độ đo theo tinh thần paper

### Coarse-grained (lọc thô)

Mục tiêu: LLM có lọc được câu **rất kém hợp lý** không?

Ví dụ thao tác:

1. Chọn threshold *T* (vd. `T = 3`): human &lt; T ⇒ *implausible*
2. Model dự đoán implausible nếu `model_score < T`
3. Báo cáo accuracy / precision / recall đơn giản trên nhãn binary này

**Kết luận mong đợi (giống paper):** coarse thường ổn hơn fine.

### Fine-grained (phân biệt tinh)

Mục tiêu: model có giữ được quan hệ tinh giữa câu không?

Cách làm thực tế cho đồ án:

- Chọn các **cặp câu** cần plausibility gần nhau hoặc khác nhau theo thiết kế thí nghiệm
- Kiểm tra model có **cùng chiều** với human không (vd. human: A &gt; B; model cũng A &gt; B?)
- Báo cáo **tỷ lệ cặp đúng chiều** + ví dụ fail

---

## Bảng kết quả mẫu (điền khi chạy xong)

| Model | Pearson *r* | MAE | RMSE | Coarse Acc | Fine pair Acc |
|---|---:|---:|---:|---:|---:|
| Model A | | | | | |
| Model B | | | | | |

Ghi chú bắt buộc dưới bảng: số câu *n*, prompt version, temperature, ngày chạy.

---

## Tiêu chuẩn tự đánh theo rubric môn

### Đủ 6đ khi

- [ ] Paper đúng ACL + ≤3 năm + có LLM
- [ ] Có implement lại (mini-reproduction chạy được)
- [ ] Có slide + báo cáo 15 phút
- [ ] Có demo
- [ ] Số liệu Model A vs human được trình bày rõ

### Đủ +3đ khi

- [ ] Có **thêm 1 trục so sánh**: **cùng dataset, model khác** (hướng nhóm đã chốt)
- [ ] Bảng so sánh Model A vs Model B (cùng metrics)
- [ ] Nêu khác biệt định lượng (không chỉ “model B tốt hơn”)

### Đủ +1đ khi

- [ ] Giải thích *vì sao* A và B khác nhau
- [ ] Gắn với **hiện tượng ngôn ngữ** hoặc **loại lỗi** cụ thể
- [ ] Có **tỷ lệ / đếm** (vd. 3/10 cặp fine-grained fail)
- [ ] Có 3–5 ví dụ minh họa (đúng của A / sai của B hoặc ngược lại)

---

## Ngưỡng “đẹp để báo cáo” (nội bộ, không phải của paper)

Không cứng nhắc, chỉ để biết kết quả có kể chuyện được không:

| Tín hiệu | Gợi ý diễn giải trên slide |
|---|---|
| *r* cao (&gt; ~0.7) | Model theo được xu hướng human |
| *r* trung bình | Dùng được coarse, cần xem cấu trúc nào kéo *r* xuống |
| Coarse tốt, fine kém | Khớp kết luận paper → điểm thảo luận mạnh |
| Model B lệch nhiều trên 1 structure | Vật liệu vàng cho +1 |

Nếu *r* thấp bất thường: kiểm tra parse score, prompt, scale đảo, hoặc human label lỗi trước khi kết luận model kém.
