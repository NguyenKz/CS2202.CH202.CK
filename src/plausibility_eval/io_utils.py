"""I/O helpers: paths, jsonl, configs, secrets."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


def find_repo_root(start: Optional[Path] = None) -> Path:
    """Locate `doan/` root (has configs/ + data/)."""
    p = (start or Path.cwd()).resolve()
    for cand in [p, *p.parents]:
        if (cand / "configs").is_dir() and (cand / "data").is_dir():
            return cand
        if (cand / "doan" / "configs").is_dir():
            return cand / "doan"
    # fallback: this file lives in doan/src/plausibility_eval/
    here = Path(__file__).resolve().parents[2]
    return here


def load_yaml(path: Path) -> Dict[str, Any]:
    if yaml is None:
        raise ImportError("PyYAML required: pip install pyyaml")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def model_dirname(model: str) -> str:
    """Filesystem-safe model folder name."""
    s = model.strip().replace("/", "__").replace(" ", "_")
    s = re.sub(r"[^A-Za-z0-9._\-__]+", "_", s)
    return s


def results_dir(repo: Path, model: str, mode: str) -> Path:
    return repo / "results" / model_dirname(model) / mode


def get_secret(name: str, fallback: str = "") -> str:
    """Env → Colab userdata → fallback (widget/notebook cell)."""
    val = os.environ.get(name, "")
    if val:
        return val
    try:
        from google.colab import userdata  # type: ignore

        got = userdata.get(name)
        if got:
            return str(got)
    except Exception:
        pass
    return fallback or ""
