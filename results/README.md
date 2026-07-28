# Results layout

```text
results/
  <model_dirname>/<MODE>/
    calls/*.json      # raw request/response/reasoning/trace_id/tokens
    scores.jsonl      # per-sentence scores + token totals (NO cost_usd)
    metrics.json      # quality + token aggregates
    run_meta.json
    notes.md
    metrics_with_cost.json   # written ONLY by summary notebook
  SUMMARY.md
  SUMMARY.csv
  pareto_quality_cost.png
```

`model_dirname`: `/` → `__` (e.g. `deepseek/deepseek-v4-flash` → `deepseek__deepseek-v4-flash`).

There may be a tiny `demo_model/ORIG` fixture (synthetic, no API) used to validate the summary pipeline — safe to delete.

Do not commit API keys. Prefer committing metrics / SUMMARY; large `calls/` may be gitignored locally if needed.
