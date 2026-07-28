#!/usr/bin/env bash
# Xóa call JSON bị lỗi API (429 / response_raw.error) và gỡ sample đó khỏi scores.jsonl
# để resume chạy lại các call còn thiếu (call OK giữ nguyên).
#
# Usage:
#   bash scripts/purge_failed_calls.sh
#   bash scripts/purge_failed_calls.sh results/openai__gpt-5.6-sol/T
#   bash scripts/purge_failed_calls.sh results/openai__gpt-5.6-sol   # mọi MODE

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${1:-$ROOT/results}"

python3 - "$ROOT" "$TARGET" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

repo = Path(sys.argv[1])
target = Path(sys.argv[2]).expanduser()
if not target.is_absolute():
    target = (repo / target).resolve()
else:
    target = target.resolve()

if not target.exists():
    raise SystemExit(f"Not found: {target}")


def is_failed_call(payload: dict) -> bool:
    raw = payload.get("response_raw")
    if isinstance(raw, dict) and raw.get("error"):
        return True
    # legacy / alternate shapes
    if payload.get("trace_id", "").startswith("error-"):
        return True
    out = (payload.get("output_text") or "").strip()
    usage = payload.get("usage") or {}
    tokens = int(usage.get("input_tokens") or 0) + int(usage.get("output_tokens") or 0)
    if not out and tokens == 0 and payload.get("parse_ok") is False:
        # empty failed call without real model output
        err = ""
        if isinstance(raw, dict):
            err = str(raw.get("error") or "")
        if "429" in err or "Rate limit" in err or "error" in err.lower():
            return True
    return False


def mode_dirs(path: Path) -> list[Path]:
    if (path / "calls").is_dir():
        return [path]
    found: list[Path] = []
    for p in sorted(path.rglob("calls")):
        if p.is_dir():
            found.append(p.parent)
    return found


dirs = mode_dirs(target)
if not dirs:
    raise SystemExit(f"No results/*/MODE with calls/ under {target}")

total_del = 0
total_rows = 0
for mode_dir in dirs:
    calls_dir = mode_dir / "calls"
    scores_path = mode_dir / "scores.jsonl"
    deleted_files: list[Path] = []
    affected: set[str] = set()

    for path in sorted(calls_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not is_failed_call(payload):
            continue
        sid = str(payload.get("sample_id") or "")
        if sid:
            affected.add(sid)
        deleted_files.append(path)

    for path in deleted_files:
        path.unlink(missing_ok=True)

    removed_rows = 0
    if scores_path.exists() and affected:
        keep: list[dict] = []
        for line in scores_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            sid = str(row.get("sample_id") or "")
            if sid in affected:
                removed_rows += 1
                continue
            keep.append(row)
        with scores_path.open("w", encoding="utf-8") as f:
            for row in keep:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # stale aggregate — next eval/summary will refresh
    for name in ("metrics.json", "metrics_with_cost.json"):
        p = mode_dir / name
        if p.exists() and (deleted_files or removed_rows):
            p.unlink(missing_ok=True)

    rel = mode_dir.relative_to(repo) if mode_dir.is_relative_to(repo) else mode_dir
    print(f"{rel}: deleted_calls={len(deleted_files)} removed_score_rows={removed_rows} samples={sorted(affected)}")
    total_del += len(deleted_files)
    total_rows += removed_rows

print(f"DONE deleted_calls={total_del} removed_score_rows={total_rows}")
print("Resume eval để gọi lại các call còn thiếu (call OK giữ nguyên).")
PY
