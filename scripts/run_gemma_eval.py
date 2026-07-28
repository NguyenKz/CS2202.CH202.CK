#!/usr/bin/env python3
"""Run plausibility eval against local Gemma 4 12B (llama-server).

Examples:
  python scripts/run_gemma_eval.py --mode ORIG
  python scripts/run_gemma_eval.py --mode ORIG --smoke
  python scripts/run_gemma_eval.py --mode ST --ensure-server
  # Resume is ON by default (skip done sentences / reuse call files)
  python scripts/run_gemma_eval.py --mode S
  python scripts/run_gemma_eval.py --mode S --no-resume   # force full API re-run
  python scripts/run_gemma_eval.py --mode S --max-concurrency 8
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def _repo_root() -> Path:
    here = Path(__file__).resolve().parent.parent
    if (here / "configs" / "experiment.yaml").exists():
        return here
    raise SystemExit(f"Cannot find doan root from {here}")


def _ensure_src(repo: Path) -> None:
    src = repo / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def _api_ok(base_url: str) -> bool:
    url = base_url.rstrip("/") + "/models"
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            return r.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _ensure_server(repo: Path, base_url: str) -> None:
    if _api_ok(base_url):
        print(f"[ok] server already up: {base_url}", flush=True)
        return
    script = repo / "scripts" / "serve_gemma.sh"
    print(f"[start] launching {script} ...", flush=True)
    subprocess.run(["bash", str(script)], check=True)
    for _ in range(60):
        if _api_ok(base_url):
            print(f"[ok] server ready: {base_url}", flush=True)
            return
        time.sleep(2)
    raise SystemExit(f"Server not ready at {base_url}")


def main() -> None:
    p = argparse.ArgumentParser(description="Eval Gemma 4 12B local (ORIG/S/T/ST/ST-E)")
    p.add_argument("--mode", default="ORIG", help="ORIG | S | T | ST | ST-E")
    p.add_argument("--model", default="gemma-4-12b")
    p.add_argument("--base-url", default="http://127.0.0.1:8080/v1")
    p.add_argument("--token", default="sk-local")
    p.add_argument("--smoke", action="store_true", help="Only first N sentences (experiment.yaml)")
    p.add_argument("--limit-sentences", type=int, default=None)
    p.add_argument("--n-samples", type=int, default=None, help="Override n_samples (default 20)")
    p.add_argument("--ensure-server", action="store_true", help="Start serve_gemma.sh if needed")
    p.add_argument(
        "--openrouter-providers",
        nargs="*",
        default=None,
        help='OpenRouter provider order, e.g. --openrouter-providers "Google AI Studio" DeepInfra',
    )
    p.add_argument(
        "--no-openrouter-fallbacks",
        action="store_true",
        help="Set provider.allow_fallbacks=false on OpenRouter",
    )
    p.add_argument(
        "--no-resume",
        action="store_true",
        help="Do not skip completed sentences / reuse call files",
    )
    p.add_argument(
        "--max-concurrency",
        type=int,
        default=None,
        help="Parallel API requests (default: experiment.yaml max_concurrency)",
    )
    p.add_argument(
        "--reasoning-effort",
        default=None,
        help="When MODE has thinking: max|xhigh|high|medium|low|minimal|none",
    )
    p.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="Override sampling temperature (default: open/closed from experiment.yaml)",
    )
    p.add_argument(
        "--request-delay",
        type=float,
        default=None,
        help="Min seconds between API requests (default: experiment.yaml request_delay_sec)",
    )
    p.add_argument(
        "--rate-limit-retries",
        type=int,
        default=None,
        help="Retries after 429 wait (default: experiment.yaml rate_limit_retries)",
    )
    args = p.parse_args()

    repo = _repo_root()
    _ensure_src(repo)

    if args.ensure_server:
        _ensure_server(repo, args.base_url)
    elif not _api_ok(args.base_url):
        raise SystemExit(
            f"No server at {args.base_url}. Start with:\n"
            f"  bash {repo / 'scripts' / 'serve_gemma.sh'}\n"
            f"or re-run with --ensure-server"
        )

    from plausibility_eval.run_eval import run_evaluation

    result = run_evaluation(
        model=args.model,
        token=args.token or os.environ.get("OPENAI_API_KEY") or "sk-local",
        base_url=args.base_url,
        mode=args.mode,
        repo=repo,
        smoke=args.smoke,
        n_samples_override=args.n_samples,
        limit_sentences=args.limit_sentences,
        resume=not args.no_resume,
        max_concurrency=args.max_concurrency,
        reasoning_effort=args.reasoning_effort,
        temperature_override=args.temperature,
        request_delay_sec=args.request_delay,
        rate_limit_retries=args.rate_limit_retries,
        openrouter_providers=args.openrouter_providers,
        openrouter_allow_fallbacks=(False if args.no_openrouter_fallbacks else None),
    )
    print("out_dir:", result["out_dir"], flush=True)
    print("metrics:", result["metrics"], flush=True)


if __name__ == "__main__":
    main()
