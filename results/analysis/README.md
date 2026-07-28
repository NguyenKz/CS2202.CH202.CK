# Analysis findings (auto)

- Runs (n≥50): **20**
- Top by Pearson: `gpt-5.6-luna` / `T` (r=0.7850968602212802)
- Best ORIG: `{'model_id': 'gpt-5.6-luna', 'mode': 'ORIG', 'pearson_r': 0.7776668912632118, 'mae': 0.6199119999999999, 'rmse': 0.7856968850644629, 'bias_model_minus_human': 0.3088159999999999, 'slope': 0.8235681071481022, 'note': ''}`
- GPT-4 paper: `{'model_id': 'gpt-4 (paper)', 'mode': 'ORIG*', 'pearson_r': 0.7546998299324308, 'mae': 0.5822320000000001, 'rmse': 0.7487967216808578, 'bias_model_minus_human': 0.06386800000000005, 'slope': 0.7769079970192213, 'note': 'from data/ready gpt4_mean; not openai/gpt-4.1-mini'}`
- Condition lowest mean MAE: `{'condition': 'plural', 'mean_mae': 0.7350436402116401, 'n_runs': 15}`
- Condition highest mean MAE: `{'condition': 'global', 'mean_mae': 0.8399037777777778, 'n_runs': 15}`

## Files

- `A_coverage.json`
- `A_leaderboard.csv`
- `B_by_condition.csv`
- `B_condition_heatmap.png`
- `B_condition_rank_mae.csv`
- `B_top_residuals.csv`
- `C_case_histograms.png`
- `C_dispersion.csv`
- `C_dispersion_summary.csv`
- `C_high_disagreement_sentences.csv`
- `D_schema_deltas.csv`
- `E_gpt4_paper_by_condition.json`
- `E_orig_ranking_with_gpt4.png`
- `E_ranking_with_gpt4_paper.csv`
- `E_residual_overlap_vs_gpt4.csv`
- `F_cost_table.csv`
- `F_pareto_quality_cost.png`
- `findings_summary.json`
