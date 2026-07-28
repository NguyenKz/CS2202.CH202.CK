"""Build paper-aligned chat prompts (via upstream prompts_getter when possible)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def _ensure_upstream_on_path(repo: Path) -> None:
    up = repo / "llm_pretesting"
    if up.is_dir() and str(up) not in sys.path:
        sys.path.insert(0, str(up))


# Fallback SYSTEM prompts (same text as paper prompts_getter)
SYSTEM_1 = """You will read sentences and judge how natural they sound.
You will need to judge, on a scale from 1 to 7, how natural/plausible the presented sentence sounds, and explain yourself.
All presented sentences will be grammatically correct.
Begin all your answers with "The naturalness score is"

Important: you are encouraged to use the whole scale."""

SYSTEM_2 = """You will read sentences and judge how natural they sound.
You will need to judge, on a scale from 1 to 7, how natural/plausible the presented sentence sounds, and explain yourself. 
All presented sentences will be grammatically correct.
Begin all your answers with "The naturalness score is"

Important: you are encouraged to use the whole scale.

Here are some examples:

EXAMPLES"""


def build_messages(
    sentence: str,
    *,
    repo: Path,
    prompt_name: str = "mem_enc",
    example_args: Optional[Dict[str, Any]] = None,
    add_examples: bool = True,
) -> List[Dict[str, str]]:
    example_args = example_args or {"num_ex": 3, "diff_sentence": "no"}
    _ensure_upstream_on_path(repo)
    try:
        from llm_pretest.prompts_getter import get_prompt

        return get_prompt("chat", prompt_name, example_args, sentence, add_examples)
    except Exception:
        # Minimal fallback without few-shots if upstream import fails
        if add_examples:
            content = SYSTEM_2.replace("EXAMPLES", "(examples unavailable — upstream import failed)")
        else:
            content = SYSTEM_1
        return [
            {"role": "system", "content": content},
            {"role": "user", "content": sentence},
        ]
