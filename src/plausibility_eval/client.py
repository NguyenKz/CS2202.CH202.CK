"""OpenAI-compatible chat client + usage extraction (no USD)."""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse


def is_open_endpoint(base_url: str, markers: List[str]) -> bool:
    u = (base_url or "").lower()
    return any(m.lower() in u for m in markers)


def provider_from_base_url(base_url: str) -> str:
    host = urlparse(base_url).netloc.lower() if base_url else ""
    if "openrouter" in host:
        return "openrouter"
    if "openai.com" in host:
        return "openai_official"
    if "googleapis" in host or "generativelanguage" in host:
        return "gemini_openai_compat"
    if "anthropic" in host:
        return "anthropic"
    if any(x in host for x in ("localhost", "127.0.0.1", "ngrok", "trycloudflare")):
        return "llamacpp_endpoint"
    return host or "unknown"


def extract_usage(resp: Any) -> Dict[str, int]:
    usage = getattr(resp, "usage", None)
    if usage is None and isinstance(resp, dict):
        usage = resp.get("usage")
    if usage is None:
        return {"input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0}

    def g(obj: Any, *names: str, default: int = 0) -> int:
        if obj is None:
            return default
        if isinstance(obj, dict):
            for n in names:
                if n in obj and obj[n] is not None:
                    return int(obj[n])
            return default
        for n in names:
            if hasattr(obj, n) and getattr(obj, n) is not None:
                return int(getattr(obj, n))
        return default

    input_tokens = g(usage, "prompt_tokens", "input_tokens")
    output_tokens = g(usage, "completion_tokens", "output_tokens")
    reasoning_tokens = 0
    details = None
    if isinstance(usage, dict):
        details = usage.get("completion_tokens_details") or usage.get("output_tokens_details")
    else:
        details = getattr(usage, "completion_tokens_details", None) or getattr(
            usage, "output_tokens_details", None
        )
    reasoning_tokens = g(details, "reasoning_tokens", default=0)
    if reasoning_tokens == 0:
        reasoning_tokens = g(usage, "reasoning_tokens", default=0)
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning_tokens,
    }


def _coerce_reasoning(value: Any) -> Optional[str]:
    """Normalize OpenRouter reasoning / reasoning_details into a single string."""
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        return s or None
    if isinstance(value, list):
        parts: List[str] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                parts.append(item.strip())
            elif isinstance(item, dict):
                text = item.get("text") or item.get("content") or item.get("summary")
                if text:
                    parts.append(str(text).strip())
        return "\n".join(parts) if parts else None
    if isinstance(value, dict):
        text = value.get("text") or value.get("content") or value.get("summary")
        return str(text).strip() if text else None
    return str(value).strip() or None


def extract_text_and_reasoning(resp: Any) -> Tuple[str, Optional[str]]:
    choice0 = None
    if hasattr(resp, "choices") and resp.choices:
        choice0 = resp.choices[0]
    elif isinstance(resp, dict) and resp.get("choices"):
        choice0 = resp["choices"][0]

    message = None
    if choice0 is not None:
        message = getattr(choice0, "message", None)
        if message is None and isinstance(choice0, dict):
            message = choice0.get("message") or {}
            text = choice0.get("text")
            if text and not message:
                return str(text), None

    if message is None:
        return "", None

    if isinstance(message, dict):
        content = message.get("content") or ""
        reasoning = (
            _coerce_reasoning(message.get("reasoning"))
            or _coerce_reasoning(message.get("reasoning_content"))
            or _coerce_reasoning(message.get("reasoning_details"))
        )
        return str(content or ""), reasoning

    content = getattr(message, "content", None) or ""
    reasoning = (
        _coerce_reasoning(getattr(message, "reasoning", None))
        or _coerce_reasoning(getattr(message, "reasoning_content", None))
        or _coerce_reasoning(getattr(message, "reasoning_details", None))
    )
    return str(content or ""), reasoning


def extract_ids(resp: Any) -> Tuple[str, Optional[str]]:
    rid = None
    if hasattr(resp, "id"):
        rid = resp.id
    elif isinstance(resp, dict):
        rid = resp.get("id")
    rid = str(rid) if rid else None
    trace = rid or str(uuid.uuid4())
    return trace, rid


def response_to_dict(resp: Any) -> Any:
    if hasattr(resp, "model_dump"):
        try:
            return resp.model_dump()
        except Exception:
            pass
    if hasattr(resp, "to_dict"):
        try:
            return resp.to_dict()
        except Exception:
            pass
    if isinstance(resp, dict):
        return resp
    return {"repr": repr(resp)}


class ChatClient:
    def __init__(self, base_url: str, token: str, model: str, default_headers: Optional[Dict[str, str]] = None):
        from openai import OpenAI

        headers = dict(default_headers or {})
        if "openrouter.ai" in (base_url or ""):
            headers.setdefault("HTTP-Referer", "https://github.com/NguyenKz/CS2202-doan-plausibility")
            headers.setdefault("X-Title", "CS2202-plausibility-eval")
        self.client = OpenAI(base_url=base_url.rstrip("/"), api_key=token or "sk-local", default_headers=headers or None)
        self.model = model
        self.base_url = base_url
        self.provider = provider_from_base_url(base_url)

    def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float,
        max_tokens: int,
        response_format: Optional[Dict[str, Any]] = None,
        extra_body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        mid = (self.model or "").lower()
        # GPT-5 / o-series: max_completion_tokens; many only allow default temperature=1
        is_reasoning_family = any(x in mid for x in ("gpt-5", "o1", "o3", "o4"))

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if is_reasoning_family:
            kwargs["max_completion_tokens"] = int(max_tokens)
            if float(temperature) == 1.0:
                kwargs["temperature"] = 1.0
        else:
            kwargs["temperature"] = float(temperature)
            kwargs["max_tokens"] = int(max_tokens)
        if response_format is not None:
            kwargs["response_format"] = response_format
        if extra_body:
            kwargs["extra_body"] = extra_body

        t0 = time.perf_counter()
        resp = self.client.chat.completions.create(**kwargs)
        latency_ms = int((time.perf_counter() - t0) * 1000)
        output_text, reasoning_text = extract_text_and_reasoning(resp)
        trace_id, request_id = extract_ids(resp)
        usage = extract_usage(resp)
        return {
            "response_raw": response_to_dict(resp),
            "output_text": output_text,
            "reasoning_text": reasoning_text,
            "usage": usage,
            "trace_id": trace_id,
            "request_id": request_id,
            "latency_ms": latency_ms,
            "request": {
                "messages_or_prompt": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "response_format": response_format,
                "extra": extra_body or {},
            },
        }
