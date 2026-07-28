# Notebooks

| Notebook | Chạy ở đâu | Mục đích |
|---|---|---|
| [`deploy/01_llamacpp_openai_server.ipynb`](deploy/01_llamacpp_openai_server.ipynb) | **Colab** (GPU) | Serve GGUF + ngrok → dán `BASE_URL` vào eval |
| [`eval/10_eval_plausibility.ipynb`](eval/10_eval_plausibility.ipynb) | **Local** | Realtime: `MODEL` / `TOKEN` / `BASE_URL` / `MODE` (OpenRouter / local / OpenAI) |
| [`eval/11_eval_openai_batch.ipynb`](eval/11_eval_openai_batch.ipynb) | **Local** | **OpenAI Batch API** (−50%): build → submit → poll → ingest |
| [`20_compare_summary.ipynb`](20_compare_summary.ipynb) | **Local** | Tokens × `pricing.yaml` → SUMMARY |

**MODE** = ablation: `ORIG` (baseline paper) · `S` (schema) · `T` (thinking) · `ST` · `ST-E` (không few-shot).

### Gemma local (CLI, khỏi notebook)

```bash
cd doan
bash scripts/serve_gemma.sh                          # dùng GGUF LocalLLM sẵn có
python scripts/run_gemma_eval.py --mode ORIG --smoke # thử nhanh
python scripts/run_gemma_eval.py --mode ORIG         # full mem_enc × 20
python scripts/run_gemma_eval.py --mode ORIG --ensure-server
```

Helpers: [`../src/plausibility_eval/`](../src/plausibility_eval/) · Configs: [`../configs/`](../configs/)
