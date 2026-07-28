"""Ablation MODE → schema / thinking / examples flags."""

from __future__ import annotations

from typing import Dict, TypedDict


class ModeFlags(TypedDict):
    schema: bool
    thinking: bool
    examples: bool


MODE_FLAGS: Dict[str, ModeFlags] = {
    "ORIG": {"schema": False, "thinking": False, "examples": True},
    "S": {"schema": True, "thinking": False, "examples": True},
    "T": {"schema": False, "thinking": True, "examples": True},
    "ST": {"schema": True, "thinking": True, "examples": True},
    "ST-E": {"schema": True, "thinking": True, "examples": False},
}

# Accept paper-style dash variants
_ALIASES = {
    "ST−E": "ST-E",
    "ST–E": "ST-E",
    "STE": "ST-E",
    "ST_E": "ST-E",
}


def normalize_mode(mode: str) -> str:
    m = (mode or "").strip()
    m = _ALIASES.get(m, m)
    return m.upper() if m.upper() in MODE_FLAGS else m


def validate_mode(mode: str) -> str:
    m = normalize_mode(mode)
    if m not in MODE_FLAGS:
        raise ValueError(f"MODE must be one of {list(MODE_FLAGS)}; got {mode!r}")
    return m
