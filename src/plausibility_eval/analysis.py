"""Offline analysis helpers for mem_enc results (no LLM calls)."""

from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .cost import human_cost_per_sentence, lookup_price, tokens_to_usd
from .io_utils import load_yaml, read_jsonl, write_json
from .metrics import coarse_accuracy, compute_metrics
from .summary import discover_runs

CONDS = ("all", "global", "animate", "plural", "name")
_SID_RE = re.compile(r"^(s\d+)_(all|global|animate|plural|name)$")


def parse_sample_id(sample_id: str) -> Tuple[Optional[str], Optional[str]]:
    m = _SID_RE.match(str(sample_id))
    if not m:
        return None, None
    return m.group(1), m.group(2)


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
    n = len(xs)
    if n < 2 or n != len(ys):
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den_x = math.sqrt(sum((x - mx) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - my) ** 2 for y in ys))
    if den_x == 0 or den_y == 0:
        return None
    return num / (den_x * den_y)


def _std(xs: Sequence[float]) -> Optional[float]:
    n = len(xs)
    if n < 2:
        return None
    m = sum(xs) / n
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def _mae(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
    if not xs or len(xs) != len(ys):
        return None
    return sum(abs(a - b) for a, b in zip(xs, ys)) / len(xs)


def load_runs(
    repo: Path,
    *,
    min_n: int = 50,
    exclude_smoke: bool = True,
) -> List[Dict[str, Any]]:
    """Load scored runs; drop smoke / incomplete by default."""
    pricing = load_yaml(repo / "configs" / "pricing.yaml")
    runs_out: List[Dict[str, Any]] = []
    for run_dir in discover_runs(repo / "results"):
        rows = read_jsonl(run_dir / "scores.jsonl")
        meta: Dict[str, Any] = {}
        meta_path = run_dir / "run_meta.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        model_id = str(meta.get("model") or run_dir.parent.name.replace("__", "/"))
        mode = str(meta.get("mode") or run_dir.name)
        n = len(rows)
        if exclude_smoke and n < min_n:
            continue
        metrics = compute_metrics(rows)
        price = lookup_price(pricing, model_id)
        usage = metrics.get("usage_totals") or {}
        cost = tokens_to_usd(usage, price)
        n_scored = max(int(metrics.get("n_scored") or 1), 1)
        mean_llm = cost["total"] / n_scored
        human_costs = [
            human_cost_per_sentence(pricing, r.get("human_n_annotators") or r.get("human_n"))
            for r in rows
            if r.get("human_mean") is not None
        ]
        mean_human = (
            sum(human_costs) / len(human_costs)
            if human_costs
            else human_cost_per_sentence(pricing)
        )
        lat = float(metrics.get("latency_ms_total") or 0.0)
        n_calls = int(usage.get("n_api_calls") or 0) or 1
        mean_lat_s = (lat / 1000.0) / n_calls if lat else None
        cost_per_hour = None
        if mean_lat_s and mean_lat_s > 0:
            calls_per_hour = 3600.0 / mean_lat_s
            cost_per_call = cost["total"] / n_calls
            cost_per_hour = calls_per_hour * cost_per_call

        runs_out.append(
            {
                "run_dir": str(run_dir),
                "model_id": model_id,
                "mode": mode,
                "n_sentences": n,
                "rows": rows,
                "meta": meta,
                "metrics": metrics,
                "pearson_r": metrics.get("pearson_r"),
                "mae": metrics.get("mae"),
                "rmse": metrics.get("rmse"),
                "parse_fail_rate": metrics.get("parse_fail_rate"),
                "coarse_acc": coarse_accuracy(rows),
                "total_tokens": usage.get("total_tokens"),
                "mean_cost_per_sentence_usd": mean_llm,
                "cost_ratio_vs_human": (mean_llm / mean_human) if mean_human else None,
                "pricing_source": cost.get("pricing_source"),
                "cost_mode": cost.get("cost_mode"),
                "latency_ms_total": lat,
                "mean_latency_s_per_call": mean_lat_s,
                "est_cost_per_hour_usd": cost_per_hour,
                "modes_coverage_note": None,
            }
        )
    runs_out.sort(key=lambda r: (-(r["pearson_r"] or -1), r["model_id"], r["mode"]))
    return runs_out


def coverage_matrix(runs: Sequence[Dict[str, Any]]) -> Dict[str, List[str]]:
    cov: Dict[str, List[str]] = defaultdict(list)
    for r in runs:
        cov[r["model_id"]].append(r["mode"])
    return {k: sorted(set(v)) for k, v in sorted(cov.items())}


def leaderboard_rows(runs: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cov = coverage_matrix(runs)
    out = []
    for r in runs:
        out.append(
            {
                "model_id": r["model_id"],
                "mode": r["mode"],
                "n": r["n_sentences"],
                "pearson_r": r["pearson_r"],
                "mae": r["mae"],
                "rmse": r["rmse"],
                "coarse_acc": r["coarse_acc"],
                "parse_fail_rate": r["parse_fail_rate"],
                "total_tokens": r["total_tokens"],
                "mean_cost_per_sentence_usd": r["mean_cost_per_sentence_usd"],
                "cost_ratio_vs_human": r["cost_ratio_vs_human"],
                "pricing_source": r["pricing_source"],
                "modes_available": ",".join(cov.get(r["model_id"], [])),
            }
        )
    return out


def mode_leaderboard(runs: Sequence[Dict[str, Any]], mode: str) -> List[Dict[str, Any]]:
    """Pearson/MAE table for one MODE only (sorted by r desc)."""
    rows = [r for r in leaderboard_rows(runs) if r["mode"] == mode]
    rows.sort(key=lambda x: (-(x["pearson_r"] or -1), x["model_id"]))
    for i, r in enumerate(rows, start=1):
        r["rank"] = i
    return rows


def ensemble_models_as_annotators(
    runs: Sequence[Dict[str, Any]],
    *,
    mode: str,
    extra_annotators: Optional[Dict[str, Dict[str, float]]] = None,
) -> Dict[str, Any]:
    """Treat each model (and optional extras) as one annotator: equal-weight mean per sentence.

    ``extra_annotators`` maps annotator_id → {sample_id: score}, e.g. paper gpt4_mean.
    """
    mode_runs = [r for r in runs if r["mode"] == mode]
    if not mode_runs and not extra_annotators:
        return {
            "mode": mode,
            "n_models": 0,
            "model_ids": [],
            "n_sentences": 0,
            "pearson_r": None,
            "mae": None,
            "bias_ensemble_minus_human": None,
            "best_single": None,
            "delta_r_vs_best_single": None,
            "per_sentence": [],
        }

    by_sid: Dict[str, Dict[str, Any]] = {}
    for r in mode_runs:
        for row in r["rows"]:
            sid = str(row.get("sample_id") or "")
            hm, mm = row.get("human_mean"), row.get("model_mean")
            if not sid or hm is None or mm is None:
                continue
            bucket = by_sid.setdefault(
                sid,
                {
                    "sample_id": sid,
                    "sentence": row.get("sentence"),
                    "human_mean": float(hm),
                    "votes": {},
                },
            )
            bucket["votes"][r["model_id"]] = float(mm)

    if extra_annotators:
        for aid, scores in extra_annotators.items():
            for sid, score in scores.items():
                bucket = by_sid.get(sid)
                if not bucket:
                    continue
                bucket["votes"][aid] = float(score)

    per_sentence: List[Dict[str, Any]] = []
    humans: List[float] = []
    ens: List[float] = []
    for sid in sorted(by_sid.keys()):
        bucket = by_sid[sid]
        votes = bucket["votes"]
        if not votes:
            continue
        e_mean = sum(votes.values()) / len(votes)
        h_mean = float(bucket["human_mean"])
        vote_std = _std(list(votes.values()))
        per_sentence.append(
            {
                "sample_id": sid,
                "sentence": bucket.get("sentence"),
                "human_mean": h_mean,
                "ensemble_mean": e_mean,
                "abs_err": abs(e_mean - h_mean),
                "n_annotators": len(votes),
                "model_vote_std": vote_std,
            }
        )
        humans.append(h_mean)
        ens.append(e_mean)

    best_single = None
    if mode_runs:
        best = max(mode_runs, key=lambda r: r["pearson_r"] if r["pearson_r"] is not None else -1)
        best_single = {
            "model_id": best["model_id"],
            "mode": best["mode"],
            "pearson_r": best["pearson_r"],
            "mae": best["mae"],
        }

    pearson = _pearson(humans, ens)
    mae = _mae(humans, ens)
    bias = (sum(e - h for h, e in zip(humans, ens)) / len(humans)) if humans else None
    model_ids = sorted({r["model_id"] for r in mode_runs})
    if extra_annotators:
        model_ids = sorted(set(model_ids) | set(extra_annotators.keys()))

    return {
        "mode": mode,
        "n_models": len(model_ids),
        "model_ids": model_ids,
        "n_sentences": len(per_sentence),
        "pearson_r": pearson,
        "mae": mae,
        "bias_ensemble_minus_human": bias,
        "best_single": best_single,
        "delta_r_vs_best_single": (
            (pearson - best_single["pearson_r"])
            if pearson is not None and best_single and best_single["pearson_r"] is not None
            else None
        ),
        "mean_abs_err": mae,
        "per_sentence": per_sentence,
    }


def metrics_by_condition(rows: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in rows:
        _, cond = parse_sample_id(str(r.get("sample_id") or ""))
        if cond:
            buckets[cond].append(r)
    out: Dict[str, Dict[str, Any]] = {}
    for cond in CONDS:
        rs = buckets.get(cond) or []
        human = [float(x["human_mean"]) for x in rs if x.get("human_mean") is not None and x.get("model_mean") is not None]
        model = [float(x["model_mean"]) for x in rs if x.get("human_mean") is not None and x.get("model_mean") is not None]
        out[cond] = {
            "n": len(model),
            "pearson_r": _pearson(human, model),
            "mae": _mae(human, model),
        }
    return out


def condition_table(runs: Sequence[Dict[str, Any]], modes: Optional[Sequence[str]] = None) -> List[Dict[str, Any]]:
    modes_set = set(modes) if modes else None
    rows_out: List[Dict[str, Any]] = []
    for r in runs:
        if modes_set is not None and r["mode"] not in modes_set:
            continue
        by_c = metrics_by_condition(r["rows"])
        for cond, m in by_c.items():
            rows_out.append(
                {
                    "model_id": r["model_id"],
                    "mode": r["mode"],
                    "condition": cond,
                    "n": m["n"],
                    "pearson_r": m["pearson_r"],
                    "mae": m["mae"],
                }
            )
    return rows_out


def top_residuals(runs: Sequence[Dict[str, Any]], *, k: int = 15, modes: Sequence[str] = ("ORIG", "T")) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for r in runs:
        if r["mode"] not in modes:
            continue
        for row in r["rows"]:
            hm, mm = row.get("human_mean"), row.get("model_mean")
            if hm is None or mm is None:
                continue
            fam, cond = parse_sample_id(str(row.get("sample_id") or ""))
            out.append(
                {
                    "model_id": r["model_id"],
                    "mode": r["mode"],
                    "sample_id": row.get("sample_id"),
                    "family": fam,
                    "condition": cond,
                    "sentence": row.get("sentence"),
                    "human_mean": float(hm),
                    "model_mean": float(mm),
                    "abs_err": abs(float(hm) - float(mm)),
                }
            )
    out.sort(key=lambda x: -x["abs_err"])
    return out[:k]


def load_human_raw(repo: Path) -> Dict[str, Dict[str, Any]]:
    path = repo / "data" / "human" / "mem_enc_exp1.jsonl"
    by_id: Dict[str, Dict[str, Any]] = {}
    for row in read_jsonl(path):
        scores = [float(x) for x in (row.get("human_results") or [])]
        sid = str(row.get("sample_id"))
        by_id[sid] = {
            "sample_id": sid,
            "sentence": row.get("sentence"),
            "human_results": scores,
            "human_mean": sum(scores) / len(scores) if scores else None,
            "human_std": _std(scores),
            "human_range": (max(scores) - min(scores)) if scores else None,
            "human_n": len(scores),
            "pct_extreme": (
                sum(1 for x in scores if x in (1.0, 7.0)) / len(scores) if scores else None
            ),
        }
    return by_id


def disagreement_table(
    runs: Sequence[Dict[str, Any]],
    human_raw: Dict[str, Dict[str, Any]],
    *,
    top_k_human: int = 15,
    modes: Sequence[str] = ("ORIG", "T"),
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Return (high-disagreement sentence stats, per-run dispersion rows)."""
    human_ranked = sorted(
        human_raw.values(),
        key=lambda x: (-(x["human_std"] or -1), -(x["human_range"] or -1)),
    )
    high = human_ranked[:top_k_human]
    high_ids = {h["sample_id"] for h in high}

    sentence_rows = []
    for h in high:
        sentence_rows.append(
            {
                "sample_id": h["sample_id"],
                "sentence": h["sentence"],
                "condition": parse_sample_id(h["sample_id"])[1],
                "human_mean": h["human_mean"],
                "human_std": h["human_std"],
                "human_range": h["human_range"],
                "pct_extreme": h["pct_extreme"],
                "human_n": h["human_n"],
            }
        )

    disp_rows: List[Dict[str, Any]] = []
    for r in runs:
        if r["mode"] not in modes:
            continue
        by_sid = {str(x.get("sample_id")): x for x in r["rows"]}
        human_stds: List[float] = []
        model_stds: List[float] = []
        collapse = 0
        n_high = 0
        for sid in high_ids:
            h = human_raw[sid]
            row = by_sid.get(sid)
            if not row:
                continue
            ms = [float(x) for x in (row.get("model_scores") or []) if x is not None]
            mstd = _std(ms)
            mrange = (max(ms) - min(ms)) if ms else None
            n_high += 1
            if h["human_std"] is not None and mstd is not None:
                human_stds.append(float(h["human_std"]))
                model_stds.append(float(mstd))
                # collapse: model much tighter than human
                if mstd < 0.5 * float(h["human_std"]):
                    collapse += 1
            disp_rows.append(
                {
                    "model_id": r["model_id"],
                    "mode": r["mode"],
                    "sample_id": sid,
                    "human_std": h["human_std"],
                    "human_range": h["human_range"],
                    "model_std": mstd,
                    "model_range": mrange,
                    "model_mean": row.get("model_mean"),
                    "human_mean": h["human_mean"],
                    "n_model_samples": len(ms),
                }
            )
        disp_rows.append(
            {
                "model_id": r["model_id"],
                "mode": r["mode"],
                "sample_id": "__SUMMARY__",
                "human_std": None,
                "human_range": None,
                "model_std": None,
                "model_range": None,
                "model_mean": None,
                "human_mean": None,
                "n_model_samples": None,
                "corr_human_model_std": _pearson(human_stds, model_stds),
                "collapse_rate_on_high_disagreement": (collapse / n_high) if n_high else None,
                "n_high": n_high,
            }
        )
    return sentence_rows, disp_rows


def dispersion_stats_for_run(
    run: Dict[str, Any],
    human_raw: Dict[str, Dict[str, Any]],
) -> Dict[str, Optional[float]]:
    """Mean human/model std and ratio across all sentences in a run."""
    human_stds: List[float] = []
    model_stds: List[float] = []
    ratios: List[float] = []
    for row in run["rows"]:
        sid = str(row.get("sample_id"))
        h = human_raw.get(sid)
        if not h:
            continue
        ms = [float(x) for x in (row.get("model_scores") or []) if x is not None]
        mstd = _std(ms)
        hstd = h.get("human_std")
        if hstd is not None:
            human_stds.append(float(hstd))
        if mstd is not None:
            model_stds.append(float(mstd))
        if hstd is not None and mstd is not None and float(hstd) > 0:
            ratios.append(float(mstd) / float(hstd))
    return {
        "mean_human_std": sum(human_stds) / len(human_stds) if human_stds else None,
        "mean_model_std": sum(model_stds) / len(model_stds) if model_stds else None,
        "mean_std_ratio": sum(ratios) / len(ratios) if ratios else None,
    }


def dispersion_summary_rows(disp_rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [d for d in disp_rows if d.get("sample_id") == "__SUMMARY__"]


def mean_model_std_on_sentences(
    disp_rows: Sequence[Dict[str, Any]],
    *,
    model_id: str,
    mode: str,
    sample_ids: Sequence[str],
) -> Optional[float]:
    sids = set(sample_ids)
    vals = [
        float(d["model_std"])
        for d in disp_rows
        if d.get("sample_id") in sids
        and d.get("model_id") == model_id
        and d.get("mode") == mode
        and d.get("model_std") is not None
    ]
    return sum(vals) / len(vals) if vals else None


def _scale_model_weights(scores: Sequence[float], *, target_n: int = 20) -> List[float]:
    """Scale histogram mass to ``target_n`` (e.g. 15 runs → each weight 20/15)."""
    n = len(scores)
    if n <= 0:
        return []
    w = float(target_n) / float(n)
    return [w] * n


def _draw_disagreement_panel(
    ax: Any,
    *,
    human_scores: Sequence[float],
    model_scores: Sequence[float],
    bins: Sequence[float],
    target_n: int = 20,
) -> int:
    """Overlay human + model hist as % of each group. Returns raw model n."""
    del target_n  # % already normalizes; keep arg for API compat
    n_human = len(human_scores)
    n_model = len(model_scores)
    if n_human:
        ax.hist(
            list(human_scores),
            bins=list(bins),
            weights=[100.0 / n_human] * n_human,
            alpha=0.55,
            label=f"human n={n_human}",
            color="#4C78A8",
        )
    if model_scores:
        ax.hist(
            list(model_scores),
            bins=list(bins),
            weights=[100.0 / n_model] * n_model,
            alpha=0.55,
            label=f"model n={n_model}",
            color="#F58518",
        )
    ax.set_xlim(0.5, 7.5)
    ax.set_xticks(range(1, 8))
    ax.set_ylim(0, 100)
    ax.set_xlabel("score 1–7", fontsize=8)
    ax.set_ylabel("%", fontsize=8)
    ax.legend(fontsize=7, loc="upper right")
    return n_model


def plot_disagreement_histograms(
    sent_rows: Sequence[Dict[str, Any]],
    human_raw: Dict[str, Dict[str, Any]],
    case_runs: Sequence[Dict[str, Any]],
    out_path: Path,
    *,
    max_sentences: int = 3,
    title: Optional[str] = None,
    target_n: int = 20,
    also_per_panel: bool = True,
) -> List[Path]:
    """Grid + optional per-panel PNGs. Model hist scaled to ``target_n`` if n≠target_n.

    Chart shows only histogram + score 1–7 + human/model n (no sample_id on plot).
    Filenames still include sample_id for lookup.
    """
    import matplotlib.pyplot as plt

    cases = list(sent_rows[:max_sentences])
    runs = list(case_runs)
    written: List[Path] = []
    if not cases or not runs:
        return written

    bins = [i + 0.5 for i in range(0, 8)]
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    stem = out_path.stem
    if stem.endswith("_case_histograms"):
        per_dir = out_path.parent / f"{stem[: -len('_case_histograms')]}_histograms"
    else:
        per_dir = out_path.parent / f"{stem}_panels"
    if also_per_panel:
        per_dir.mkdir(parents=True, exist_ok=True)

    nrows = len(cases)
    ncols = len(runs)
    fig, axes = plt.subplots(nrows, ncols, figsize=(3.8 * ncols, 3.2 * nrows), squeeze=False)

    for i, hrow in enumerate(cases):
        sid = str(hrow["sample_id"])
        human_scores = list(human_raw[sid]["human_results"])
        for j, run in enumerate(runs):
            ax = axes[i][j]
            row = next((x for x in run["rows"] if str(x.get("sample_id")) == sid), None)
            model_scores = (
                [float(x) for x in (row.get("model_scores") or []) if x is not None] if row else []
            )
            short = str(run["model_id"]).split("/")[-1]
            mode = str(run["mode"])
            _draw_disagreement_panel(
                ax,
                human_scores=human_scores,
                model_scores=model_scores,
                bins=bins,
                target_n=target_n,
            )

            if also_per_panel:
                fig1, ax1 = plt.subplots(figsize=(4.2, 3.2))
                _draw_disagreement_panel(
                    ax1,
                    human_scores=human_scores,
                    model_scores=model_scores,
                    bins=bins,
                    target_n=target_n,
                )
                fig1.tight_layout()
                safe_model = short.replace("/", "_")
                panel_path = per_dir / f"{sid}__{safe_model}_{mode}.png"
                fig1.savefig(panel_path, dpi=150, bbox_inches="tight")
                plt.close(fig1)
                written.append(panel_path)

    if title:
        fig.suptitle(title, fontsize=10)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    written.insert(0, out_path)
    return written


def schema_deltas(runs: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_mm: Dict[Tuple[str, str], Dict[str, Any]] = {(r["model_id"], r["mode"]): r for r in runs}
    models = sorted({r["model_id"] for r in runs})
    out: List[Dict[str, Any]] = []
    pairs = [("S", "ORIG"), ("ST", "T"), ("ST", "ORIG"), ("T", "ORIG")]
    for model in models:
        for a, b in pairs:
            ra, rb = by_mm.get((model, a)), by_mm.get((model, b))
            if not ra or not rb:
                continue
            out.append(
                {
                    "model_id": model,
                    "contrast": f"{a}-{b}",
                    "delta_pearson": (ra["pearson_r"] or 0) - (rb["pearson_r"] or 0),
                    "delta_mae": (ra["mae"] or 0) - (rb["mae"] or 0),
                    f"{a}_pearson": ra["pearson_r"],
                    f"{b}_pearson": rb["pearson_r"],
                    f"{a}_mae": ra["mae"],
                    f"{b}_mae": rb["mae"],
                    f"{a}_parse_fail": ra["parse_fail_rate"],
                    f"{b}_parse_fail": rb["parse_fail_rate"],
                }
            )
    return out


def load_ready_gpt4(repo: Path) -> List[Dict[str, Any]]:
    path = repo / "data" / "ready" / "mem_enc_human_and_gpt.jsonl"
    return read_jsonl(path)


def paper_gpt4_metrics(ready_rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    human = [float(r["human_mean"]) for r in ready_rows if r.get("human_mean") is not None and r.get("gpt4_mean") is not None]
    gpt4 = [float(r["gpt4_mean"]) for r in ready_rows if r.get("human_mean") is not None and r.get("gpt4_mean") is not None]
    return {
        "model_id": "gpt-4 (paper)",
        "mode": "ORIG*",
        "n": len(gpt4),
        "pearson_r": _pearson(human, gpt4),
        "mae": _mae(human, gpt4),
        "rmse": math.sqrt(sum((h - m) ** 2 for h, m in zip(human, gpt4)) / len(gpt4)) if gpt4 else None,
        "note": "from data/ready gpt4_mean; not openai/gpt-4.1-mini",
    }


def paper_gpt4_by_condition(ready_rows: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    buckets: Dict[str, List[Tuple[float, float]]] = defaultdict(list)
    for r in ready_rows:
        _, cond = parse_sample_id(str(r.get("sample_id") or ""))
        if not cond or r.get("human_mean") is None or r.get("gpt4_mean") is None:
            continue
        buckets[cond].append((float(r["human_mean"]), float(r["gpt4_mean"])))
    out = {}
    for cond in CONDS:
        pairs = buckets.get(cond) or []
        h = [p[0] for p in pairs]
        m = [p[1] for p in pairs]
        out[cond] = {"n": len(pairs), "pearson_r": _pearson(h, m), "mae": _mae(h, m)}
    return out


def calibration_stats(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    pairs = [
        (float(r["human_mean"]), float(r["model_mean"]))
        for r in rows
        if r.get("human_mean") is not None and r.get("model_mean") is not None
    ]
    if len(pairs) < 2:
        return {"n": len(pairs), "bias": None, "slope": None, "intercept": None}
    hs = [p[0] for p in pairs]
    ms = [p[1] for p in pairs]
    bias = sum(m - h for h, m in pairs) / len(pairs)
    # simple OLS: model ~ a + b * human
    mx = sum(hs) / len(hs)
    my = sum(ms) / len(ms)
    num = sum((x - mx) * (y - my) for x, y in zip(hs, ms))
    den = sum((x - mx) ** 2 for x in hs)
    slope = (num / den) if den else None
    intercept = (my - slope * mx) if slope is not None else None
    return {"n": len(pairs), "bias_model_minus_human": bias, "slope": slope, "intercept": intercept}


def paradox_vs_baseline(
    runs: Sequence[Dict[str, Any]],
    baseline_model: str,
    baseline_mode: str = "ORIG",
    *,
    modes: Sequence[str] = ("ORIG", "T"),
) -> List[Dict[str, Any]]:
    """Compare each run to a baseline on Pearson r, MAE, and calibration."""
    baseline: Dict[str, Any] | None = None
    for r in runs:
        if r["model_id"] == baseline_model and r["mode"] == baseline_mode:
            baseline = r
            break
    if not baseline:
        return []

    base_r = baseline.get("pearson_r")
    base_mae = baseline.get("mae")
    base_cal = calibration_stats(baseline["rows"])
    out: List[Dict[str, Any]] = []

    for r in runs:
        if r["mode"] not in modes:
            continue
        cal = calibration_stats(r["rows"])
        pr = r.get("pearson_r")
        mae = r.get("mae")
        out.append(
            {
                "model_id": r["model_id"],
                "mode": r["mode"],
                "pearson_r": pr,
                "mae": mae,
                "delta_r": (pr - base_r) if pr is not None and base_r is not None else None,
                "delta_mae": (mae - base_mae) if mae is not None and base_mae is not None else None,
                "bias_model_minus_human": cal.get("bias_model_minus_human"),
                "slope": cal.get("slope"),
                "beats_baseline": (pr or -1) > (base_r or -1),
                "baseline_model": baseline_model,
                "baseline_mode": baseline_mode,
                "baseline_pearson_r": base_r,
                "baseline_mae": base_mae,
                "baseline_bias": base_cal.get("bias_model_minus_human"),
                "baseline_slope": base_cal.get("slope"),
            }
        )
    out.sort(key=lambda x: (-(x["pearson_r"] or -1), x["model_id"], x["mode"]))
    return out


def condition_delta_vs_baseline(
    run: Dict[str, Any],
    baseline_run: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Per-condition Pearson r / MAE delta vs baseline run."""
    by_c = metrics_by_condition(run["rows"])
    base_by_c = metrics_by_condition(baseline_run["rows"])
    out: List[Dict[str, Any]] = []
    for cond in CONDS:
        m = by_c.get(cond) or {}
        b = base_by_c.get(cond) or {}
        r_m, r_b = m.get("pearson_r"), b.get("pearson_r")
        mae_m, mae_b = m.get("mae"), b.get("mae")
        out.append(
            {
                "model_id": run["model_id"],
                "mode": run["mode"],
                "baseline_model": baseline_run["model_id"],
                "baseline_mode": baseline_run["mode"],
                "condition": cond,
                "n": m.get("n"),
                "pearson_r": r_m,
                "baseline_pearson_r": r_b,
                "delta_r": (r_m - r_b) if r_m is not None and r_b is not None else None,
                "mae": mae_m,
                "baseline_mae": mae_b,
                "delta_mae": (mae_m - mae_b) if mae_m is not None and mae_b is not None else None,
            }
        )
    return out


def head_to_head_cases(
    challenger_run: Dict[str, Any],
    baseline_run: Dict[str, Any],
    *,
    k: int = 5,
    min_advantage: float = 0.5,
) -> List[Dict[str, Any]]:
    """Sentences where baseline is closer to human than challenger."""
    base_by = {str(r.get("sample_id")): r for r in baseline_run["rows"]}
    scored: List[Dict[str, Any]] = []
    for row in challenger_run["rows"]:
        sid = str(row.get("sample_id"))
        base = base_by.get(sid)
        if not base:
            continue
        hm = row.get("human_mean")
        cm = row.get("model_mean")
        bm = base.get("model_mean")
        if hm is None or cm is None or bm is None:
            continue
        hm_f, cm_f, bm_f = float(hm), float(cm), float(bm)
        err_c = abs(cm_f - hm_f)
        err_b = abs(bm_f - hm_f)
        advantage = err_c - err_b
        if advantage < min_advantage:
            continue
        _, cond = parse_sample_id(sid)
        scored.append(
            {
                "challenger_model": challenger_run["model_id"],
                "challenger_mode": challenger_run["mode"],
                "baseline_model": baseline_run["model_id"],
                "baseline_mode": baseline_run["mode"],
                "sample_id": sid,
                "condition": cond,
                "sentence": row.get("sentence"),
                "human_mean": hm_f,
                "challenger_mean": cm_f,
                "baseline_mean": bm_f,
                "challenger_abs_err": err_c,
                "baseline_abs_err": err_b,
                "err_advantage_baseline": advantage,
            }
        )
    scored.sort(key=lambda x: -x["err_advantage_baseline"])
    return scored[:k]


def thinking_deltas(runs: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """T − ORIG delta for models that have both modes."""
    by_mm: Dict[Tuple[str, str], Dict[str, Any]] = {(r["model_id"], r["mode"]): r for r in runs}
    models = sorted({r["model_id"] for r in runs})
    out: List[Dict[str, Any]] = []
    for model in models:
        orig = by_mm.get((model, "ORIG"))
        t_run = by_mm.get((model, "T"))
        if not orig or not t_run:
            continue
        o_r, t_r = orig.get("pearson_r"), t_run.get("pearson_r")
        o_mae, t_mae = orig.get("mae"), t_run.get("mae")
        out.append(
            {
                "model_id": model,
                "orig_pearson_r": o_r,
                "t_pearson_r": t_r,
                "delta_r": (t_r - o_r) if o_r is not None and t_r is not None else None,
                "orig_mae": o_mae,
                "t_mae": t_mae,
                "delta_mae": (t_mae - o_mae) if o_mae is not None and t_mae is not None else None,
            }
        )
    out.sort(key=lambda x: -(x.get("delta_r") or -999))
    return out


def ranking_with_gpt4(
    runs: Sequence[Dict[str, Any]],
    ready_rows: Sequence[Dict[str, Any]],
    *,
    modes: Sequence[str] = ("ORIG", "T"),
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    g4 = paper_gpt4_metrics(ready_rows)
    out.append(
        {
            "model_id": g4["model_id"],
            "mode": g4["mode"],
            "pearson_r": g4["pearson_r"],
            "mae": g4["mae"],
            "rmse": g4["rmse"],
            "bias_model_minus_human": None,
            "slope": None,
            "note": g4["note"],
        }
    )
    # also calibration for paper gpt4
    fake_rows = [
        {"human_mean": r["human_mean"], "model_mean": r["gpt4_mean"]}
        for r in ready_rows
        if r.get("gpt4_mean") is not None
    ]
    cal4 = calibration_stats(fake_rows)
    out[0]["bias_model_minus_human"] = cal4.get("bias_model_minus_human")
    out[0]["slope"] = cal4.get("slope")

    for r in runs:
        if r["mode"] not in modes:
            continue
        cal = calibration_stats(r["rows"])
        out.append(
            {
                "model_id": r["model_id"],
                "mode": r["mode"],
                "pearson_r": r["pearson_r"],
                "mae": r["mae"],
                "rmse": r["rmse"],
                "bias_model_minus_human": cal.get("bias_model_minus_human"),
                "slope": cal.get("slope"),
                "note": "",
            }
        )
    out.sort(key=lambda x: (-(x["pearson_r"] or -1), x["model_id"], x["mode"]))
    return out


def compare_to_paper_gpt4(
    runs: Sequence[Dict[str, Any]],
    ready_rows: Sequence[Dict[str, Any]],
    *,
    compare_models: Optional[Sequence[str]] = None,
    mode: str = "ORIG",
) -> List[Dict[str, Any]]:
    """Compare zoo runs vs gpt-4 (paper) on r, MAE, bias."""
    rank = ranking_with_gpt4(runs, ready_rows, modes=(mode, "T"))
    paper = next((x for x in rank if x["model_id"] == "gpt-4 (paper)"), None)
    if not paper:
        return []
    pr = paper.get("pearson_r")
    pm = paper.get("mae")
    pb = paper.get("bias_model_minus_human")
    ps = paper.get("slope")
    out: List[Dict[str, Any]] = []
    for row in rank:
        if row["model_id"] == "gpt-4 (paper)":
            continue
        if row["mode"] != mode:
            continue
        if compare_models is not None and row["model_id"] not in compare_models:
            continue
        r_r = row.get("pearson_r")
        r_m = row.get("mae")
        r_b = row.get("bias_model_minus_human")
        out.append(
            {
                "model_id": row["model_id"],
                "mode": row["mode"],
                "pearson_r": r_r,
                "mae": r_m,
                "bias_model_minus_human": r_b,
                "slope": row.get("slope"),
                "paper_pearson_r": pr,
                "paper_mae": pm,
                "paper_bias": pb,
                "paper_slope": ps,
                "delta_r_vs_paper": (r_r - pr) if r_r is not None and pr is not None else None,
                "delta_mae_vs_paper": (r_m - pm) if r_m is not None and pm is not None else None,
                "delta_bias_vs_paper": (r_b - pb) if r_b is not None and pb is not None else None,
            }
        )
    out.sort(key=lambda x: (-(x["pearson_r"] or -1), x["model_id"]))
    return out


def residual_overlap_vs_gpt4(
    runs: Sequence[Dict[str, Any]],
    ready_rows: Sequence[Dict[str, Any]],
    *,
    mode: str = "ORIG",
    err_thresh: float = 1.0,
) -> List[Dict[str, Any]]:
    ready_by = {str(r["sample_id"]): r for r in ready_rows}
    out = []
    for r in runs:
        if r["mode"] != mode:
            continue
        gpt4_better = model_better = both_bad = 0
        for row in r["rows"]:
            sid = str(row.get("sample_id"))
            rr = ready_by.get(sid)
            if not rr or row.get("model_mean") is None or rr.get("gpt4_mean") is None:
                continue
            hm = float(row["human_mean"])
            e_m = abs(float(row["model_mean"]) - hm)
            e_g = abs(float(rr["gpt4_mean"]) - hm)
            if e_g < err_thresh <= e_m:
                gpt4_better += 1
            elif e_m < err_thresh <= e_g:
                model_better += 1
            elif e_g >= err_thresh and e_m >= err_thresh:
                both_bad += 1
        out.append(
            {
                "model_id": r["model_id"],
                "mode": mode,
                "gpt4_ok_model_bad": gpt4_better,
                "model_ok_gpt4_bad": model_better,
                "both_bad": both_bad,
                "err_thresh": err_thresh,
            }
        )
    return out


def write_csv(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    import csv

    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    # union keys preserving order of first row then extras
    keys: List[str] = list(rows[0].keys())
    for r in rows:
        for k in r.keys():
            if k not in keys:
                keys.append(k)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)


REPORT_HEADER = """# Báo cáo phân tích (mem_enc)

> Narrative chung cho Mục 1–7. Script `run_muc*.py` upsert từng section `## Mục N — …`.
> Artifact CSV/JSON nằm cùng thư mục `results/analysis/`.

"""


def upsert_report_section(report_path: Path, heading: str, body: str) -> None:
    """Replace or append a `## {heading}` section in report.md.

    ``heading`` is the title without ``## `` (e.g. ``Mục 1 — Kết quả tổng thể``).
    ``body`` is markdown under that heading (no leading ``##`` line).
    """
    report_path.parent.mkdir(parents=True, exist_ok=True)
    section = f"## {heading}\n\n{body.strip()}\n"
    if not report_path.exists():
        report_path.write_text(REPORT_HEADER + section + "\n", encoding="utf-8")
        return

    text = report_path.read_text(encoding="utf-8")
    if not text.startswith("# "):
        text = REPORT_HEADER + text.lstrip()

    marker = f"## {heading}"
    start = text.find(marker)
    if start < 0:
        report_path.write_text(text.rstrip() + "\n\n" + section + "\n", encoding="utf-8")
        return

    # find next ## at beginning of line after start
    rest = text[start + len(marker) :]
    next_m = re.search(r"\n## ", rest)
    if next_m:
        end = start + len(marker) + next_m.start()
        new_text = text[:start] + section + text[end:].lstrip("\n")
    else:
        new_text = text[:start] + section
    report_path.write_text(new_text.rstrip() + "\n", encoding="utf-8")


def run_full_analysis(repo: Path) -> Dict[str, Any]:
    """Generate all checklist artifacts under results/analysis/."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_dir = repo / "results" / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    runs = load_runs(repo, min_n=50, exclude_smoke=True)
    ready = load_ready_gpt4(repo)
    human_raw = load_human_raw(repo)

    # A
    lb = leaderboard_rows(runs)
    write_csv(out_dir / "A_leaderboard.csv", lb)
    cov = coverage_matrix(runs)
    write_json(out_dir / "A_coverage.json", cov)

    # B
    cond_tbl = condition_table(runs, modes=("ORIG", "T"))
    write_csv(out_dir / "B_by_condition.csv", cond_tbl)
    residuals = top_residuals(runs, k=25, modes=("ORIG", "T"))
    write_csv(out_dir / "B_top_residuals.csv", residuals)

    # heatmap pearson ORIG+T
    models = sorted({r["model_id"] for r in runs if r["mode"] in ("ORIG", "T")})
    # prefer T if both, else ORIG for heatmap rows labeled model@mode
    heat_rows = [r for r in runs if r["mode"] in ("ORIG", "T")]
    labels = [f"{r['model_id']} | {r['mode']}" for r in heat_rows]
    mat = []
    for r in heat_rows:
        by_c = metrics_by_condition(r["rows"])
        mat.append([by_c[c]["pearson_r"] if by_c[c]["pearson_r"] is not None else float("nan") for c in CONDS])

    fig, ax = plt.subplots(figsize=(10, max(4, 0.35 * len(labels) + 1)))
    import numpy as np

    arr = np.array(mat, dtype=float)
    im = ax.imshow(arr, aspect="auto", vmin=0, vmax=1, cmap="viridis")
    ax.set_xticks(range(len(CONDS)))
    ax.set_xticklabels(CONDS)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_title("Pearson r by linguistic condition (ORIG / T)")
    fig.colorbar(im, ax=ax, fraction=0.02)
    fig.tight_layout()
    fig.savefig(out_dir / "B_condition_heatmap.png", dpi=150)
    plt.close(fig)

    # mean MAE by condition across ORIG/T
    mae_by_cond = {c: [] for c in CONDS}
    for r in heat_rows:
        by_c = metrics_by_condition(r["rows"])
        for c in CONDS:
            if by_c[c]["mae"] is not None:
                mae_by_cond[c].append(by_c[c]["mae"])
    cond_rank = [
        {"condition": c, "mean_mae": sum(v) / len(v) if v else None, "n_runs": len(v)}
        for c, v in mae_by_cond.items()
    ]
    cond_rank.sort(key=lambda x: x["mean_mae"] if x["mean_mae"] is not None else 9e9)
    write_csv(out_dir / "B_condition_rank_mae.csv", cond_rank)

    # C
    sent_rows, disp_rows = disagreement_table(runs, human_raw, top_k_human=15, modes=("ORIG", "T"))
    write_csv(out_dir / "C_high_disagreement_sentences.csv", sent_rows)
    write_csv(out_dir / "C_dispersion.csv", disp_rows)
    summaries = dispersion_summary_rows(disp_rows)
    write_csv(out_dir / "C_dispersion_summary.csv", summaries)

    best_orig = next(
        r for r in sorted(runs, key=lambda x: -(x["pearson_r"] or -1)) if r["mode"] == "ORIG"
    )
    plot_disagreement_histograms(
        sent_rows,
        human_raw,
        [best_orig],
        out_dir / "C_case_histograms.png",
        max_sentences=3,
        title=f"High-disagreement: human vs {best_orig['model_id']} ORIG samples",
    )

    # D
    deltas = schema_deltas(runs)
    write_csv(out_dir / "D_schema_deltas.csv", deltas)

    # E
    rank = ranking_with_gpt4(runs, ready, modes=("ORIG", "T"))
    write_csv(out_dir / "E_ranking_with_gpt4_paper.csv", rank)
    g4_cond = paper_gpt4_by_condition(ready)
    write_json(out_dir / "E_gpt4_paper_by_condition.json", g4_cond)
    overlap = residual_overlap_vs_gpt4(runs, ready, mode="ORIG", err_thresh=1.0)
    write_csv(out_dir / "E_residual_overlap_vs_gpt4.csv", overlap)

    # bar chart pearson ORIG + gpt4 paper
    orig_rank = [x for x in rank if x["mode"] in ("ORIG", "ORIG*")]
    fig, ax = plt.subplots(figsize=(10, 5))
    names = [f"{x['model_id']}" for x in orig_rank]
    vals = [x["pearson_r"] or 0 for x in orig_rank]
    colors = ["#E45756" if "paper" in x["model_id"] else "#4C78A8" for x in orig_rank]
    ax.barh(range(len(names)), vals, color=colors)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Pearson r vs human")
    ax.set_title("ORIG human-likeness (+ GPT-4 paper)")
    fig.tight_layout()
    fig.savefig(out_dir / "E_orig_ranking_with_gpt4.png", dpi=150)
    plt.close(fig)

    # F cost table
    cost_rows = []
    for r in runs:
        if r["mode"] not in ("ORIG", "T"):
            continue
        cost_rows.append(
            {
                "model_id": r["model_id"],
                "mode": r["mode"],
                "pearson_r": r["pearson_r"],
                "mean_cost_per_sentence_usd": r["mean_cost_per_sentence_usd"],
                "cost_ratio_vs_human": r["cost_ratio_vs_human"],
                "est_cost_per_hour_usd": r["est_cost_per_hour_usd"],
                "mean_latency_s_per_call": r["mean_latency_s_per_call"],
                "pricing_source": r["pricing_source"],
                "cheaper_than_human": (r["cost_ratio_vs_human"] or 9) < 1.0,
            }
        )
    write_csv(out_dir / "F_cost_table.csv", cost_rows)

    fig, ax = plt.subplots(figsize=(8, 6))
    for r in cost_rows:
        ax.scatter(
            r["mean_cost_per_sentence_usd"],
            r["pearson_r"],
            s=60,
            alpha=0.85,
        )
        ax.annotate(
            f"{r['model_id'].split('/')[-1]}|{r['mode']}",
            (r["mean_cost_per_sentence_usd"], r["pearson_r"] or 0),
            fontsize=7,
            alpha=0.8,
        )
    ax.set_xlabel("$ / sentence (post-hoc)")
    ax.set_ylabel("Pearson r")
    ax.set_title("Pareto: quality vs cost (ORIG/T)")
    ax.set_xscale("log")
    fig.tight_layout()
    fig.savefig(out_dir / "F_pareto_quality_cost.png", dpi=150)
    plt.close(fig)

    findings = {
        "n_runs": len(runs),
        "excluded_smoke": True,
        "top_overall": lb[0] if lb else None,
        "best_orig": next((x for x in rank if x["mode"] == "ORIG"), None),
        "gpt4_paper": next((x for x in rank if "paper" in x["model_id"]), None),
        "condition_easiest_mae": cond_rank[0] if cond_rank else None,
        "condition_hardest_mae": cond_rank[-1] if cond_rank else None,
        "schema_note": "See D_schema_deltas.csv; negative delta_pearson for S-ORIG means schema hurts human-likeness.",
        "coverage": cov,
    }
    write_json(out_dir / "findings_summary.json", findings)

    md_lines = [
        "# Analysis findings (auto)",
        "",
        f"- Runs (n≥50): **{len(runs)}**",
        f"- Top by Pearson: `{findings['top_overall']['model_id'] if findings['top_overall'] else None}` / `{findings['top_overall']['mode'] if findings['top_overall'] else None}` (r={findings['top_overall']['pearson_r'] if findings['top_overall'] else None})",
        f"- Best ORIG: `{findings['best_orig']}`",
        f"- GPT-4 paper: `{findings['gpt4_paper']}`",
        f"- Condition lowest mean MAE: `{findings['condition_easiest_mae']}`",
        f"- Condition highest mean MAE: `{findings['condition_hardest_mae']}`",
        "",
        "## Files",
        "",
    ]
    for p in sorted(out_dir.iterdir()):
        if p.name.startswith("."):
            continue
        md_lines.append(f"- `{p.name}`")
    (out_dir / "README.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    return {"out_dir": str(out_dir), "findings": findings, "n_runs": len(runs)}
