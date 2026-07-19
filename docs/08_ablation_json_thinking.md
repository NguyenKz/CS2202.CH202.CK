# 08 — Hướng đóng góp: JSON schema × Thinking × Examples

Thí nghiệm trên **cùng 1 model**, **cùng base prompt** (instruction paper), **cùng subset data + human gold**.  
Chỉ đổi cách *elicitation* (schema / thinking / có-examples).

Mục tiêu “tốt hơn” = **gần human hơn** (Pearson ↑, MAE ↓), không phải điểm cao hơn.

---

## Pipeline gốc (baseline paper-like)

Gọi tắt: **ORIG**

- Prompt paper (có few-shot examples)
- Free-text output
- Parse số 1–7 bằng regex/word (như `parse_prediction`)
- Không JSON schema
- Không thinking / reasoning mode

---

## Các điều kiện thí nghiệm (ablations)

Tất cả so với **ORIG** trên cùng model + cùng câu.

| ID | Tên ngắn | JSON schema | Thinking | Few-shot examples | So với ORIG để trả lời gì |
|---|---|---|---|---|---|
| **ORIG** | Baseline | Không | Không | Có | Mốc paper-like |
| **S** | Schema only | Có | Không | Có | Schema có giúp gần human / parse sạch hơn không? |
| **T** | Thinking only | Không | Có | Có | Thinking có giúp gần human không? |
| **ST** | Schema + Thinking | Có | Có | Có | Kết hợp có cộng hưởng không? |
| **ST−E** | Schema + Thinking − Examples | Có | Có | **Không** | Bỏ example (giảm chi phí) còn giữ được chất lượng không? |

Ghi chú: user liệt kê 4 hướng so ORIG; bảng trên phủ đủ:

1. **ST vs ORIG** — schema + thinking  
2. **S vs ORIG** — chỉ schema  
3. **T vs ORIG** — chỉ thinking  
4. **ST−E vs ORIG** — schema + thinking, bỏ example  

(Có thể thêm **S−E** sau nếu còn thời gian; không bắt buộc.)

---

## Thiết kế công bằng

Giữ cố định:

- Model (1 model chính; có thể lặp lại sau trên model 2 nếu kịp +3 multi-model)
- Subset câu + `human_mean`
- Định nghĩa thang 1–7 (plausibility đời thường)
- Cách aggregate: 1 lần hoặc N sample — **đồng nhất mọi điều kiện**; ghi rõ trong notes

Chỉ thay:

- `response_format` / JSON schema on-off  
- Thinking on-off  
- Examples on-off (chỉ ở **ST−E**)

---

## JSON schema (gợi ý)

```json
{
  "type": "object",
  "properties": {
    "score": {
      "type": "integer",
      "minimum": 1,
      "maximum": 7,
      "description": "Everyday-life plausibility of the sentence. 1 = almost impossible/absurd, 7 = highly natural. Grammar is already correct; judge the situation/meaning only."
    },
    "reason": {
      "type": "string",
      "description": "One short sentence explaining why this score was chosen."
    }
  },
  "required": ["score"]
}
```

Với thinking: lấy **score cuối** sau reasoning; không dùng độ dài thinking làm metric.

---

## Metrics bắt buộc mỗi điều kiện

| Metric | Ý nghĩa |
|---|---|
| Pearson *r* | Xu hướng xếp hạng giống human |
| MAE / RMSE | Lệch tuyệt đối với human_mean |
| Parse fail rate | % lần không lấy được score hợp lệ |
| (Optional) Chi phí token / latency | Trade-off bỏ example / bật thinking |

Bảng tổng đưa lên slide:

| Condition | *r* | MAE | Parse fail | Ghi chú |
|---|---:|---:|---:|---|
| ORIG | | | | |
| S | | | | |
| T | | | | |
| ST | | | | |
| ST−E | | | | |

---

## Cách chia việc (khớp plan nhóm)

Trên **1 model đã chốt**:

| Người | Chạy |
|---|---|
| P1 | ORIG + S |
| P2 | T + ST |
| P3 | ST−E + gộp bảng / notes tổng |

Hoặc mỗi người full matrix trên model mình — nếu đã chia 3–4 model ở phase khác. **Ưu tiên:** xong đủ 5 điều kiện trên **1 model** trước (câu chuyện ablation sạch).

Output mỗi điều kiện:

```text
results/<model>/ablation/
  ORIG/
  S/
  T/
  ST/
  ST-E/
  summary.md
```

---

## Câu kết luận mẫu (sau khi có số)

Điền đúng theo kết quả thật:

- Schema giúp chủ yếu **parse** hay cả **gần human**?  
- Thinking có cải thiện **fine-grained** không, hay chỉ làm chậm/đắt?  
- **ST−E**: bỏ example có mất bao nhiêu *r* so với ST / ORIG? Có đáng để giảm chi phí không?

---

## Khớp rubric môn

| Điểm | Gắn thế nào |
|---|---|
| **6đ** | Reproduce ORIG (prompt paper, free text) |
| **+3** | So các điều kiện elicitation (S/T/ST/ST−E) trên cùng data — hoặc thêm model khác |
| **+1** | Giải thích condition nào gần human hơn ở kiểu câu nào; trade-off chi phí |

Đây là hướng đóng góp chính của nhóm so với paper 2024.
