"""Web demo: score sentence plausibility (1–7) with gpt-5.6-luna."""

from __future__ import annotations

import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from plausibility_eval.client import ChatClient  # noqa: E402
from plausibility_eval.io_utils import read_jsonl  # noqa: E402
from plausibility_eval.parse import parse_score_from_output  # noqa: E402
from plausibility_eval.prompts import SYSTEM_1, build_messages  # noqa: E402

MODEL = os.environ.get("DEMO_MODEL", "gpt-5.6-luna")
BASE_URL = os.environ.get("DEMO_BASE_URL", "https://api.openai.com/v1")
# GPT-5.x realtime often only accepts default temperature=1 (paper closed was 1.5 via Batch).
TEMPERATURE = float(os.environ.get("DEMO_TEMPERATURE", "1.0"))
MAX_TOKENS_ORIG = int(os.environ.get("DEMO_MAX_TOKENS", "128"))
MAX_TOKENS_T = int(os.environ.get("DEMO_MAX_TOKENS_T", "1024"))
REASONING_EFFORT = os.environ.get("DEMO_REASONING_EFFORT", "medium")
MAX_SENTENCES = int(os.environ.get("DEMO_MAX_SENTENCES", "20"))
MAX_WORKERS = int(os.environ.get("DEMO_MAX_WORKERS", "4"))

STATIC = Path(__file__).resolve().parent / "static"
DATA_PATH = REPO / "data" / "ready" / "mem_enc_human_and_gpt.jsonl"

app = FastAPI(title="Plausibility demo", docs_url=None, redoc_url=None)


def _load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv(REPO / ".env")


def _token() -> str:
    if "openrouter.ai" in (BASE_URL or ""):
        return (
            os.environ.get("OPENROUTER_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or ""
        )
    return (
        os.environ.get("OPENAI_API_KEY")
        or os.environ.get("OPENROUTER_API_KEY")
        or ""
    )


def _example_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "sample_id": row.get("sample_id"),
        "sentence": (row.get("sentence") or "").strip(),
        "human_mean": round(float(row["human_mean"]), 2)
        if row.get("human_mean") is not None
        else None,
    }


def _load_examples() -> List[Dict[str, Any]]:
    # Always include one classic absurd sentence (paper-style coarse filter).
    picked: List[Dict[str, Any]] = [
        {
            "sample_id": None,
            "sentence": "The teacher scolded the shoe.",
            "human_mean": None,
        }
    ]
    seen = {picked[0]["sentence"]}
    if not DATA_PATH.is_file():
        return picked

    rows = read_jsonl(DATA_PATH)
    # High + low human_mean from mem_enc, plus a couple mid examples.
    ranked = sorted(
        (r for r in rows if r.get("sentence") and r.get("human_mean") is not None),
        key=lambda r: float(r["human_mean"]),
    )
    for row in (ranked[-1], ranked[0], ranked[len(ranked) // 2]):
        sent = (row.get("sentence") or "").strip()
        if sent and sent not in seen:
            picked.append(_example_row(row))
            seen.add(sent)
    return picked


EXAMPLES = _load_examples()
HUMAN_BY_SENTENCE = {
    (r.get("sentence") or "").strip(): r
    for r in (read_jsonl(DATA_PATH) if DATA_PATH.is_file() else [])
}


class ScoreRequest(BaseModel):
    """One sentence per line in `text` (or legacy single `sentence`)."""

    text: Optional[str] = Field(default=None, max_length=8000)
    sentence: Optional[str] = Field(default=None, max_length=500)
    thinking: bool = False


class SentenceResult(BaseModel):
    sentence: str
    score: Optional[int] = None
    explanation: str = ""
    thinking: Optional[str] = None
    human_mean: Optional[float] = None
    sample_id: Optional[str] = None
    latency_ms: int = 0
    error: Optional[str] = None


class ScoreResponse(BaseModel):
    model: str
    mode: str
    thinking: bool
    results: List[SentenceResult]


def _parse_sentences(req: ScoreRequest) -> List[str]:
    raw = req.text if req.text is not None else req.sentence
    if raw is None:
        return []
    out: List[str] = []
    seen = set()
    for line in str(raw).splitlines():
        sentence = " ".join(line.strip().split())
        if not sentence or sentence in seen:
            continue
        seen.add(sentence)
        out.append(sentence)
        if len(out) >= MAX_SENTENCES:
            break
    return out


def _extra_for_mode(thinking: bool) -> Dict[str, Any]:
    if thinking:
        return {"reasoning_effort": REASONING_EFFORT}
    return {"reasoning_effort": "none"}


def _human_meta(sentence: str) -> Tuple[Optional[float], Optional[str]]:
    human = HUMAN_BY_SENTENCE.get(sentence)
    if not human:
        return None, None
    human_mean = (
        round(float(human["human_mean"]), 2)
        if human.get("human_mean") is not None
        else None
    )
    return human_mean, human.get("sample_id")


def _messages_for_thinking(messages: List[Dict[str, str]], num_ex: int = 3) -> List[Dict[str, str]]:
    """Rewrite paper prompt as short system + N user/assistant few-shots.

    Upstream packs many examples into one system blob; that often yields
    reasoning_tokens but an empty summary. Multi-turn 3-shot keeps few-shot
    calibration and reliably returns a visible reasoning summary.
    """
    if not messages:
        return messages
    system = messages[0].get("content") or ""
    sentence = (messages[-1].get("content") or "").strip()
    match = re.search(r"Here are some examples:\s*(.*)$", system, re.S)
    block = (match.group(1) if match else "").strip()
    parts = re.split(r"(The naturalness score is[^\n]*)", block)
    pairs: List[Tuple[str, str]] = []
    for i, part in enumerate(parts):
        if part.startswith("The naturalness score is"):
            prev = parts[i - 1].strip() if i else ""
            if prev:
                pairs.append((prev, part.strip()))
            if len(pairs) >= num_ex:
                break

    out: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_1}]
    for user_sent, assistant in pairs:
        out.append({"role": "user", "content": user_sent})
        out.append({"role": "assistant", "content": assistant})
    out.append({"role": "user", "content": sentence})
    return out


def _extract_responses_texts(resp: Any) -> Tuple[str, Optional[str]]:
    """Parse Responses API output → (message text, reasoning summary)."""
    output_parts: List[str] = []
    thinking_parts: List[str] = []
    items = getattr(resp, "output", None) or []
    for item in items:
        itype = getattr(item, "type", None)
        if itype == "reasoning":
            for block in getattr(item, "summary", None) or []:
                text = getattr(block, "text", None)
                if text:
                    thinking_parts.append(str(text).strip())
        elif itype == "message":
            for block in getattr(item, "content", None) or []:
                text = getattr(block, "text", None)
                if text:
                    output_parts.append(str(text).strip())
    output = "\n".join(p for p in output_parts if p).strip()
    thinking = "\n\n".join(p for p in thinking_parts if p).strip() or None
    return output, thinking


def _score_via_responses(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """T mode: Responses API so we can show reasoning.summary on the UI."""
    import time

    from openai import OpenAI

    client = OpenAI(base_url=BASE_URL.rstrip("/"), api_key=_token())
    input_messages = _messages_for_thinking(messages, num_ex=3)
    t0 = time.perf_counter()
    resp = client.responses.create(
        model=MODEL,
        input=input_messages,
        reasoning={"effort": REASONING_EFFORT, "summary": "auto"},
        max_output_tokens=MAX_TOKENS_T,
    )
    latency_ms = int((time.perf_counter() - t0) * 1000)
    output_text, reasoning_text = _extract_responses_texts(resp)
    return {
        "output_text": output_text,
        "reasoning_text": reasoning_text,
        "latency_ms": latency_ms,
    }


def _score_one(client: ChatClient, sentence: str, *, thinking: bool) -> SentenceResult:
    human_mean, sample_id = _human_meta(sentence)
    messages = build_messages(
        sentence,
        repo=REPO,
        prompt_name="mem_enc",
        example_args={"num_ex": 3, "diff_sentence": "no"},
        add_examples=True,
    )
    try:
        if thinking:
            # Chat Completions không trả reasoning text; Responses API + summary mới show được.
            result = _score_via_responses(messages)
        else:
            result = client.chat(
                messages,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS_ORIG,
                extra_body=_extra_for_mode(False),
            )
    except Exception as exc:  # noqa: BLE001
        return SentenceResult(
            sentence=sentence,
            human_mean=human_mean,
            sample_id=sample_id,
            error=f"Model API error: {exc}",
        )

    output = (result.get("output_text") or "").strip()
    reasoning = (result.get("reasoning_text") or "").strip() or None
    parsed, ok = parse_score_from_output(output, expect_schema=False)
    if not ok or parsed is None:
        return SentenceResult(
            sentence=sentence,
            explanation=output,
            thinking=reasoning,
            human_mean=human_mean,
            sample_id=sample_id,
            latency_ms=int(result.get("latency_ms") or 0),
            error=f"Could not parse score: {output[:200]!r}",
        )

    return SentenceResult(
        sentence=sentence,
        score=int(parsed),
        explanation=output,
        thinking=reasoning,
        human_mean=human_mean,
        sample_id=sample_id,
        latency_ms=int(result.get("latency_ms") or 0),
    )


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "model": MODEL,
        "base_url": BASE_URL,
        "token_set": bool(_token()),
        "max_sentences": MAX_SENTENCES,
        "reasoning_effort": REASONING_EFFORT,
    }


@app.get("/api/examples")
def examples() -> Dict[str, Any]:
    return {"examples": EXAMPLES}


@app.post("/api/score", response_model=ScoreResponse)
def score(req: ScoreRequest) -> ScoreResponse:
    sentences = _parse_sentences(req)
    if not sentences:
        raise HTTPException(
            status_code=400,
            detail="Nhập ít nhất một câu (mỗi câu một dòng).",
        )

    token = _token()
    if not token:
        raise HTTPException(
            status_code=500,
            detail="Missing OPENAI_API_KEY in doan/.env",
        )

    thinking = bool(req.thinking)
    mode = "T" if thinking else "ORIG"
    client = ChatClient(base_url=BASE_URL, token=token, model=MODEL)
    results: List[Optional[SentenceResult]] = [None] * len(sentences)
    workers = min(MAX_WORKERS, len(sentences))

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_score_one, client, sentence, thinking=thinking): idx
            for idx, sentence in enumerate(sentences)
        }
        for fut in as_completed(futures):
            idx = futures[fut]
            results[idx] = fut.result()

    return ScoreResponse(
        model=MODEL,
        mode=mode,
        thinking=thinking,
        results=[r for r in results if r is not None],
    )


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "8000")),
        reload=True,
    )
