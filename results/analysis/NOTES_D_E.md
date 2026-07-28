# Schema & GPT-4 analysis notes (Checklist D + E)

Auto-supporting narrative for `30_analysis_report.ipynb`. Evidence from `results/analysis/*.csv`.

## D — Why schema often hurts human-likeness

**Evidence (ΔPearson S−ORIG / ST−T):**

| Model | S−ORIG Δr | ST−T Δr |
|---|---:|---:|
| deepseek-v4-flash | **−0.135** | **−0.101** |
| gemma-3-12b-it | −0.056 | (no T/ST) |
| gemma-4-31b-it | +0.131 (exception) | **−0.087** |

On deepseek (clearest small-model matrix), schema is the largest human-likeness drop. Thinking alone (T−ORIG) is often neutral/slightly positive; **ST is worse than T**.

**Likely mechanisms (interpretive, tied to protocol):**

1. **Format mismatch with human task.** Paper ORIG asks free-text `"The naturalness score is N (...)"` — same surface form as human instruction. JSON schema forces a different generation policy (field filling / constrained decoding), which is not how annotators produce Likert feels.
2. **Calibration compression.** Schema models often emit “safe” mid-scale integers with short `reason` strings → lower correlation with nuanced human means even when MAE does not explode.
3. **Thinking + schema interaction.** ST adds reasoning tokens then packs into JSON; extra compute does not restore the free-text rating channel that matches human labels.
4. **Parse is not the issue.** Parse-fail rates stay ~0 for S/ORIG on these runs — the harm is **likeness**, not validity.

**Operational conclusion:** For the goal “giống người” (Pearson/MAE vs human), drop S/ST on large models; keep ORIG (+ optional T). Schema remains useful only if the product needs machine-readable JSON, not human-likeness.

## E — GPT-4 paper vs modern models (trọng điểm)

**On this mem_enc n=50 subset (ready `gpt4_mean`):**

| Rank (ORIG-like) | Model | Pearson r | MAE | bias (model−human) |
|---|---|---:|---:|---:|
| 1 | gpt-5.6-luna ORIG | **0.778** | 0.620 | +0.31 |
| 2 | **gpt-4 (paper)** | **0.755** | **0.582** | **+0.06** |
| 3 | gpt-5.6-sol ORIG | 0.733 | 0.638 | +0.36 |

Nuance vs the “GPT-4 bất bại” story:

- Paper GPT-4 is **still elite** (best MAE among top rows; smallest systematic bias).
- It is **not strictly #1 on Pearson** here: **luna ORIG/T beat it** on correlation.
- `openai/gpt-4.1-mini` (our run, r≈0.53) is **not** paper GPT-4 — do not conflate.

**Structured checks supporting / refining the training-era hypothesis:**

1. **Calibration:** Newer strong models (luna/sol) show **larger positive bias** (+0.3–0.4) than paper GPT-4 (+0.06) — they rate situations more “natural” than humans on average. That fits “fluent / helpful assistant prior” more than “crowdsource Likert feel.”
2. **Variance collapse (Checklist C):** On top-15 human-disagreement sentences, nearly all models have `collapse_rate≈1.0` (model_std ≪ human_std). Humans disagree; LLMs resample stably. Paper GPT-4 means also average multiple runs but still track human means with low bias.
3. **Condition profile:** Hardest mean MAE across ORIG/T runs is **`global`**; easiest **`plural`**. GPT-4 paper remains competitive across conditions (`E_gpt4_paper_by_condition.json`).
4. **Narrative (hypothesis, not causal proof):** Shift from chat-rating pretraining/evals toward coding/agent objectives can reduce one-shot “everyday plausibility” calibration even as general capability rises. Our data **supports a calibration/variance story**, not a direct proof of training mixture.

**Bottom line for the report:** GPT-4 paper remains a formidable human-likeness baseline (esp. MAE/bias). Modern winners (luna) can exceed it on Pearson but still look “too confident / too positive” relative to human disagreement and mean level.
