# Tóm tắt phân tích (slide / báo cáo)

Nguồn số: `results/analysis/report.md`, artifact `M1`–`M7`, `D_schema_deltas.csv`.  
Phạm vi: **mem_enc** 50 câu; human cost là ước slide ($0.08×40 ≈ $3.20/câu), không phải hóa đơn paper.

---

## Q → A từng mục

### Mục 1 — Tổng thể
**Hỏi:** Model×MODE nào giống người nhất / kém nhất?  
**Trả lời:** #1 **luna T** (r≈0.785); GPT-4 paper ≈0.755; Thinking thường giúp (**5/6** T≥ORIG). DeepSeek / Gemma-4 / GLM ORIG ≤ Gemma-3-12B.

### Mục 2 — Điều kiện câu
**Hỏi:** Dataset/thao tác là gì? Vì sao dùng? LLM giỏi/kém kiểu đổi object nào?  
**Trả lời:**
- **Dataset:** mem_enc = **10 khung** × **5 cách đổi object-NP** (chủ ngữ/động từ giữ) = 50 câu; mỗi câu ~40 người chấm.
- **Vì sao:** Chuẩn bị thí nghiệm *similarity-based interference*; pretest để các biến thể **cùng mức plausibility** (40 cặp t-test / §4.4). Có 4 biến thể ngoài baseline vì thiết kế 40 cặp — paper **không** giải thích vì sao đúng 4 loại global/animate/plural/name.
- **Kết quả LLM:** dễ **`animate`** (mean r≈0.81); khó **`global`** (mean r≈0.49). Case: *“The art dealer brought the artist.”* human≈3.3 vs nhiều model≈6–7.

| Condition | Ý nghĩa ngắn |
|---|---|
| `all` | Baseline — object đúng kỳ vọng |
| `global` | Hợp ngữ cảnh nhưng **lệch vai** |
| `animate` | Đổi hữu sinh ↔ vô tri (thường sang đồ vật) |
| `plural` | Object số nhiều |
| `name` | Object = tên riêng |

### Mục 3 — Disagreement
**Hỏi:** Người chấm 1 vs 7 — LLM resample có phân tán giống người?  
**Trả lời:** **Không** — collapse ~91%; model_std ≪ human_std. Mean bám được → coarse OK; fine-grained (t-test cặp) chưa. Paper EACL 2024 vẫn đúng trên zoo 2025–26.

### Mục 4 — Schema *(số từ `D_schema_deltas.csv`; section report chưa viết riêng)*
**Hỏi:** JSON schema (S/ST) có giúp likeness? Sao model lớn chỉ ORIG+T?  
**Trả lời:** Schema **thường hại** (vd. DeepSeek S−ORIG Δr≈−0.14; Gemma-3 S−ORIG Δr≈−0.06). Parse vẫn ổn → lệch calibration/format. Model đắt: chỉ cần **ORIG (+T)**.

### Mục 5 — Frontier vs Gemma-3
**Hỏi:** Model frontier/lớn sao thua hoặc không hơn Gemma-3-12B?  
**Trả lời:** **Quy mô ≠ likeness.** DeepSeek/Gemma-4 thua vì bias cao / slope thấp / lỗi ở điều kiện khó — không vì “kém thông minh”. Thinking cứu một phần, chưa đủ vượt baseline nhỏ.

### Mục 6 — GPT-4 paper
**Hỏi:** Vì sao GPT-4 paper vẫn mạnh so model mới?  
**Trả lời:** Elite calibration: r≈0.755, MAE≈0.582, bias≈+0.06. Luna thắng Pearson (≈0.778) nhưng **bơm điểm** hơn (+0.31). Giả thuyết: era chat-rating vs coding/agent.

### Mục 7 — Chi phí
**Hỏi:** Ngoài nhanh hơn, $/câu có rẻ hơn ước người? Ai Pareto?  
**Trả lời:** **Có** — mọi ORIG/T rẻ hơn ước crowdsource (~$3.20/câu) khoảng **43×–4165×**. Rẻ nhất: gemma-3 ORIG. Pareto tốt: **luna T/ORIG**.

---

## Đúc kết sau nghiên cứu (có giải thích ngắn)

1. **Coarse OK — LLM thay được người khi lọc câu thô.**  
   Pearson r với `human_mean` cao (luna T ≈0.785, GPT-4 paper ≈0.755). Pretest chỉ cần bỏ câu rất vô lý / giữ câu ổn → mean LLM đủ dùng.

2. **Fine-grained chưa — variance collapse, chưa thay t-test cặp câu.**  
   Trên câu người bất đồng mạnh, model_std ≪ human_std (collapse ~91%). So cặp “cùng mức plausibility” bằng t-test người thì LM quá phẳng → không thay được (paper §5).

3. **Thinking giúp, schema thường hại.**  
   5/6 model: T ≥ ORIG trên r. Schema (S/ST) thường giảm likeness (vd. DeepSeek S−ORIG Δr≈−0.14) dù parse OK → format/calibration lệch. Budget: model đắt chạy ORIG (+T) là đủ.

4. **SOTA ≠ giống Likert crowdsource.**  
   DeepSeek / Gemma-4 ORIG thua Gemma-3-12B (r≈0.55/0.49 vs 0.64) vì bias cao, slope thấp, lỗi ở condition khó — không vì “kém thông minh” hay thiếu tham số.

5. **GPT-4 paper vẫn baseline calibration mạnh.**  
   MAE≈0.58, bias≈+0.06 (ít bơm). Luna thắng Pearson nhưng bias ≈+0.31 → thứ tự câu tốt hơn, mức điểm lệch crowdsource hơn.

6. **Lỗi theo điều kiện ngôn ngữ (`global` khó nhất).**  
   mem_enc = đổi object có kiểm soát. Mean r cao ở `animate` (≈0.81), thấp ở `global` (≈0.49): object “gần ngữ cảnh nhưng lệch vai” khó hơn đổi vô tri.

7. **API rẻ hơn crowdsource rất nhiều.**  
   Ước human ≈$3.20/câu ($0.08×40). Mọi ORIG/T: ~43×–4165× rẻ hơn. Pareto ngon: luna (r cao, ~$0.016–0.027/câu).

8. **Paper EACL 2024 vẫn đứng trên zoo 2025–26 (mem_enc).**  
   Reproduce đúng hướng: mean correlate tốt, variance LM thấp, coarse được / fine chưa. Model mới có thể hơn GPT-4 về r — không phá claim chính của paper.

---

## Map slide nhanh (~15’)

| Phút | Nội dung | Mục |
|---:|---|---|
| 0–6 | Bài toán, paper, setup (data, MODE) | Intro |
| 6–9 | Kết quả tổng + theo điều kiện | 1–2 |
| 9–12 | Disagreement, schema, frontier, GPT-4 | 3–6 |
| 12–13 | Chi phí | 7 |
| 13–15 | Demo + kết luận 8 điểm trên | Đúc kết |
