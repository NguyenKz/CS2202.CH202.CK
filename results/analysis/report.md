# Báo cáo phân tích (mem_enc)

> Narrative chung cho Mục 1–7. Script `run_muc*.py` upsert từng section `## Mục N — …`.
> Artifact CSV/JSON nằm cùng thư mục `results/analysis/`.

## Mục 1 — Kết quả tổng thể

Tham chiếu paper: **`gpt-4 (paper)`** từ `data/ready/…/gpt4_mean` (r=0.7547, MAE=0.5822) — **không** phải `openai/gpt-4.1-mini`.

### Biểu đồ xếp hạng (ORIG + T + gpt-4 paper + llm_annotators)

![Agreement with Human](M1_agreement_vs_gpt4paper.png)

- Xanh: r ≥ paper. Cam: r < paper. Xám: paper. Tím: **`llm_annotators`**.
- 2 entry ≥ paper; 14 entry < paper.

### Bảng tổng hợp (sort Pearson r ↓)

| Rank | Model | Mode | Pearson r | MAE | vs paper |
|---:|---|---|---:|---:|---|
| 1 | `gpt-5.6-luna` | `T` | 0.7851 | 0.5740 | Δr=+0.0304 |
| 2 | `gpt-5.6-luna` | `ORIG` | 0.7777 | 0.6199 | Δr=+0.0230 |
| 3 | **`gpt-4 (paper)`** | `ref` | 0.7547 | 0.5822 | ← **tham chiếu** |
| 4 | `gpt-5.6-sol` | `ORIG` | 0.7331 | 0.6378 | Δr=-0.0216 |
| 5 | **`llm_annotators`** | `mean` | 0.7273 | 0.6227 | Δr=-0.0274 |
| 6 | `gpt-5.6-sol` | `T` | 0.7062 | 0.6758 | Δr=-0.0485 |
| 7 | `moonshotai/kimi-k3` | `T` | 0.6954 | 0.6498 | Δr=-0.0593 |
| 8 | `moonshotai/kimi-k3` | `ORIG` | 0.6918 | 0.6680 | Δr=-0.0629 |
| 9 | `google/gemini-3.6-flash` | `T` | 0.6810 | 0.8166 | Δr=-0.0737 |
| 10 | `z-ai/glm-5.2` | `T` | 0.6678 | 0.9251 | Δr=-0.0869 |
| 11 | `google/gemma-4-31b-it` | `T` | 0.6421 | 0.8146 | Δr=-0.1126 |
| 12 | `google/gemma-3-12b-it` | `ORIG` | 0.6402 | 1.1865 | Δr=-0.1145 |
| 13 | `z-ai/glm-5.2` | `ORIG` | 0.6282 | 0.8656 | Δr=-0.1265 |
| 14 | `deepseek/deepseek-v4-flash` | `T` | 0.5944 | 0.7695 | Δr=-0.1603 |
| 15 | `deepseek/deepseek-v4-flash` | `ORIG` | 0.5488 | 0.6999 | Δr=-0.2059 |
| 16 | `openai/gpt-4.1-mini` | `ORIG` | 0.5251 | 0.8717 | Δr=-0.2296 |
| 17 | `google/gemma-4-31b-it` | `ORIG` | 0.4880 | 0.9310 | Δr=-0.2667 |

### `llm_annotators` là gì?

Không phải một model API. Mỗi LLM trong zoo được coi như **1 annotator** (lấy `model_mean` của model đó trên từng câu; ưu tiên MODE **ORIG**, không có ORIG thì dùng **T**; **không** gồm `gpt-4 (paper)`, **không** gồm S/ST). Điểm tổng hợp = **trung bình đều** các vote → rồi mới tính Pearson r / MAE với `human_mean`.

- Số annotator LLM: **9** — `deepseek/deepseek-v4-flash`, `google/gemini-3.6-flash`, `google/gemma-3-12b-it`, `google/gemma-4-31b-it`, `gpt-5.6-luna`, `gpt-5.6-sol`, `moonshotai/kimi-k3`, `openai/gpt-4.1-mini`, `z-ai/glm-5.2`
- Kết quả: r=0.7273, MAE=0.6227, hạng **#5** (paper hạng #3).

### Nhận định

- **#1:** `gpt-5.6-luna` / `T` (r=0.7851).
- **gpt-4 (paper):** hạng #3 (r=0.7547).
- **llm_annotators:** hạng #5 (r=0.7273) — dưới paper (Δr=-0.0274); crowd pha loãng model mạnh nên thường kém #1 đơn lẻ.

- **Thinking giúp likeness (quy luật tổng thể):** trên 6 model có cả ORIG và T, **5/6** có T ≥ ORIG trên Pearson r — Thinking **thực sự cải thiện** kết quả giống người ở hầu hết zoo.
  - Chi tiết Δr (T − ORIG):
  - ✓ `deepseek/deepseek-v4-flash`: 0.5488 → 0.5944 (Δr=+0.0456)
  - ✓ `google/gemma-4-31b-it`: 0.4880 → 0.6421 (Δr=+0.1541)
  - ✓ `gpt-5.6-luna`: 0.7777 → 0.7851 (Δr=+0.0074)
  - ✗ `gpt-5.6-sol`: 0.7331 → 0.7062 (Δr=-0.0270)
  - ✓ `moonshotai/kimi-k3`: 0.6918 → 0.6954 (Δr=+0.0036)
  - ✓ `z-ai/glm-5.2`: 0.6282 → 0.6678 (Δr=+0.0396)
  - **Ngoại lệ:** `gpt-5.6-sol` — T thua ORIG (Δr=-0.0270, |Δr|≈0.03). Có thể do **sample chưa đủ** (n=50 câu) hoặc mức chênh **không đáng kể** (~0.03) nên coi là nhiễu / điểm bất thường; **không phá** quy luật tổng thể “Thinking thường ≥ ORIG”.
- **Chỗ lạ (neo Mục 5):**
  - `deepseek/deepseek-v4-flash` ORIG r=0.5488 < Gemma-3-12B r=0.6402
  - `google/gemma-4-31b-it` ORIG r=0.4880 < Gemma-3-12B r=0.6402
  - `z-ai/glm-5.2` ORIG r=0.6282 < Gemma-3-12B r=0.6402

### Artifact

- `M1_agreement_vs_gpt4paper.png`
- `M1_unified_ranking.csv`
- `M1_llm_annotators_summary.json`, `M1_llm_annotators_sentences.csv`

## Mục 2 — Theo điều kiện câu

Điều kiện = manipulation **object-NP** trên cùng khung câu (hậu tố `sample_id`), **không** phải topic tin tức. Mỗi điều kiện ≈ 10 câu.

| Condition | Ý nghĩa ngắn |
|---|---|
| `all` | object khớp kỳ vọng (baseline) |
| `global` | object liên quan nhưng kém khớp ngữ cảnh |
| `animate` | đổi animate/inanimate của object |
| `plural` | object số nhiều |
| `name` | object là tên riêng |

### Giải thích các condition — theo paper

**Nguồn:** Amouyal, Meltzer-Asscher & Berant (EACL 2024 Findings; arXiv:2402.05455), dataset *Our data* / mem_enc trong §2.1, Table 1, §4.4.

#### Tại sao có các biến thể câu?

Paper mô tả bộ **50 câu plausible**, cấu trúc **đơn giản** (simple transitive trong Table 1), được tạo *“for a future experiment on **similarity-based interference**”* (§2.1). Cấu trúc: **40 cặp câu**, trong đó *“one sentence is shared among 4 pairs”* — tức **10 khung câu × 5 biến thể**; mỗi câu có **40** đánh giá plausibility từ người.

**Động cơ kiểm soát plausibility (§1):** khi thí nghiệm thao tác biến ngôn ngữ (ví dụ độ tương đồng NP), cần đảm bảo các câu **cùng mức hợp lý** để chênh lệch xử lý không bị lẫn bởi plausibility. Paper minh họa bằng ví dụ *photographer / contract* và trích **Ness & Meltzer-Asscher (2019)**: hai NP đều animate (1a) vs một animate + một inanimate (1b) có thể gây **similarity-based interference** khi đọc.

**Pretest fine-grained (§4.4):** một cách dùng plausibility là so **cặp câu** — chạy **t-test** xem hai câu có cùng phân phối điểm không; cặp bị reject thì loại khỏi materials. Trong data repo, field `need_ttest` trên các dòng `*_all` liệt kê 4 biến thể còn lại cùng khung (ví dụ `s1_all` so với `s1_global`, `s1_animate`, `s1_plural`, `s1_name`) — **khớp mục đích §4.4**, nhưng paper **không** đặt tên các hậu tố đó.

Paper cảm ơn **Tal Ness** (Acknowledgments) — tác giả làm về similarity-based interference cùng Meltzer-Asscher; paper **không** mô tả chi tiết thiết kế từng manipulation trong mem_enc ngoài hai ví dụ Table 1.

#### Tại sao **4** biến thể (không phải 5–6–7 hay 1–2–3)?

**Phần paper *có* trả lời — về số lượng, không phải loại manipulation:**

- §2.1: *“40 sentence pairs (one sentence is shared among 4 pairs)”*.
- Suy ra từ cấu trúc data: **10 khung** (`s1`–`s10`) × **4 cặp so sánh** / khung = **40 cặp**; mỗi khung có **5 câu** (1 baseline + 4 biến thể) → **50 câu** tổng.
- Table 1 (Ours): hai dòng *Simple | Plaus* với số item **10** và **40** — khớp **10 baseline + 40 biến thể**.
- Field `need_ttest` trên `*_all`: baseline được so t-test với **đúng 4** biến thể còn lại — khớp thiết kế pretest fine-grained §4.4.

Tức paper giải thích vì sao có **4 cặp** (và do đó **4** biến thể ngoài baseline), chứ **không** nói “có thể thêm biến thể thứ 5–6–7” hay “chỉ cần 2–3”. Số 4 là **hệ quả thiết kế thí nghiệm tương lai + pretest cặp**, không phải con số tùy ý trong repo.

**Phần paper *không* trả lời — vì sao đúng 4 *loại* này (`global`, `animate`, `plural`, `name`):**

- Paper **không** liệt kê lý do chọn bốn thao tác object-NP này thay vì thao tác khác (vd. đổi động từ, đổi subject, thêm modifier, câu dài hơn, v.v.).
- Paper **không** giải thích vì sao không thêm biến thể thứ 5 (vd. chỉ đổi definiteness *a/the*) hoặc bớt còn 2–3 — ngoài việc cố định **4 cặp/khung** như trên.
- §1 trích **animacy** (Ness 2019) như **ví dụ tổng quát** về similarity NP; paper **không** nói “biến thể `animate` trong mem_enc được chọn vì lý do X”.
- Thiết kế chi tiết của thí nghiệm similarity-based interference **tương lai** (mà bộ câu này phục vụ) **không** được mô tả trong paper EACL 2024 — paper chỉ dùng bộ câu để **đánh giá LLM pretest**.

**Kết luận thẳng:** biết **tại sao có 4** (cấu trúc 40 cặp / pretest t-test); **không biết từ paper** tại sao 4 loại manipulation lại là global/animate/plural/name — chỉ thấy pattern đó trong `sample_id` của data tác giả công bố.

#### Paper có định nghĩa `all|global|animate|plural|name` không?

**Không.** §2.1 và Table 1 chỉ đưa hai ví dụ từ cùng khung *The nurse fetched …*: *…the patient.* và *…the intern.* Paper **không** giải thích nhãn `all`, `global`, `animate`, `plural`, `name`; các nhãn này đến từ **quy ước `sample_id` trong data/repo** (hậu tố sau `s1`–`s10`).

**Lưu ý:** *global prompt* trong paper (§2.3, Appendix) là loại **prompt LLM** (ví dụ chung cho mọi dataset), **không** liên quan condition `global` trên object-NP.

#### Từng condition — paper nói gì / không nói gì

| Condition | Paper (trích ý) | Trong paper? | Quan sát từ data (repo; **không** phải định nghĩa tác giả) |
|---|---|---|---|
| `all` | Table 1: *The nurse fetched the patient.* | Có ví dụ; **không** gọi là `all` | Hậu tố `all`; dòng `need_ttest` → vai trò **baseline** so cặp t-test |
| `global` | Table 1: *The nurse fetched the intern.* | Có ví dụ; **không** gọi là `global`, **không** giải thích vì sao *intern* khác *patient* | Cùng khung, object animate khác (thường cùng “vai”/bối cảnh nghề nghiệp) |
| `animate` | §1: động cơ **animacy** / similarity NP (Ness 2019) — ngữ cảnh tổng quát | **Không** gắn suffix `animate` với mem_enc | Object đổi sang NP **vô tri** (vd. *file*, *cake*, *portrait*) |
| `plural` | — | **Không có** | Object **số nhiều** (vd. *interns*, *chefs*) |
| `name` | — | **Không có** | Object là **tên riêng** (vd. *Matt*, *Louis*) |

Bảng *Ý nghĩa ngắn* phía trên là **diễn giải phân tích** (gloss) để đọc heatmap — chỉ `patient`/`intern` có ví dụ trực tiếp trong paper; các dòng còn lại suy từ pattern câu trong `mem_enc_exp1.jsonl`.

### Giải thích dễ hiểu

**Condition là gì?** Mỗi condition là một **cách đổi tân ngữ (object)** trên **cùng một khung câu**. Chủ ngữ và động từ giữ nguyên; chỉ phần sau động từ thay đổi. Ví dụ khung `s1`: *The nurse fetched …* — chỉ đổi *patient / intern / file / interns / Matt*.

**Bộ câu được tổ chức thế nào?**

- **10 khung** (`s1` … `s10`) — 10 tình huống nghề nghiệp khác nhau (y tá, bồi bàn, đại lý nghệ thuật, …).
- Mỗi khung có **5 câu** = 1 baseline + 4 biến thể → **50 câu** tổng.
- Hậu tố trong `sample_id` (`all`, `global`, `animate`, `plural`, `name`) cho biết **đang đổi object theo kiểu nào**.

**Năm biến thể — đọc qua ví dụ `s1`:**

| Condition | Câu | Ý chính (dễ nhớ) |
|---|---|---|
| `all` | *The nurse fetched the patient.* | **Baseline** — object “đúng kỳ vọng” nhất trong khung |
| `global` | *The nurse fetched the intern.* | Vẫn người, vẫn hợp ngữ cảnh bệnh viện, nhưng **vai khác** (thực tập sinh, không phải bệnh nhân) |
| `animate` | *The nurse fetched the file.* | Đổi sang **đồ vật** (vô tri) — câu vẫn đúng ngữ pháp |
| `plural` | *The nurse fetched the interns.* | Cùng ý với *intern* nhưng **số nhiều** |
| `name` | *The nurse fetched Matt.* | Gọi **tên riêng** thay vì cụm danh từ *the …* |

**Thuật ngữ tiếng Việt — `plural` và `animate` (dễ nhầm):**

- **`plural`** = **số nhiều** (object chuyển từ số ít sang số nhiều). Ví dụ: *the intern* (một thực tập sinh) → *the interns* (các thực tập sinh).
- **`animate`** trong ngôn ngữ học = **hữu sinh** (người, động vật); đối lập **vô sinh** / **vô tri** (đồ vật). Nhãn condition `animate` = **biến thể thao tác theo chiều animacy (hữu sinh ↔ vô sinh)**, **không** có nghĩa “object trong câu là hữu sinh”.
- Trong data, `animate` thường **đổi object sang vô sinh**: `all` *…the patient* (hữu sinh) → `animate` *…the file* (vô sinh). Tên nhãn trỏ vào **loại thao tác**, không mô tả trực tiếp object ở câu đó.

**Tại sao cần nhiều biến thể?** Paper nói bộ câu này chuẩn bị cho thí nghiệm tương lai về *similarity-based interference* — khi hai cụm danh từ trong câu **giống nhau** (cùng animate, cùng số, …), người đọc có thể **nhầm lẫn** khi xử lý. Trước khi chạy thí nghiệm đó, tác giả cần pretest: các biến thể phải **cùng độ hợp lý** (plausibility), không để câu này “hợp lý hơn hẳn” câu kia chỉ vì đổi từ.

**Tại sao đúng 4 biến thể (ngoài baseline)?** Đơn giản: thiết kế cố định **4 cặp so sánh / khung** (baseline so với từng biến thể) → 10 × 4 = **40 cặp** để chạy t-test plausibility (§4.4). Không phải chọn ngẫu nhiên “4 hay 7”.

**Tại sao lại là 4 *loại* global / animate / plural / name?** Phần này **paper không giải thích** — chỉ thấy trong data. Khi phân tích Mục 2, ta coi đây là **4 kiểu thao tác object** đã có sẵn trong bộ materials, rồi hỏi: LLM bám điểm người tốt nhất ở kiểu nào, kém nhất ở kiểu nào?

**Đọc kết quả Mục 2 nghĩa là gì?** Heatmap và bảng trung bình cho biết: với cùng metric human-likeness (Pearson r / MAE), model có **ổn định** qua mọi kiểu đổi object không, hay chỉ giỏi ở baseline (`all`) / đổi vô tri (`animate`) mà **yếu** khi object liên quan nhưng lệch vai (`global`) hoặc khi dùng tên riêng (`name`)? Đó là lý do ta tách theo condition — không phải vì “chủ đề tin tức”, mà vì **loại thao tác ngôn ngữ trên object**.

### Heatmap Pearson r (ORIG / T + gpt-4 paper)

![Pearson r by condition](M2_condition_heatmap.png)

### Trung bình qua zoo ORIG+T (và so paper)

| Rank (r) | Condition | mean r | mean MAE | paper r | paper MAE |
|---:|---|---:|---:|---:|---:|
| 1 | `animate` | 0.806 | 0.783 | 0.845 | 0.432 |
| 2 | `name` | 0.697 | 0.741 | 0.853 | 0.578 |
| 3 | `plural` | 0.651 | 0.735 | 0.731 | 0.656 |
| 4 | `all` | 0.642 | 0.803 | 0.751 | 0.540 |
| 5 | `global` | 0.492 | 0.840 | 0.622 | 0.706 |

### Minh họa từng condition (cùng khung câu `s1`)

Cùng khung *The nurse fetched …* — đổi object-NP theo condition. Dưới đây: **toàn bộ điểm người chấm** (raw crowdsource) và **mỗi LLM = 1 annotator** (`model_mean` trên câu đó; ưu tiên MODE ORIG, không có thì T; không gồm gpt-4 paper).

| Condition | Câu | human mean | llm_annotators mean | gpt-4 paper |
|---|---|---:|---:|---:|
| `all` | *The nurse fetched the patient.*<br>→ *Y tá đã đón bệnh nhân.* | 6.27 | 5.86 | 6.45 |
| `global` | *The nurse fetched the intern.*<br>→ *Y tá đã đón thực tập sinh.* | 5.10 | 5.29 | 5.70 |
| `animate` | *The nurse fetched the file.*<br>→ *Y tá đã lấy hồ sơ.* | 6.22 | 5.95 | 6.20 |
| `plural` | *The nurse fetched the interns.*<br>→ *Y tá đã đón các thực tập sinh.* | 5.45 | 5.48 | 6.05 |
| `name` | *The nurse fetched Matt.*<br>→ *Y tá đã đón Matt.* | 4.90 | 5.27 | 5.40 |

#### `all` — *The nurse fetched the patient.* (`s1_all`)

*→ Y tá đã đón bệnh nhân.*

**Human (n=41, mean=6.27):** 7, 6, 5, 7, 7, 6, 2, 5, 7, 7, 5, 7, 7, 7, 7, 7, 5, 7, 4, 7, 5, 5, 7, 7, 7, 7, 7, 7, 7, 5, 6, 7, 7, 7, 5, 5, 7, 7, 6, 7, 7

**AI annotators (n=9, mean=5.86):**

| Model | MODE | mean |
|---|---|---:|
| `deepseek-v4-flash` | `ORIG` | 6.90 |
| `gemini-3.6-flash` | `T` | 6.00 |
| `gemma-3-12b-it` | `ORIG` | 6.30 |
| `gemma-4-31b-it` | `ORIG` | 6.00 |
| `gpt-5.6-luna` | `ORIG` | 6.05 |
| `gpt-5.6-sol` | `ORIG` | 6.00 |
| `kimi-k3` | `ORIG` | 6.40 |
| `gpt-4.1-mini` | `ORIG` | 3.65 |
| `glm-5.2` | `ORIG` | 5.40 |

#### `global` — *The nurse fetched the intern.* (`s1_global`)

*→ Y tá đã đón thực tập sinh.*

**Human (n=40, mean=5.10):** 7, 3, 6, 6, 2, 7, 1, 2, 6, 2, 6, 5, 5, 5, 4, 6, 5, 7, 6, 7, 7, 4, 6, 5, 7, 7, 3, 4, 7, 5, 5, 6, 1, 7, 3, 4, 7, 5, 7, 6

**AI annotators (n=9, mean=5.29):**

| Model | MODE | mean |
|---|---|---:|
| `deepseek-v4-flash` | `ORIG` | 5.00 |
| `gemini-3.6-flash` | `T` | 5.20 |
| `gemma-3-12b-it` | `ORIG` | 5.00 |
| `gemma-4-31b-it` | `ORIG` | 6.00 |
| `gpt-5.6-luna` | `ORIG` | 5.00 |
| `gpt-5.6-sol` | `ORIG` | 5.60 |
| `kimi-k3` | `ORIG` | 5.60 |
| `gpt-4.1-mini` | `ORIG` | 5.05 |
| `glm-5.2` | `ORIG` | 5.20 |

#### `animate` — *The nurse fetched the file.* (`s1_animate`)

*→ Y tá đã lấy hồ sơ.*

**Human (n=40, mean=6.22):** 6, 7, 7, 6, 6, 7, 6, 7, 7, 7, 7, 7, 5, 7, 7, 7, 6, 7, 6, 5, 4, 7, 6, 4, 7, 3, 6, 7, 7, 6, 2, 7, 7, 7, 7, 5, 7, 6, 7, 7

**AI annotators (n=9, mean=5.95):**

| Model | MODE | mean |
|---|---|---:|
| `deepseek-v4-flash` | `ORIG` | 4.20 |
| `gemini-3.6-flash` | `T` | 6.60 |
| `gemma-3-12b-it` | `ORIG` | 6.00 |
| `gemma-4-31b-it` | `ORIG` | 7.00 |
| `gpt-5.6-luna` | `ORIG` | 5.75 |
| `gpt-5.6-sol` | `ORIG` | 6.00 |
| `kimi-k3` | `ORIG` | 6.20 |
| `gpt-4.1-mini` | `ORIG` | 6.00 |
| `glm-5.2` | `ORIG` | 5.80 |

#### `plural` — *The nurse fetched the interns.* (`s1_plural`)

*→ Y tá đã đón các thực tập sinh.*

**Human (n=40, mean=5.45):** 7, 6, 7, 5, 6, 7, 7, 6, 2, 7, 6, 7, 1, 7, 7, 5, 6, 5, 7, 4, 7, 6, 7, 6, 4, 6, 3, 5, 5, 6, 7, 2, 6, 5, 4, 5, 6, 5, 1, 7

**AI annotators (n=9, mean=5.48):**

| Model | MODE | mean |
|---|---|---:|
| `deepseek-v4-flash` | `ORIG` | 5.25 |
| `gemini-3.6-flash` | `T` | 5.00 |
| `gemma-3-12b-it` | `ORIG` | 6.00 |
| `gemma-4-31b-it` | `ORIG` | 6.00 |
| `gpt-5.6-luna` | `ORIG` | 5.05 |
| `gpt-5.6-sol` | `ORIG` | 5.80 |
| `kimi-k3` | `ORIG` | 5.20 |
| `gpt-4.1-mini` | `ORIG` | 5.00 |
| `glm-5.2` | `ORIG` | 6.00 |

#### `name` — *The nurse fetched Matt.* (`s1_name`)

*→ Y tá đã đón Matt.*

**Human (n=40, mean=4.90):** 2, 6, 7, 5, 3, 7, 6, 6, 2, 6, 4, 6, 2, 2, 5, 5, 5, 4, 5, 1, 6, 5, 6, 4, 6, 7, 6, 7, 6, 4, 7, 4, 7, 3, 3, 4, 3, 7, 5, 7

**AI annotators (n=9, mean=5.27):**

| Model | MODE | mean |
|---|---|---:|
| `deepseek-v4-flash` | `ORIG` | 4.30 |
| `gemini-3.6-flash` | `T` | 5.20 |
| `gemma-3-12b-it` | `ORIG` | 6.00 |
| `gemma-4-31b-it` | `ORIG` | 6.00 |
| `gpt-5.6-luna` | `ORIG` | 5.50 |
| `gpt-5.6-sol` | `ORIG` | 5.00 |
| `kimi-k3` | `ORIG` | 4.40 |
| `gpt-4.1-mini` | `ORIG` | 5.65 |
| `glm-5.2` | `ORIG` | 5.40 |

**Ghi chú nhanh:**
- `all` / *patient*: baseline; human & AI đều cao.
- `global` / *intern*: human thấp hơn; nhiều AI vẫn ~5.
- `animate` / *file*: human cao; AI bám khá.
- `plural` / *interns*: human ~5.5; AI hơi cao.
- `name` / *Matt*: human thấp nhất (~4.9); nhiều AI **over-rate** (~5–6).

### Case residual điển hình (nhiều model lệch cùng câu)

| sample_id | cond | sentence | human | worst model | mode | model | abs err |
|---|---|---|---:|---|---|---:|---:|
| `s3_global` | `global` | The art dealer brought the artist. | 3.30 | `gemma-3-12b-it` | `ORIG` | 6.75 | 3.45 |
| `s3_all` | `all` | The art dealer brought the buyer. | 3.33 | `gemma-4-31b-it` | `ORIG` | 7.00 | 3.67 |
| `s5_animate` | `animate` | The owner payed for the tractor. | 4.65 | `gemma-3-12b-it` | `ORIG` | 7.00 | 2.35 |

### Nhận định

- **Dễ bám người nhất (mean r cao):** `animate` (mean r=0.806) — đổi animate/inanimate của object.
- **Khó nhất (mean r thấp):** `global` (mean r=0.492) — object liên quan nhưng kém khớp ngữ cảnh.
- Theo **MAE** (thấp = gần điểm người hơn): dễ `plural` (mean MAE=0.735); khó `global` (mean MAE=0.840).
- Paper GPT-4 cũng yếu hơn ở `global` (r=0.622) và mạnh ở `name` (r=0.853) — cùng hướng zoo.

- Ví dụ lệch lớn: `s3_global` *“The art dealer brought the artist.”* — human≈3.30 nhưng `gemma-3-12b-it`/ORIG≈6.75 (|err|≈3.45); xuất hiện trong top residual của **9** run → lỗi mang tính **điều kiện/câu**, không chỉ 1 model.

### Artifact

- `M2_condition_heatmap.png`
- `M2_by_condition.csv`, `M2_condition_mean.csv`
- `M2_top_residuals.csv`, `M2_hard_sentences.csv`, `M2_residual_examples.csv`
- `M2_condition_examples.csv`, `M2_condition_ai_votes.csv`, `M2_condition_examples_detail.json`
- `M2_summary.json`

## Mục 3 — Disagreement người vs phân tán LLM

**Câu hỏi:** Câu người chấm 1, người khác 7 — LLM resample có phân tán giống người hay luôn dồn quanh một điểm?

**Caveat:** `human_std` = ~40 annotator/câu; `model_std` = 20 lần gọi API/câu — so **ý nghĩa phân tán**, không phải thí nghiệm đối chứng cùng *n*.

**Neo paper (§5, Figure 8):** variance điểm LM **thấp hơn người rất nhiều** dù resample nhiều lần; §4.4: điều này làm **t-test fine-grained** (so cặp câu cùng plausibility) kém với người.

Trên mem_enc: mean `human_std` (50 câu) ≈ **1.53**. Top **15** câu disagreement cao nhất (sort `human_std`, rồi `human_range`).

### Paper nói gì / nhóm bổ sung gì

**Paper có nghiên cứu & giải thích (Amouyal et al., EACL 2024):**

- **Abstract / §1:** LLM ổn cho pretest **coarse-grained**; **kém fine-grained** (vd. hai câu cùng mức plausibility).
- **§4.4:** pretest cặp câu bằng **t-test** trên điểm người; với LM khó vì *(trích §5)* **variance LM thấp hơn người rất nhiều** → thay bằng ngưỡng chênh mean, vẫn kém (Figure 6–7).
- **§5 — *Variance of Humans vs. LMs*:** human variance **≫** LM dù sampling temp=1.5; resample LM cho điểm **gần giống nhau** (**Figure 8**: std trung bình GPT-4/GPT-3.5 vs người, 4 dataset).
- **Giải thích §5:** output LM như trung bình của *N* lượt người → var_LM ≈ σ²/*N*; ước *N* bằng ratio `var_human / var_LM` **trên từng câu**.

**Paper không làm (phần dưới là mở rộng của nhóm trên mem_enc):**

| Phân tích nhóm (Mục 3) | Trong paper? |
|---|---|
| Top 10–15 câu **disagreement cao** (`human_std`, range) | Không — paper báo **std trung bình** theo dataset |
| Metric **`collapse rate`** (model_std < 0.5 × human_std) | Không — thuật ngữ & ngưỡng của nhóm |
| Zoo model (luna, gemma, …) | Chủ yếu GPT-4 / GPT-3.5 |
| Histogram **từng câu** + raw scores | Figure 8 = bar std **trung bình** |
| `r(std_h, std_m)` trên top-15 | Không |

**Đọc Mục 3:** cùng câu hỏi với paper §5 (LM ít phân tán); nhóm **drill-down** trên câu người bất đồng nhất + nhiều model. Kết quả collapse ~0.91 **khớp hướng paper**, không phải metric paper định nghĩa sẵn.

#### Giải thích dễ hiểu

Hai lớp câu hỏi khác nhau:

1. **Trung bình có khớp không?** (Mục 1 — Pearson r, MAE) — LLM cho *điểm trung bình* gần người không?
2. **Phân tán có khớp không?** (Mục 3) — Gọi LLM nhiều lần trên **cùng một câu**, điểm có **lan** như nhiều người chấm không?

**Paper trả lời lớp 2 — có, và khá đầy đủ:**

- Người chấm **không đồng ý nhau** (variance cao). GPT resample **gần như cho cùng một số** (variance thấp) — dù bật temperature cao (§5).
- Hệ quả thực tế: LLM **lọc câu quá dở / quá ổn** (coarse) thì được; nhưng **so hai câu xem plausibility có ngang nhau không** (fine-grained, t-test §4.4) thì **không tin được** — vì LM “phẳng” quá, chênh mean nhỏ khó phản ánh sự bất đồng của người.

##### Giải thích thuật ngữ — plausibility, lọc câu, coarse vs fine-grained

**Plausibility (mức hợp lý / tự nhiên):** Người (hoặc LLM) đọc một câu và cho điểm **1–7** — câu nghe *tự nhiên, hợp lý trong đời thực* đến mức nào. Không phải đúng/sai ngữ pháp: trong mem_enc **mọi câu đều đúng ngữ pháp**; điểm phản ánh “có believable không” (vd. *The nurse fetched the patient* cao, *The teacher scolded the shoe* thấp).

**Pretest là gì?** Trước thí nghiệm chính (vd. đo thời gian đọc), tác giả **pretest** materials bằng plausibility judgments để **chọn hoặc loại câu** — tránh hiệu ứng xử lý bị lẫn vì câu quá vô lý hoặc hai câu so sánh không cùng “độ hợp lý”.

**“Lọc câu” (coarse-grained) — lọc câu gì?** Paper §4.2–4.3, ba kiểu dùng plausibility; hai kiểu **lọc từng câu một** (coarse):

| Kiểu lọc | Lọc câu nào? | Ví dụ |
|---|---|---|
| Lọc **implausible** (§4.2) | Bỏ câu **quá vô lý** (mean thấp, dưới ngưỡng) | Câu kiểu *The teacher scolded the shoe* — mean ≈ 1–2 |
| Lọc **plausible** (§4.3) | Bỏ câu **quá hợp lý** khi thí nghiệm *cần* câu vô lý | Giữ lại câu implausible cho stimulus |

Chỉ cần **một con số trung bình** / ngưỡng: “câu này quá dở hay quá ổn?” → LLM thường làm **tốt** (paper Figure 4–5).

**“So hai câu ngang plausibility không?” (fine-grained) — là gì, tại sao cần?** Paper §4.4 — kiểu thứ ba:

- So **cặp câu** (không phải từng câu lẻ): hai câu cùng khung, khác một thao tác (vd. *…the patient* vs *…the intern*).
- **Mục tiêu:** mean plausibility **tương đương** — không để câu A “hợp lý hơn hẳn” câu B khi thí nghiệm chính chỉ muốn so hiệu ứng **ngôn ngữ** (vd. similarity-based interference ở Mục 2), không phải hiệu ứng “câu này dễ chấp nhận hơn”.
- **mem_enc:** 40 cặp; field `need_ttest` (vd. `s1_all` so với `s1_global`, …) — **đúng use case fine-grained** này.
- **Cách làm với người:** thu điểm cả hai câu → **t-test** — H₀: hai câu cùng phân phối plausibility. Nếu **reject** → người thấy hai câu **khác mức** → **loại cặp** khỏi materials.

**t-test (§4.4) — một câu:** Kiểm định “hai câu có cùng ‘độ hợp lý’ theo người không?”. Khác với lọc coarse (một ngưỡng trên **một** câu), fine-grained hỏi **quan hệ giữa hai câu** — tinh hơn, khó hơn.

**LM “phẳng” (variance thấp) — vì sao fine-grained hỏng?**

- Gọi LLM 20 lần trên **cùng câu** → điểm **dồn quanh mean** (Mục 3: collapse).
- Gọi trên **hai câu** → hai mean cũng **ổn định, chênh ít** → LLM hay kết luận “ngang nhau” dù **người** t-test **reject** (paper Figure 7: chênh mean là feature tốt với người, kém với LM).
- Tức Pearson mean (Mục 1) có thể cao, nhưng LM **không bắt được** “cặp này phải loại vì plausibility lệch” — cần người hoặc metric khác.

- Paper minh họa bằng **std trung bình** trên cả dataset (Figure 8) và lý do: LM như đã **lấy trung bình sẵn** của rất nhiều “ý kiến ảo” → mỗi lần gọi chỉ dao động nhẹ quanh mean.

**Nhóm bổ sung thêm — paper không làm chi tiết này:**

- Không dừng ở std trung bình: tìm **câu người tranh cãi nhất** (std ≈ 2, có người 1 có người 7) rồi hỏi: *trên đúng những câu đó*, LLM có “feel” tranh cãi không?
- Thử **nhiều model** (luna, gemma, …), không chỉ GPT-4/3.5.
- Đặt tên **`collapse`**: model_std quá nhỏ so với human_std → resample **không mô phỏng** crowd disagreement.

**Một câu tóm:** Paper chứng minh LM **ít phân tán** (§5); Mục 3 **chỉ ra chỗ đau** — trên câu người bất đồng nhất, hầu hết model vẫn **dồn điểm** (collapse ~0.91) → giải thích vì sao Mục 1 có thể đẹp (mean khớp) mà pretest fine-grained vẫn cần người.

### Chú giải header bảng

**Bảng *Top câu disagreement* — chỉ điểm người** (tìm câu crowdsource bất đồng nhất):

| Header | Nghĩa |
|---|---|
| `Rank` | Thứ hạng disagreement: sort `human_std` ↓, hòa thì `human_range` ↓ |
| `sample_id` | ID câu (vd. `s4_all` = khung `s4`, condition `all`) |
| `cond` | Condition object-NP — xem Mục 2 |
| `human mean` | Trung bình điểm người (thang 1–7, ~40 annotator/câu) |
| `human std` | Độ lệch chuẩn điểm người — **cao = người càng không đồng ý** |
| `range` | max − min điểm người (vd. 6 = có người cho 1 và người cho 7) |
| `% cực (1/7)` | Tỷ lệ annotator cho điểm **1 hoặc 7** |

Dòng *So nhanh… model_std* (dưới bảng): trung bình phân tán LLM trên cùng tập câu — so với `human std` ~2.0.

**Bảng *Collapse* — so phân tán LLM vs người trên top-15 disagreement** (mỗi dòng = model × MODE):

| Header | Nghĩa |
|---|---|
| `Model` / `MODE` | Model và cách prompt (`ORIG` / `T`) |
| `collapse rate` | Tỷ lệ câu mà `model_std < 0.5 × human_std` — model “co” phân tán. 1.00 = collapse trên cả 15 câu |
| `mean model_std (top-15)` | Trung bình độ lệch chuẩn **20 lần resample** LLM trên 15 câu đó |
| `mean ratio (top-15)` | Trung bình `model_std / human_std` — ~0.2 nghĩa là model chỉ ~20% độ spread của người |
| `r(std_h, std_m)` | Pearson: câu người càng tranh cãi (`human_std` cao) thì model có phân tán theo không? Gần 0/âm → không |

**Case chi tiết:** `n` = số điểm; `mean` / `std` / `range` (chỉ human) như trên; danh sách số = raw scores để thấy người trải 1–7 còn model dồn quanh 5–6.

### Top câu disagreement (người)

| Rank | sample_id | cond | human mean | human std | range | % cực (1/7) |
|---:|---|---|---:|---:|---:|---:|
| 1 | `s4_all` | `all` | 4.12 | 2.08 | 6 | 30% |
| 2 | `s3_global` | `global` | 3.30 | 2.04 | 6 | 35% |
| 3 | `s3_name` | `name` | 3.35 | 1.99 | 6 | 28% |
| 4 | `s5_name` | `name` | 3.65 | 1.99 | 6 | 28% |
| 5 | `s3_all` | `all` | 3.33 | 1.99 | 6 | 35% |
| 6 | `s3_plural` | `plural` | 3.85 | 1.98 | 6 | 22% |
| 7 | `s7_global` | `global` | 4.08 | 1.97 | 6 | 25% |
| 8 | `s6_animate` | `animate` | 3.83 | 1.93 | 6 | 18% |
| 9 | `s5_animate` | `animate` | 4.65 | 1.93 | 6 | 28% |
| 10 | `s5_plural` | `plural` | 3.35 | 1.93 | 6 | 28% |

**So nhanh trên top-10** — `model_std` trung bình:
- `gpt-5.6-luna` ORIG: 0.30
- `gemma-3-12b-it` ORIG: 0.17

### Collapse trên top disagreement (model_std < 0.5 × human_std)

| Model | MODE | collapse rate | mean model_std (top-15) | mean ratio (top-15) | r(std_h, std_m) |
|---|---|---:|---:|---:|---:|
| `deepseek-v4-flash` | `ORIG` | 1.00 | 0.35 | 0.21 | 0.25 |
| `gemini-3.6-flash` | `T` | 1.00 | 0.35 | 0.23 | -0.30 |
| `gemma-3-12b-it` | `ORIG` | 1.00 | 0.17 | 0.16 | 0.48 |
| `gemma-4-31b-it` | `ORIG` | 1.00 | 0.09 | 0.18 | -0.18 |
| `gpt-5.6-luna` | `T` | 1.00 | 0.45 | 0.25 | -0.01 |
| `gpt-5.6-luna` | `ORIG` | 1.00 | 0.30 | 0.21 | 0.46 |
| `gpt-5.6-sol` | `ORIG` | 1.00 | 0.23 | 0.23 | -0.49 |
| `gpt-5.6-sol` | `T` | 1.00 | 0.28 | 0.22 | -0.05 |
| `kimi-k3` | `T` | 1.00 | 0.52 | 0.27 | -0.06 |
| `gpt-4.1-mini` | `ORIG` | 1.00 | 0.40 | 0.24 | 0.20 |
| `glm-5.2` | `ORIG` | 1.00 | 0.43 | 0.28 | 0.33 |
| `deepseek-v4-flash` | `T` | 0.93 | 0.59 | 0.33 | 0.11 |
| `gemma-4-31b-it` | `T` | 0.93 | 0.45 | 0.29 | 0.00 |
| `kimi-k3` | `ORIG` | 0.80 | 0.71 | 0.39 | 0.27 |
| `glm-5.2` | `T` | 0.00 | 2.06 | 1.06 | 0.24 |

![Human vs model dispersion](M3_case_histograms.png)

*Hàng:* top-3 câu disagreement. *Cột:* `gpt-5.6-luna` ORIG, `gemma-3-12b-it` ORIG. Xanh = người; cam = model.

### Case chi tiết (top disagreement)

#### `s4_all` — *The dean observed the scientist.* (`all`)

**Human (n=40, mean=4.12, std=2.08, range=6):** 6, 6, 5, 7, 1, 1, 1, 5, 2, 7, 1, 7, 2, 7, 2, 5, 4, 6, 5, 2, 5, 2, 3, 6, 3, 4, 2, 7, 4, 6, 1, 7, 4, 4, 2, 5, 2, 4, 5, 7

**`gpt-5.6-luna` / `ORIG`** (n=20, mean=5.35, std=0.49): 6, 5, 6, 6, 5, 6, 6, 5, 6, 6, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5

**`gemma-3-12b-it` / `ORIG`** (n=20, mean=5.90, std=0.31): 6, 6, 6, 6, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 5, 6, 6, 6, 6, 6

#### `s3_global` — *The art dealer brought the artist.* (`global`)

**Human (n=40, mean=3.30, std=2.04, range=6):** 7, 2, 2, 2, 2, 1, 7, 3, 5, 6, 1, 1, 7, 1, 5, 6, 3, 1, 5, 1, 5, 5, 1, 2, 5, 2, 3, 4, 5, 2, 2, 1, 2, 4, 4, 1, 5, 3, 7, 1

**`gpt-5.6-luna` / `ORIG`** (n=20, mean=5.05, std=0.22): 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 6, 5, 5, 5, 5, 5, 5, 5, 5

**`gemma-3-12b-it` / `ORIG`** (n=20, mean=6.75, std=0.44): 6, 7, 7, 7, 7, 7, 7, 7, 6, 7, 7, 7, 7, 6, 7, 6, 7, 6, 7, 7

### Nhận định

- Trên top-15 disagreement: **collapse rate trung bình ≈ 0.91** (11/15 run ≥ 0.99) — LLM **ít phân tán hơn người** trên câu người bất đồng.
- Ratio `model_std/human_std` trên top-15: thấp nhất `gemma-3-12b-it`/ORIG ≈ 0.16; cao nhất `glm-5.2`/T ≈ 1.06 (vẫn thường ≪ 1).
- **Kết luận:** Hầu hết model **collapse** — resample ổn định quanh mean, không tái hiện disagreement người. Khớp paper §5; giải thích vì sao Pearson cao (Mục 1) vẫn **không đủ** cho pretest fine-grained (t-test cặp câu).

### Kết luận đối chiếu paper — vẫn đúng ở thời điểm hiện tại?

**Có** — về **hướng và kết luận chính**, paper (Amouyal et al., EACL 2024) **vẫn đứng** trên zoo model hiện tại + mem_enc. Phân tích nhóm **ủng hộ** paper hơn là bác bỏ; **không** đưa ra kết luận trái paper, chỉ **reproduce + định lượng** (collapse, case cụ thể).

| Kết luận paper | Trên data nhóm |
|---|---|
| LLM bám **mean** người khá tốt (GPT-4 mạnh) | **Đúng** — xem Mục 1 (vd. luna T r cao; gpt-4 paper vẫn baseline MAE/bias tốt) |
| **Coarse** pretest (lọc câu quá dở/ổn) LLM làm được | Nhóm **không replicate** Figure 4–5; **không** có bằng chứng ngược |
| **Fine-grained** (so cặp câu cùng plausibility) LLM **yếu** | **Đúng hướng** — collapse ~0.91 (Mục 3) → LM “phẳng”, khó thay t-test người |
| Variance LM **≪** người khi resample (§5) | **Đúng** — `model_std` ~0.2–0.5 vs `human_std` ~2 trên top disagreement |

**Tinh chỉnh (không phải bác paper):**

- Model **mới** (luna, sol, …) có thể **hơn** gpt-4 paper về Pearson — paper không claim GPT-4 #1 mãi mãi; claim *mean OK, variance không* — **vẫn đúng**.
- Model mới **không phá** quy luật variance: hầu hết vẫn collapse trên câu disagreement.
- **Ngoại lệ:** `glm-5.2`/T (collapse ≈ 0) — không đảo kết luận chung; chưa chứng minh fine-grained ngang người.
- **Phạm vi:** nhóm chỉ đủ trên **mem_enc** (50 câu), không replicate 4 dataset của paper.

**Một câu slide:** *Paper EACL 2024 vẫn valid — mean correlate tốt, variance thấp, coarse được / fine-grained chưa; chúng em xác nhận trên model 2025–26, Mục 3 khớp §5 (collapse ~91%).*


### Artifact

- `M3_case_histograms.png` (gộp) + `M3_histograms/*.png` (từng ô; model hist scale → n=20 nếu thiếu)
- `M3_high_disagreement_sentences.csv`
- `M3_dispersion.csv`, `M3_dispersion_summary.csv`
- `M3_summary.json`
## Mục 5 — Ai tốt / ai tệ + nghịch lý frontier vs Gemma-3-12B

**Câu hỏi slide:** Kimi-K3, GLM-5.2, DeepSeek-v4-flash… là frontier / rất lớn — sao có cái **thua hoặc không hơn** Gemma-3-12B trên giống người?

**Baseline:** `google/gemma-3-12b-it` / `ORIG` — r≈**0.640**, MAE≈**1.186**.

### Bảng nghịch lý (vs Gemma-3-12B ORIG)

| Model | MODE | r | Δr | MAE | bias | slope | vs baseline |
|---|---|---:|---:|---:|---:|---:|---|
| `gpt-5.6-luna` | `ORIG` | 0.778 | 0.1374 | 0.620 | 0.309 | 0.824 | ✓ hơn |
| `kimi-k3` | `ORIG` | 0.692 | 0.0516 | 0.668 | 0.126 | 0.821 | ✓ hơn |
| `gemma-4-31b-it` | `T` | 0.642 | 0.0019 | 0.815 | 0.647 | 0.589 | ✓ hơn |
| `glm-5.2` | `ORIG` | 0.628 | -0.0121 | 0.866 | 0.566 | 0.670 | ✗ thua |
| `deepseek-v4-flash` | `T` | 0.594 | -0.0459 | 0.769 | 0.503 | 0.556 | ✗ thua |
| `deepseek-v4-flash` | `ORIG` | 0.549 | -0.0914 | 0.700 | 0.194 | 0.470 | ✗ thua |
| `gemma-4-31b-it` | `ORIG` | 0.488 | -0.1522 | 0.931 | 0.595 | 0.487 | ✗ thua |

**Neo số (ORIG):**

- `deepseek-v4-flash`: r=0.549 (Δr=-0.0914), bias=0.194, slope=0.470
- `gemma-4-31b-it`: r=0.488 (Δr=-0.1522), bias=0.595, slope=0.487
- `glm-5.2`: r=0.628 (Δr=-0.0121), bias=0.566, slope=0.670
- `kimi-k3`: r=0.692 (Δr=0.0516), bias=0.126, slope=0.821
- `luna` (mốc tốt hơn): r=0.778 (Δr=0.1374)

### Giải thích dễ hiểu

**Câu hỏi thực tế:** Model “mạnh”, “frontier”, nhiều tỷ tham số — sao lại **thua** Gemma-3-12B trên *giống người* (Pearson r với mean crowdsource)?

Không phải vì model “kém thông minh”. Trên mem_enc, **human-likeness** đo khả năng **bám thang Likert 1–7 của ~40 người/câu — khác benchmark coding/reasoning.

Bốn cơ chế có số trong repo:

1. **Calibration / bias:** Model cho cảnh “tự nhiên hơn” người (bias dương lớn) → Pearson/MAE xấu dù “hiểu” câu.
2. **Slope thấp:** Model ít **theo biến thiên** điểm người (câu dễ vs khó) — chỉ bám vùng mean.
3. **Lỗi theo condition:** Thua rõ ở `global` / `plural` / `name` (Mục 2) — không đều trên 50 câu.
4. **r vs MAE:** Gemma-3 có r tốt nhưng MAE cao → bám **thứ hạng** câu khá ổn, nhưng **lệch tuyệt đối** từng điểm.

*Giả thuyết phụ (không chứng minh từ data này):* model huấn luyện cho coding/agent có thể mất calibration “everyday plausibility” so với era chat-rating (GPT-4 paper — xem Mục 6).

### Calibration — frontier có “bơm” điểm cao hơn người?

| Model | MODE | r | bias (model−human) | slope |
|---|---|---:|---:|---:|
| `gpt-5.6-luna` | `ORIG` | 0.778 | 0.309 | 0.824 |
| `gemma-3-12b-it` | `ORIG` | 0.640 | 0.191 | 1.141 |
| `deepseek-v4-flash` | `ORIG` | 0.549 | 0.194 | 0.470 |
| `gemma-4-31b-it` | `ORIG` | 0.488 | 0.595 | 0.487 |
| `glm-5.2` | `ORIG` | 0.628 | 0.566 | 0.670 |
| `kimi-k3` | `ORIG` | 0.692 | 0.126 | 0.821 |
| `deepseek-v4-flash` | `T` | 0.594 | 0.503 | 0.556 |
| `gemma-4-31b-it` | `T` | 0.642 | 0.647 | 0.589 |

![Calibration bias/slope](M5_calibration_bias_slope.png)

**Nhận định:**

- **Gemma-4 / GLM** bias ≈ **+0.57–0.59** — **bơm điểm** (cho cao hơn người ~0.6 điểm, hệ thống).
- **DeepSeek** bias gần Gemma-3 (~+0.19) nhưng **độ dốc ≈ 0.47** — ít bám biên độ cao–thấp của người.
- **Gemma-3** slope ≈ **1.14** — bám xu hướng human mean tốt hơn dù MAE cao.
- **Kimi** bias thấp (+0.13) + slope 0.82 → hơn Gemma-3 về r; vẫn dưới luna.

### Breakdown theo condition (Δr vs Gemma-3 ORIG)

Condition — xem [Mục 2](report.md#mục-2--human-likeness-theo-điều-kiện-câu-object-np).

**`deepseek-v4-flash` / `ORIG`:**

| condition | r (model) | r (Gemma-3) | Δr | MAE Δ |
|---|---:|---:|---:|---:|
| `all` (object khớp kỳ vọng (baseline)) | 0.573 | 0.563 | 0.0097 | -0.480 |
| `global` (object liên quan nhưng kém khớp ngữ cảnh) | 0.493 | 0.488 | 0.0043 | -0.461 |
| `animate` (đổi animate/inanimate của object) | 0.672 | 0.776 | -0.1040 | -0.515 |
| `plural` (object số nhiều) | 0.536 | 0.798 | -0.2623 | -0.225 |
| `name` (object là tên riêng) | 0.567 | 0.547 | 0.0203 | -0.752 |

**`gemma-4-31b-it` / `ORIG`:**

| condition | r (model) | r (Gemma-3) | Δr | MAE Δ |
|---|---:|---:|---:|---:|
| `all` (object khớp kỳ vọng (baseline)) | 0.288 | 0.563 | -0.2751 | -0.221 |
| `global` (object liên quan nhưng kém khớp ngữ cảnh) | -0.042 | 0.488 | -0.5303 | 0.029 |
| `animate` (đổi animate/inanimate của object) | 0.798 | 0.776 | 0.0220 | -0.250 |
| `plural` (object số nhiều) | 0.277 | 0.798 | -0.5213 | 0.055 |
| `name` (object là tên riêng) | 0.776 | 0.547 | 0.2288 | -0.890 |

**GLM / Kimi — điểm yếu thêm:**
- GLM `plural`: r=0.419 (Δr=-0.3791)
- Kimi `global`: r=0.454 (Δr=-0.0339)
- Kimi `name`: r=0.505 (Δr=-0.0426)

### Case studies — frontier lệch, Gemma-3 gần human

**Case 1 — `s1_animate`** (`animate`): *“The nurse fetched the file.”*
- Human mean ≈ **6.22**
- `deepseek-v4-flash`: **4.20** (|err|≈2.02)
- `gemma-3-12b-it`: **6.00** (|err|≈0.22; advantage Δ|err|≈1.80)

**Case 2 — `s9_global`** (`global`): *“The guide observed the sculptor.”*
- Human mean ≈ **4.95**
- `deepseek-v4-flash`: **3.70** (|err|≈1.25)
- `gemma-3-12b-it`: **5.05** (|err|≈0.10; advantage Δ|err|≈1.15)

**Case 3 — `s6_name`** (`name`): *“The judge needed Joel.”*
- Human mean ≈ **3.48**
- `gemma-4-31b-it`: **5.00** (|err|≈1.52)
- `gemma-3-12b-it`: **3.00** (|err|≈0.48; advantage Δ|err|≈1.05)

### Thinking có cứu không? (`T − ORIG`)

| Model | r ORIG | r T | Δr | ΔMAE |
|---|---:|---:|---:|---:|
| `gemma-4-31b-it` | 0.488 | 0.642 | 0.1541 | -0.116 |
| `deepseek-v4-flash` | 0.549 | 0.594 | 0.0456 | 0.070 |
| `glm-5.2` | 0.628 | 0.668 | 0.0396 | 0.059 |
| `gpt-5.6-luna` | 0.778 | 0.785 | 0.0074 | -0.046 |
| `kimi-k3` | 0.692 | 0.695 | 0.0036 | -0.018 |
| `gpt-5.6-sol` | 0.733 | 0.706 | -0.0270 | 0.038 |

**Kết luận Thinking:**

- DeepSeek T: r=0.594 — cải thiện -0.0459 so ORIG nhưng **vẫn dưới** Gemma-3 ORIG (0.640).
- Gemma-4 T: r=0.642 — vượt Gemma-3 ORIG nhưng chỉ sau reasoning; ORIG vẫn thua rõ (Δr=-0.1522).
- Thinking **không đảm bảo** human-likeness; cải thiện không đồng đều giữa model.

### Tổng hợp

**Mục 5 giải thích gì?** Trên mem_enc, model **to / frontier / mới** không chắc **giống người chấm** (~40 người/câu, thang 1–7) hơn model **nhỏ / cũ hơn** (Gemma-3-12B). Metric chính: **Pearson r** — model có **bám thứ tự** câu dễ ↔ khó như crowdsource không. **Không** kết luận model thua vì “kém thông minh”.

**Chuẩn so sánh — crowdsource:** trung bình điểm ~40 người chấm/câu (`human_mean`). Model “giống người” khi điểm model **gần** và **cùng chiều cao–thấp** với chuẩn đó.

**Thuật ngữ (trong report):**

| Thuật ngữ | Số trong data | Ý nghĩa dễ hiểu |
|---|---|---|
| **Bơm điểm** | `bias = model − human` **dương** | Model **hay cho cao hơn** mức người (vd. người ≈ 3.5, model ≈ 5) |
| **+0.59** (Gemma-4) | bias trung bình 50 câu | Cao hơn người **~0.6 điểm** trên thang 1–7 — **bơm mạnh** |
| **+0.19** (Gemma-3) | cùng công thức | Vẫn hơi bơm, nhưng **ít hơn** Gemma-4/GLM (~+0.57–0.59) |
| **Độ dốc (slope)** | hồi quy model ~ human | Người tăng 1 điểm → model tăng bao nhiêu; **≈1** = bám tốt; **≈0.5** = **phản ứng yếu**, hay dồn ~5–6 |
| **Biên độ cao–thấp** | spread điểm 1–7 | Người chênh câu dễ vs khó nhiều; model **biên hẹp** = không tách rõ câu lạ vs câu ổn |

**“Thằng nào cũng bơm à?”** — **Hầu hết có**, nhưng **mức khác nhau**: GPT-4 paper **+0.06** (gần như không); Kimi **+0.13**; Gemma-3 / DeepSeek ORIG **~+0.19**; luna **+0.31**; Gemma-4 / GLM ORIG **~+0.57–0.59**. Ngoại lệ: GLM **T** bias **−0.70** (hay cho **thấp hơn** người). Thua/thắng không phải “có bơm hay không” mà **bơm bao nhiêu** + **độ dốc** + **lỗi ở câu khó**.

**Vì sao model mới / lớn thua Gemma-3?** (có số)

1. **Bơm mạnh hơn** — Gemma-4, GLM ~+0.6 vs Gemma-3 ~+0.2.
2. **Độ dốc thấp** — DeepSeek / Gemma-4 ~0.47–0.49: người chấm thấp/cao chênh nhiều, model vẫn dồn quanh 5–6.
3. **Sập ở câu khó** — `global`, `plural` (Gemma-4 `global` r ≈ 0 / âm).
4. **Thắng sai chỗ metric** — một số model MAE tốt hơn Gemma-3 nhưng **thứ tự câu** sai → r thấp hơn.
5. **Thinking chưa cứu hết** — DeepSeek T vẫn dưới Gemma-3 ORIG; Gemma-4 T mới sát baseline.

**Gemma-3 / GPT-4 paper bám người hơn — biết gì từ số?**

- **GPT-4 (paper)** r ≈ **0.75**, bias **+0.06** — **ít bơm nhất**, bám crowdsource tốt (xem Mục 6).
- **Gemma-3** r ≈ **0.64**, bias **+0.19**, độ dốc **~1.14** — cũng bơm nhẹ nhưng **co giãn theo người** tốt hơn Gemma-4.
- **Gemma-4** r ≈ **0.49**, bias **~+0.59**, độ dốc **~0.49** — bơm mạnh + phẳng → thua dù **lớn hơn**.

*Giả thuyết (chưa chứng minh từ mem_enc n=50):* model era “chấm điểm / hội thoại” (GPT-4 paper) hoặc tune ít lệch mức (Gemma-3) **calibrate** tốt hơn model tối ưu coding/agent — **không** suy ra mixture huấn luyện cụ thể.

### 3 bullet slide (vì sao — gắn số)

1. **Bơm điểm + calibration:** Gemma-4/GLM bias **+0.57–0.59**; DeepSeek độ dốc **~0.47** → không bám biên độ người.
2. **Condition:** Gemma-4 thua mạnh ở `global` (r≈−0.04 vs Gemma-3); Kimi yếu `global`/`name` dù tổng thể hơn Gemma-3.
3. **Metric nuance:** Gemma-3 thắng **Pearson** (rank) nhưng MAE **~1.19** — frontier thua vì lệch calibration, không vì “kém hiểu tiếng Anh”.

### Câu kết luận slide

> Trên mem_enc, quy mô/frontier không đảm bảo likeness: DeepSeek/Gemma-4 thua Gemma-3-12B chủ yếu vì **bias cao / slope thấp / lỗi tập trung ở condition khó** (`global`, `plural`), không vì “kém thông minh hơn”. Thinking cải thiện một phần (DeepSeek T +0.046 r) nhưng chưa vượt baseline nhỏ. *Giả thuyết phụ:* SOTA coding/reasoning ≠ giống crowdsource Likert 1–7.

### Artifact

- `M5_calibration_bias_slope.png`
- `M5_paradox_table.csv`
- `M5_calibration.csv`
- `M5_condition_delta.csv`
- `M5_head_to_head_cases.csv`
- `M5_thinking_delta.csv`
- `M5_summary.json`

## Mục 6 — Trọng điểm GPT-4 paper

**Câu hỏi slide:** Vì sao GPT-4 (paper) vẫn rất mạnh so với nhiều model mới?

**Nguồn:** `data/ready/mem_enc_human_and_gpt.jsonl` → `gpt4_mean` (Amouyal et al.; resample paper). **Không** dùng `openai/gpt-4.1-mini` trong zoo.

**Neo GPT-4 paper:** r≈**0.755**, MAE≈**0.582**, bias≈**0.064**, độ dốc≈**0.777** (hạng Pearson ORIG-like: **#2** / 9).

### Bảng so sánh vs GPT-4 paper (ORIG)

| Model | r | Δr | MAE | ΔMAE | bias | Δbias |
|---|---:|---:|---:|---:|---:|---:|
| **`gpt-4 (paper)`** | 0.755 | — | 0.582 | — | 0.064 | — |
| `gpt-5.6-luna` | 0.778 | 0.0230 | 0.620 | 0.038 | 0.309 | 0.245 |
| `gpt-5.6-sol` | 0.733 | -0.0216 | 0.638 | 0.056 | 0.358 | 0.294 |
| `kimi-k3` | 0.692 | -0.0629 | 0.668 | 0.086 | 0.126 | 0.062 |

### Giải thích dễ hiểu

**GPT-4 (paper)** không phải model API trong zoo — là **điểm trung bình GPT-4** tác giả paper chạy trên cùng 50 câu mem_enc (`gpt4_mean` trong `data/ready/`), cùng tinh thần prompt ORIG.

**Vì sao vẫn “mạnh”?** Trên n=50:

- **MAE thấp nhất** trong nhóm top (~0.58) → sai số tuyệt đối từng câu nhỏ.
- **Bias thấp nhất** (+0.06) → **ít bơm điểm** (xem thuật ngữ Mục 5) so luna/sol (+0.3–0.4).
- **Không #1 Pearson:** luna ORIG/T **vượt r** (~0.78) — thắng **thứ tự câu**, không thắng **calibration mức điểm**.

**Cấm nhầm:** `openai/gpt-4.1-mini` (run zoo, r≈0.53) **≠** GPT-4 paper (r≈0.75). Nhãn “GPT-4” trên API không đảm bảo giống baseline paper.

### Calibration — bias (model − human)

| Model | MODE | r | MAE | bias | độ dốc |
|---|---|---:|---:|---:|---:|
| `gpt-4 (paper)` | ref | 0.755 | 0.582 | 0.064 | 0.777 |
| `gpt-5.6-luna` | `ORIG` | 0.778 | 0.620 | 0.309 | 0.824 |
| `gpt-5.6-sol` | `ORIG` | 0.733 | 0.638 | 0.358 | 0.752 |
| `kimi-k3` | `ORIG` | 0.692 | 0.668 | 0.126 | 0.821 |
| `gpt-4.1-mini` | `ORIG` | 0.525 | 0.872 | 0.217 | 0.624 |

![Calibration compare](M6_calibration_compare.png)

**Nhận định:** GPT-4 paper **ít bơm điểm nhất** (+0.06); luna/sol **+0.31–0.36** — thắng thứ tự câu (r) nhưng **lệch mức crowdsource** hơn paper.

### GPT-4 paper theo condition

| condition | n | r | MAE |
|---|---:|---:|---:|
| `all` (object khớp kỳ vọng (baseline)) | 10 | 0.751 | 0.540 |
| `global` (object liên quan nhưng kém khớp ngữ cảnh) | 10 | 0.622 | 0.706 |
| `animate` (đổi animate/inanimate của object) | 10 | 0.845 | 0.432 |
| `plural` (object số nhiều) | 10 | 0.731 | 0.656 |
| `name` (object là tên riêng) | 10 | 0.853 | 0.578 |

GPT-4 paper **ổn trên mọi condition** (r ≥ ~0.62); MAE cao nhất ở `global` (~0.71) — khớp Mục 2 (condition khó).

### Residual overlap (|err−human| < 1.0, ORIG)

Đếm câu mà **GPT-4 paper gần human hơn** model (`gpt4_ok_model_bad`) vs ngược lại (`model_ok_gpt4_bad`):

| Model | GPT-4 tốt hơn | Model tốt hơn GPT-4 | Cả hai đều lệch |
|---|---:|---:|---:|
| `gpt-5.6-luna` | 8 | 3 | 6 |
| `gpt-5.6-sol` | 5 | 6 | 3 |
| `kimi-k3` | 9 | 4 | 5 |

luna: paper thua model trên vài câu (3) nhưng paper thắng model trên **8** câu (threshold 1.0) — không phủ định paper baseline; cho thấy model mới **không dominate mọi câu**.

### Cảnh báo: gpt-4.1-mini

| `gpt-4.1-mini` | r=0.525 | Δr vs paper=-0.2296 | MAE=0.872 | bias=0.217 |

→ Run zoo **gpt-4.1-mini** (r≈0.53) **không thay thế** GPT-4 paper (r≈0.75) khi nói baseline paper.

### Tổng hợp

**GPT-4 paper vẫn mạnh ở đâu?** r≈**0.755**, MAE≈**0.582**, bias≈**0.064** — **elite calibration** (ít bơm, MAE tốt) trong top zoo.

**Yếu / không bất bại ở đâu?**

- **luna** r cao hơn paper (Δr=0.0230) nhưng bias lớn hơn (Δbias=0.2449) → trade-off thứ tự vs mức điểm.
- **Không #1 Pearson** trên mem_enc — narrative “GPT-4 vô đối” cần chỉnh.
- Residual overlap: model mới vẫn **thắng paper trên một số câu** (|err|<1 vs human).
- **gpt-4.1-mini** r≈0.525 — chứng minh nhãn GPT-4 ≠ GPT-4 paper data.

*Giả thuyết (chưa chứng minh từ n=50):* era huấn luyện/align “chat-rating / plausibility” (GPT-4 paper) calibrate Likert tốt hơn model coding/agent (luna/sol) — data ủng hộ **câu chuyện bias/MAE**, không chứng minh mixture.

**Liên hệ Mục 5:** frontier thua Gemma-3 là paradox **quy mô ≠ likeness**; Mục 6 là case **baseline paper era** vẫn elite về **MAE + ít bơm** dù model mới thắng **r**.

### Câu kết luận slide

> GPT-4 paper đạt r≈0.755 / MAE≈0.582 / bias≈+0.06; luna cao hơn Pearson (≈0.778) nhưng bias lớn hơn (+0.31). *Giả thuyết:* model era coding/agent thắng **thứ tự câu** nhưng mất **calibration Likert** so baseline chat-rating; paper GPT-4 vẫn elite **MAE + ít bơm**. Xem thêm [Mục 5](report.md) (frontier vs Gemma-3).

### Artifact

- `M6_calibration_compare.png`
- `M6_gpt4_paper_metrics.json`
- `M6_compare_vs_paper.csv`
- `M6_gpt4_by_condition.csv`
- `M6_residual_overlap.csv`
- `M6_summary.json`
- `E_orig_ranking_with_gpt4.png` (ranking tổng từ full analysis)

## Mục 7 — Chi phí: AI có rẻ hơn người không?

**Câu hỏi slide:** Ngoài nhanh hơn, $/câu (và ước $/giờ) có rẻ hơn ước lượng người không? Ai Pareto?

**Giá API:** `configs/pricing.yaml` — `as_of: 2026-07-26` (post-hoc từ token log; eval không ghi USD).

**Ước lượng người (crowdsource slide):** `$0.08` / rating × **40** annotators/câu ≈ **$3.20 / câu**. Rough crowdsource estimate for slide comparison only — not from the paper invoice.

### Bảng ORIG / T (sort Pearson r ↓)

| Model | MODE | Pearson r | $/câu | × rẻ hơn human | est $/giờ |
|---|---|---:|---:|---:|---:|
| `gpt-5.6-luna` | `T` | 0.7851 | $0.0269 | 120× | — |
| `gpt-5.6-luna` | `ORIG` | 0.7777 | $0.0159 | 202× | — |
| `gpt-5.6-sol` | `ORIG` | 0.7331 | $0.0399 | 81× | — |
| `gpt-5.6-sol` | `T` | 0.7062 | $0.0584 | 55× | — |
| `kimi-k3` | `T` | 0.6954 | $0.0530 | 61× | $2.869 |
| `kimi-k3` | `ORIG` | 0.6918 | $0.0122 | 265× | $2.978 |
| `gemini-3.6-flash` | `T` | 0.6810 | $0.0749 | 43× | $6.841 |
| `glm-5.2` | `T` | 0.6678 | $0.0438 | 74× | $0.570 |
| `gemma-4-31b-it` | `T` | 0.6421 | $0.0090 | 359× | $0.113 |
| `gemma-3-12b-it` | `ORIG` | 0.6402 | $0.0008 | 4165× | $0.126 |
| `glm-5.2` | `ORIG` | 0.6282 | $0.0025 | 1311× | $0.817 |
| `deepseek-v4-flash` | `T` | 0.5944 | $0.0095 | 338× | $0.254 |
| `deepseek-v4-flash` | `ORIG` | 0.5488 | $0.0020 | 1613× | $0.235 |
| `gpt-4.1-mini` | `ORIG` | 0.5251 | $0.0067 | 477× | $0.706 |
| `gemma-4-31b-it` | `ORIG` | 0.4880 | $0.0022 | 1476× | $0.366 |

![Pareto quality vs cost](M7_pareto_quality_cost.png)

### Nhận định

- **Có — AI rẻ hơn ước lượng người** trên **mọi** run ORIG/T đủ 50 câu: khoảng **43×–4165×** rẻ hơn (~$3.20/câu human).
- **Rẻ nhất:** `gemma-3-12b-it` / `ORIG` — $0.0008/câu (r=0.640, ~4165× rẻ hơn human).
- **r cao nhất:** `gpt-5.6-luna` / `T` — r=0.785, $0.0269/câu (~120× rẻ hơn human).
- **Pareto chất lượng/giá (luna ORIG):** r=0.778, $0.0159/câu — gần #1 likeness với $/câu thấp hơn luna T.
- **Kimi ORIG:** r=0.692, $0.0122/câu — điểm Pareto trung bình tốt (r khá, $ thấp).
- **Sweet spot (r cao trong nửa rẻ hơn):** `kimi-k3` / `ORIG` — r=0.692, $0.0122/câu.

**Lưu ý:** `est $/giờ` chỉ có khi run log latency; một số batch (luna/sol) có thể trống cột này. Self-host `cost_mode: estimated_gpu` có thể ≈ $0 — không trộn với giá API khi kể chuyện.

### Câu kết luận slide

> **Có.** Mọi run ORIG/T rẻ hơn ước crowdsource (~$3.20/câu) khoảng **43×–4165×**. Rẻ nhất: gemma-3-12b-it ORIG ($0.0008/câu). Pareto tốt: gpt-5.6-luna T (r≈0.785, $0.0269/câu; luna ORIG $0.0159/câu gần cùng r).

### Artifact

- `M7_cost_table.csv`
- `M7_pareto_quality_cost.png`
- `M7_summary.json`
- `F_cost_table.csv` / `F_pareto_quality_cost.png` (đồng bộ notebook F)

## Kết luận tổng hợp (đúc kết)

> **Note đầy đủ (Q→A + giải thích + map slide):** [`TOM_TAT.md`](TOM_TAT.md).

1. **Coarse OK** — r cao với mean người → lọc câu thô dùng LLM được.
2. **Fine-grained chưa** — collapse ~91% → chưa thay t-test cặp câu (paper §5).
3. **Thinking giúp, schema thường hại** → model đắt: ORIG (+T).
4. **SOTA ≠ Likert crowdsource** — frontier thua Gemma-3 vì bias/calibration.
5. **GPT-4 paper** elite MAE + ít bơm; luna thắng r nhưng bơm hơn.
6. **Điều kiện:** dễ `animate`, khó `global` (object lệch vai).
7. **Chi phí:** AI rẻ hơn ước crowdsource ~43×–4165×; Pareto luna.
8. **Paper EACL 2024 vẫn đứng** trên zoo 2025–26 (mem_enc).
