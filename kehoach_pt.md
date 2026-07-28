# Kế hoạch phân tích số liệu (cho slide & báo cáo)

> **Chỉ là kế hoạch** — làm **từng mục một** theo thứ tự 1→7.  
> Không phải sổ tay cột CSV; khi triển khai mới mở notebook/tính số.  
> **Kết quả narrative (bảng + nhận định) lưu chung vào** [`results/analysis/report.md`](results/analysis/report.md). Artifact CSV/JSON cùng thư mục.

Paper nhóm: *Large Language Models for Psycholinguistic Plausibility Pretesting* (EACL 2024 Findings).  
Thí nghiệm ablation MODE đã chạy xong → giai này = **đọc số → kể chuyện trên slide**.

---

## Học từ đồ án mẫu (`thamkhao/do_an_example`)

Slide mẫu THOR kể theo: **Giới thiệu → Phương pháp → Setup → Kết quả → Phân tích lỗi → Kết luận → Demo**.

Áp vào bài mình (không copy ISA / không bắt buộc fine-tune):

| Mẫu làm tốt | Mình làm tương ứng |
|---|---|
| Bảng kết quả rõ trước | Mục 1–2 (tổng thể + theo điều kiện câu) |
| **Phân tích lỗi**: taxonomy + %/count + ví dụ câu cụ thể | Mục 3–6 (không chỉ Pearson) |
| Ablation có nhận xét | Mục 4 (ORIG/S/T/ST; schema hại likeness) |
| Kết luận + hạn chế + demo cache | Slide cuối + demo từ `results/` (không phụ thuộc API live) |

---

## Đánh giá: đã đủ làm đồ án môn chưa?

Theo `docs/01_overview.md` (target 10/10):

| Điểm | Yêu cầu | Hiện trạng |
|---|---|---|
| **6đ** | Đọc paper + mini-reproduce + slide 15’ + demo | **Thí nghiệm đã đủ/dư** (nhiều model, mem_enc 50, ORIG/S/T/ST, raw `calls/`, SUMMARY). **Chưa đủ deliverable**: slide thuyết trình, demo 1–2’, báo cáo viết. |
| **+3đ** | Cùng data, đánh giá model khác | **Đã vượt** (luna, sol, kimi, glm, deepseek, gemma, gemini, …). |
| **+1đ** | Giải thích vì sao khác: hiện tượng, lỗi cụ thể, tỷ lệ | **Chưa đủ chuẩn mẫu**: cần case câu + pattern/tỷ lệ, không chỉ bảng r/MAE. |

**Kết luận:** không cần chạy thêm model để “đủ điểm thí nghiệm”. Rủi ro điểm nằm ở **đóng gói slide + demo + phân tích lỗi/story** (Mục 1–7 dưới đây). Nhóm đã chốt **không train** — vẫn đạt 10 nếu +3/+1 vững; không cần bắt chước LoRA của mẫu.

### Deliverable còn thiếu (ngoài phân tích số)

- [ ] Slide PDF ~15 phút (outline cuối file)  
- [ ] Demo 1–2’ từ kết quả đã cache trong `results/`  
- [ ] Báo cáo viết (Editor) khớp số trên slide  
- [ ] Rehearsal Q&A  

---

## Thuật ngữ nhanh

| Từ | Nghĩa |
|---|---|
| **“Giống người”** | Pearson r (chính) / MAE (phụ) giữa `model_mean` và `human_mean` trên cùng câu. |
| **MODE** | `ORIG` / `S` / `T` / `ST` (cách prompt). Luôn nêu kèm model. |
| **Điều kiện câu** | Hậu tố `sample_id`: `all` \| `global` \| `animate` \| `plural` \| `name` — manipulation object-NP, không phải “topic tin tức”. |
| **GPT-4 paper** | `gpt4_mean` trong `data/ready/…` — **khác** `openai/gpt-4.1-mini`. |
| **Human raw** | `human_results` trong `data/human/mem_enc_exp1.jsonl`. |

Nguồn số: `results/**/scores.jsonl`, `results/SUMMARY.md`, `data/ready/`, `data/human/`. Không sửa raw `calls/` / `scores.jsonl`.  
**Viết nhận định:** `results/analysis/report.md` (mỗi mục = một section `## Mục N — …`).

---

# Bảy mục phân tích (làm từng cái)

Mỗi mục: **câu hỏi slide** → **lấy số ở đâu** → **đưa lên slide gì** → **câu kết luận mẫu** → checkbox.

---

## Mục 1 — Kết quả tổng thể

**Câu hỏi slide:** Trên cả 50 câu mem_enc, model×MODE nào giống người nhất / kém nhất?

**Lấy số từ đâu**
- `results/SUMMARY.md` hoặc `python scripts/run_muc1.py` → CSV `M1_*.csv` + section trong `results/analysis/report.md`.
- Chỉ dùng run đủ 50 câu; bỏ smoke (vd. gemini ORIG n=1).

**Đưa lên slide**
- **Một bảng tổng hợp**: ORIG + T + `gpt-4 (paper)` + `llm_annotators`, sort Pearson r.
- Không trộn MODE rồi nói “model X tốt nhất” khi so từng model — nêu kèm MODE.
- `llm_annotators` = trung bình đều mọi LLM (1 model = 1 vote; trừ paper).

**Kết luận đã điền số** (chi tiết: `results/analysis/report.md` § Mục 1)

> Một bảng tổng hợp ORIG+T+gpt-4 paper+`llm_annotators`, sort Pearson r.  
> #1 **luna T** (r=0.785); **gpt-4 (paper)** tham chiếu r=0.755; **llm_annotators** hạng #5 (r=0.727).  
> Thinking: **5/6** model T ≥ ORIG; ngoại lệ **sol** (Δr≈−0.03, có thể nhiễu / n=50).  
> Chỉ luna ORIG/T vượt paper; biểu đồ: `M1_agreement_vs_gpt4paper.png` trong `report.md`.  
> Neo Mục 5: DeepSeek / Gemma-4 / GLM đều **thua hoặc ≈** Gemma-3-12B trên ORIG r.

- [x] Bảng tổng hợp ORIG/T/paper/llm_annotators  
- [x] 2–3 câu nhận định có số  
- [x] Ghi sẵn các “chỗ lạ” để Mục 5 (vd. DeepSeek/GLM thua Gemma-3)  
- [x] `llm_annotators` trong cùng ranking

---

## Mục 2 — Theo điều kiện câu (all / global / animate / plural / name)

**Câu hỏi slide:** LLM giống người ở nhóm câu nào? Kém ở nhóm nào?

**Lấy số từ đâu**
- Parse `sample_id` → 5 điều kiện × 10 câu.
- Pearson / MAE theo từng điều kiện cho ORIG và T (model tiêu biểu + trung bình qua model).

**Đưa lên slide**
- 1 heatmap hoặc bảng nhỏ: hàng = model\|MODE, cột = 5 điều kiện.
- **1 câu minh họa / condition** (cùng khung `s1`: patient → intern → file → interns → Matt).
- 2–3 câu residual: `|model_mean − human_mean|` lớn (ghi sentence + human vs model).

**Câu kết luận mẫu**
> Trung bình, điều kiện **`animate`** dễ bám người nhất (mean r≈0.81); **`global`** khó nhất (mean r≈0.49). Paper cũng yếu ở `global`. Ví dụ: `s3_global` “The art dealer brought the artist.” human≈3.3 vs nhiều model≈6–7.

- [x] Bảng/heatmap theo điều kiện  
- [x] 2–3 case residual  
- [x] 1 đoạn kết luận nhóm mạnh/yếu  

Chi tiết: `results/analysis/report.md` § Mục 2 (`python scripts/run_muc2.py`).

---

## Mục 3 — Chỗ người chấm lệch nhau vs LLM có phân tán không?

**Câu hỏi slide:** Câu người cho 1 và người khác cho 7 — LLM có “feel” phân tán giống người hay luôn ra điểm gần nhau?

**Lấy số từ đâu**
- `data/human/mem_enc_exp1.jsonl` → `human_std` / `human_range`.
- Top ~10–15 câu disagreement cao.
- `model_scores` trong `scores.jsonl` → `model_std` cùng câu.

**Đưa lên slide**
- Bảng ngắn: sample_id | human_std | model_std (1–2 model).
- 1 hình histogram cạnh nhau (human vs model samples) cho 1–2 câu.
- Caveat 1 dòng: std người = nhiều annotator; std model = nhiều lần gọi API.

**Câu kết luận mẫu**
> Trên câu disagreement cao, hầu hết model có std thấp hơn người nhiều (collapse rate≈0.91; 11/15 run≥0.99). Luna ORIG model_std≈0.30 vs human≈2.0 trên top-15.

- [x] Chọn top câu disagreement  
- [x] So dispersion + 1–2 plot  
- [x] Kết luận collapse hay không  

Chi tiết: `results/analysis/report.md` § Mục 3 (`python scripts/run_muc3.py`).

---

## Mục 4 — Schema làm giảm “giống người”

**Câu hỏi slide:** Vì sao model nhỏ chạy S/ST mà schema không giúp (thường hại) likeness — và vì sao model lớn chỉ ORIG+T?

**Lấy số từ đâu**
- Model có đủ matrix: deepseek-v4-flash, gemma-4-31b, gemma-3-12b.
- ΔPearson / ΔMAE: `S − ORIG`, `ST − T`.
- `parse_fail_rate` (thường ~0 → không phải lỗi parse).

**Đưa lên slide**
- 1 bảng Δ nhỏ.
- 1 bullet: ORIG = free-text giống instruction người; S = ép JSON → lệch kênh rating.

**Câu kết luận mẫu**
> Schema không tăng likeness (vd. deepseek S−ORIG Δr≈…); parse vẫn ổn → hại ở calibration/format. Nên model lớn chỉ ORIG (+T).

- [ ] Bảng Δ schema  
- [ ] Giải thích ngắn (không dài lý thuyết)  
- [ ] Recommendation vận hành trên slide  

---

## Mục 5 — Ai tốt / ai tệ + nghịch lý frontier vs Gemma-3-12B

**Câu hỏi slide (trọng tâm zoo model):**  
Kimi-K3, GLM-5.2, DeepSeek-v4-flash… là frontier / rất lớn — sao có cái **thua hoặc không hơn** Gemma-3-12B trên giống người?

**Neo số (ORIG, Pearson r — cập nhật lại khi làm; lấy từ SUMMARY):**

| Hiện tượng | Gợi ý số hiện có |
|---|---|
| DeepSeek-v4-flash thua Gemma-3-12B | ~0.55 vs ~0.64 |
| Gemma-4-31B thua Gemma-3-12B | ~0.49 vs ~0.64 |
| GLM-5.2 ≈ / dưới Gemma-3 | ~0.63 vs ~0.64 |
| Kimi-K3 hơn Gemma-3 nhưng dưới luna | ~0.69 vs luna ~0.78 |
| DeepSeek T vẫn dưới Gemma-3 ORIG | T ~0.59 vs 0.64 |

**Lấy số / làm gì (để có “phân tích lỗi” kiểu mẫu)**
1. Bias & slope: frontier có “bơm” điểm cao hơn người không?  
2. Lỗi theo điều kiện câu (Mục 2): thua ở `global` / `name` / …?  
3. 2–3 case: cùng `sample_id`, frontier lệch nhiều mà Gemma-3 gần human — trích lý do từ output nếu cần.  
4. Thinking có cứu không (`T − ORIG`)?  
5. Thông điệp: **SOTA coding/reasoning ≠ giống crowdsource Likert 1–7.**

**Đưa lên slide**
- 1 bảng cặp nghịch lý + Δr.  
- 1–2 case câu.  
- 3 bullet “vì sao” gắn số (calibration / điều kiện / case) — narrative training chỉ là giả thuyết phụ.

**Câu kết luận mẫu**
> Trên mem_enc, quy mô/frontier không đảm bảo likeness: DeepSeek/Gemma-4 thua Gemma-3-12B chủ yếu vì … (bias/điều kiện/case …), không vì “kém thông minh hơn”.

- [x] Bảng nghịch lý có số  
- [x] Calibration + breakdown điều kiện cho cặp chính  
- [x] ≥2 case câu  
- [x] Đoạn kết luận slide sẵn  

---

## Mục 6 — Trọng điểm GPT-4 paper

**Câu hỏi slide:** Vì sao GPT-4 (paper) vẫn rất mạnh so với nhiều model mới? (Cùng tinh thần Mục 5; case riêng.)

**Lấy số từ đâu**
- `gpt4_mean` vs `human_mean` trên 50 câu → r, MAE, bias.  
- So với luna / sol / kimi (ORIG).  
- Cấm nhầm với `gpt-4.1-mini`.

**Đưa lên slide**
- 1 hàng “gpt-4 (paper)” trong bảng ORIG.  
- Bias/MAE so luna–sol.  
- 1 câu: narrative “chat-rating era vs coding/agent” **sau** khi chỉ ra số (bias nhỏ, MAE tốt, v.v.) — ghi là giả thuyết.

**Câu kết luận mẫu**
> GPT-4 paper đạt r≈… / MAE≈…; luna có thể cao hơn Pearson nhưng bias lớn hơn (…). Giả thuyết: ….

- [x] Neo GPT-4 paper vào bảng  
- [x] So luna/sol bằng số  
- [x] Section trọng điểm ngắn + pointer Mục 5  

---

## Mục 7 — Chi phí: AI có rẻ hơn người không?

**Câu hỏi slide:** Ngoài nhanh hơn, $/câu (và ước $/giờ) có rẻ hơn ước lượng người không? Ai Pareto?

**Lấy số từ đâu**
- `configs/pricing.yaml` (cập nhật giá OpenRouter/… khi làm mục này).  
- Usage trong scores → $/câu; vs human ≈ `$0.08 × ~40` annotators/câu (ước lượng crowdsource — nói rõ).  
- Latency nếu có → ước $/giờ.

**Đưa lên slide**
- Bảng ORIG/T: r | $/câu | lần rẻ hơn human.  
- 1 Pareto (r vs $).

**Câu kết luận mẫu**
> Mọi run ORIG/T rẻ hơn ước lượng người ~…×; … rẻ nhất; … Pareto tốt (r cao, $ vừa).

- [ ] Giá cập nhật + bảng cost  
- [ ] Pareto  
- [ ] 1 câu trả lời “có rẻ hơn không?”  

---

## Map sang outline slide 15 phút (học mẫu)

| Phút | Nội dung | Nguồn kế hoạch |
|---:|---|---|
| 0–6 | Bài toán pretest, paper, setup nhóm (data, prompt, MODE, ai chạy model) | Intro (đã có trong docs) |
| 6–9 | **Kết quả:** bảng tổng + theo điều kiện câu | Mục 1–2 |
| 9–12 | **Thảo luận / phân tích lỗi:** disagreement, schema, frontier vs Gemma-3, GPT-4 | Mục 3–6 |
| 12–13 | Chi phí vs người (nếu còn slot) | Mục 7 |
| 13–14 | Demo cache 1–2 câu | `results/` |
| 14–15 | Kết luận + hạn chế + Q&A | — |

Thứ tự làm phân tích: **1 → 2 → 3 → 4 → 5 → 6 → 7**.  
Mỗi lần xong một mục: đánh dấu checkbox trong mục đó; chỉ khi đủ 1–6 mới khóa slide kết quả/thảo luận.
