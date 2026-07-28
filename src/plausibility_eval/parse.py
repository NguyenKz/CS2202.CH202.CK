"""Score parsing — paper free-text + JSON schema outputs."""

from __future__ import annotations

import json
import re
from typing import Any, Optional, Tuple


def parse_prediction(pred: str) -> Optional[int]:
    """Paper `parse_prediction`: first numeric token's first digit (1–7 expected)."""
    if pred is None:
        return None
    naturalness_score = None
    found_num = False
    for sentence in str(pred).split("\n"):
        if found_num:
            break
        for word in sentence.split(" "):
            cleaned = word.replace(".", "")
            if cleaned.isnumeric():
                naturalness_score = int(cleaned[0])
                found_num = True
                break
    if naturalness_score is not None and 1 <= naturalness_score <= 7:
        return naturalness_score
    return naturalness_score


def _clamp_score(value: Any) -> Optional[int]:
    try:
        n = int(float(value))
    except (TypeError, ValueError):
        return None
    if 1 <= n <= 7:
        return n
    return None


def parse_json_score(text: str) -> Optional[int]:
    if not text:
        return None
    text = text.strip()
    # Strip markdown fences
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        # try to find a JSON object substring
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            return None
        try:
            obj = json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    if isinstance(obj, dict):
        for key in ("score", "plausibility", "naturalness", "rating"):
            if key in obj:
                return _clamp_score(obj[key])
    return None


def parse_score_from_output(output_text: str, expect_schema: bool = False) -> Tuple[Optional[int], bool]:
    """Return (score, parse_ok). Prefer JSON when schema mode; else paper free-text."""
    if expect_schema:
        score = parse_json_score(output_text)
        if score is not None:
            return score, True
        # fallback free-text
        score = parse_prediction(output_text)
        return score, score is not None and 1 <= score <= 7
    score = parse_prediction(output_text)
    if score is not None and 1 <= score <= 7:
        return score, True
    # rare: model returned JSON anyway
    score = parse_json_score(output_text)
    return score, score is not None
