#!/usr/bin/env python3
"""Run full mem_enc analysis → results/analysis/."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from plausibility_eval.analysis import run_full_analysis  # noqa: E402
from plausibility_eval.io_utils import load_yaml  # noqa: E402
from plausibility_eval.summary import summarize_all  # noqa: E402


def main() -> None:
    exp = load_yaml(ROOT / "configs" / "experiment.yaml")
    summary = summarize_all(repo=ROOT, coarse_threshold=float(exp.get("coarse_threshold") or 3.0))
    print("summarize_all n_runs:", summary["n_runs"])
    out = run_full_analysis(ROOT)
    print("analysis out_dir:", out["out_dir"])
    print("findings keys:", list(out["findings"].keys()))
    top = out["findings"].get("top_overall")
    if top:
        print(f"top: {top['model_id']} / {top['mode']} r={top['pearson_r']}")


if __name__ == "__main__":
    main()
