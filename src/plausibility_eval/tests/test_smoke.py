"""Minimal tests (no network). Run: cd doan && PYTHONPATH=src python -m pytest src/plausibility_eval/tests -q"""

from plausibility_eval.modes import validate_mode
from plausibility_eval.parse import parse_prediction, parse_score_from_output
from plausibility_eval.cost import tokens_to_usd, lookup_price


def test_modes():
    assert validate_mode("ORIG") == "ORIG"
    assert validate_mode("ST−E") == "ST-E"


def test_parse():
    assert parse_prediction("The naturalness score is 4 (maybe)") == 4
    s, ok = parse_score_from_output('{"score": 7, "reason": "ok"}', expect_schema=True)
    assert ok and s == 7


def test_row_complete_and_resume_helpers(tmp_path):
    from plausibility_eval.run_eval import (
        _call_path,
        _existing_call_count,
        _row_complete,
        _safe_sample_id,
    )

    assert _safe_sample_id("s1_all") == "s1_all"
    row = {"usage": {"n_api_calls": 20}, "call_refs": []}
    assert _row_complete(row, 20)
    assert not _row_complete({"usage": {"n_api_calls": 3}}, 20)

    calls = tmp_path / "calls"
    calls.mkdir()
    _call_path(calls, "s1_all", 0).write_text("{}", encoding="utf-8")
    _call_path(calls, "s1_all", 1).write_text("{}", encoding="utf-8")
    assert _existing_call_count(calls, "s1_all", 20) == 2


def test_cost_fold_reasoning():
    price = {"input_per_1m": 1.0, "output_per_1m": 2.0, "reasoning_per_1m": None, "source": "t"}
    c = tokens_to_usd({"input_tokens": 1_000_000, "output_tokens": 0, "reasoning_tokens": 1_000_000}, price)
    assert abs(c["input"] - 1.0) < 1e-9
    assert abs(c["output"] - 2.0) < 1e-9  # reasoning folded into output
