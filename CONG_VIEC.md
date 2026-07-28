# Công việc nhóm sẽ làm

Đã chốt. Chi tiết theo ngày/phase: [`docs/02_main_tasks.md`](docs/02_main_tasks.md), [`docs/03_timeline_1_week.md`](docs/03_timeline_1_week.md).

## Nguyên tắc

- Dùng **nhãn người của paper** (`data/`) — không tự annotate gold mới
- Prompt lấy từ paper — không invent từ đầu
- Không train
- **Cả nhóm** đọc hiểu paper trước; experiment chia theo **model**; slide/báo cáo chia **sau khi có số**

## Các bước

1. **Cả nhóm đọc hiểu paper**  
   Pretest plausibility là gì, paper hỏi gì, coarse vs fine.

2. **Notebook chung + thử model**  
   Load data, gọi prompt, smoke-test → chốt **3–4 model**.

3. **Mỗi người chạy 1–2 model**  
   Batch trên cùng subset → `results/<model>/` (scores + metrics + notes nhận xét riêng).

4. **Gộp số liệu**  
   Bảng tổng Human vs các model + 3–5 case study (+3/+1).

5. **Mới chia deliverable cuối**
   - **Speaker A:** giới thiệu, lý thuyết, overview  
   - **Speaker B:** phân tích kết quả thực nghiệm + demo nhanh  
   - **Editor:** tổng hợp viết báo cáo  

6. **Rehearsal** 15 phút thuyết trình + demo/Q&A.

## Hướng đóng góp chính (đã chốt)

Trên **cùng 1 model + cùng base prompt**, so với pipeline gốc (**ORIG** = không schema, không thinking, có examples):

| Điều kiện | Schema | Thinking | Examples |
|---|---|---|---|
| ORIG | Không | Không | Có |
| S | Có | Không | Có |
| T | Không | Có | Có |
| ST | Có | Có | Có |
| ST−E | Có | Có | **Không** |

“Tốt hơn” = gần human hơn (Pearson / MAE). Chi tiết: [`docs/08_ablation_json_thinking.md`](docs/08_ablation_json_thinking.md).

### Chính sách budget (đã note)

- **`n_samples = 20`** (khớp paper) — giữ cố định; model đắt sẽ tính tiếp khi chạy (có thể giảm sau, phải ghi `run_meta`).
- **Model lớn / đắt** (GPT-5.x flagship, Kimi K3, Claude Sonnet/Opus, …): chỉ chạy **ORIG + ST**  
  (baseline paper-like vs schema+thinking — đủ để so đóng góp chính, tiết kiệm ~60% call so với full 5 MODE).
- **Model rẻ / self-host** (vd. GLM 5.2, DeepSeek Flash, Gemma self-host): ưu tiên **full matrix** 5 MODE nếu budget cho phép.
- Subset mặc định: `mem_enc` (50 câu). Chi tiết ma trận: [`configs/model_coverage.yaml`](configs/model_coverage.yaml).

### Tổng lần call LLM (mỗi model × mỗi MODE)

```
calls = số_câu × n_samples
      = 50 (mem_enc) × 20
      = 1000 lần / (model × MODE)
```

| Phạm vi | Số MODE | Tổng call (mem_enc, n=20) |
|---|---:|---:|
| 1 model × 1 MODE | 1 | **1000** |
| Model đắt: ORIG + ST | 2 | **2000** |
| Model rẻ: full matrix | 5 | **5000** |

Mỗi call → 1 file raw trong `results/<model>/<MODE>/calls/`.

## Không làm

- Dataset người chấm mới làm hệ quy chiếu chính  
- Chia silo kiểu một người chỉ lý thuyết, người kia chỉ code từ đầu chí cuối  
- Làm slide số liệu khi chưa có kết quả chạy model  
