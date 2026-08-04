from __future__ import annotations

import json
import os
import re
import time
from typing import Any

from openai import OpenAI


def get_deepseek_client() -> OpenAI:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY not set in environment")
    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    return OpenAI(api_key=api_key, base_url=base_url)


def chat_json(
    client: OpenAI,
    *,
    system: str,
    user: str,
    model: str = "deepseek-v4-flash",
    temperature: float = 0.1,
    max_tokens: int = 800,
    retries: int = 4,
    disable_thinking: bool = True,
) -> dict[str, Any]:
    """Call chat completion and parse a JSON object from the response."""
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            kwargs: dict[str, Any] = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
            }
            # V4 defaults to thinking mode; for bulk labeling we want direct JSON answers.
            if disable_thinking:
                kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
                kwargs["temperature"] = temperature
            else:
                kwargs["extra_body"] = {"thinking": {"type": "enabled"}}
                kwargs["reasoning_effort"] = "low"

            resp = client.chat.completions.create(**kwargs)
            msg = resp.choices[0].message
            content = (msg.content or "").strip()
            if not content:
                # rare: model only filled reasoning
                reasoning = getattr(msg, "reasoning_content", None) or ""
                content = reasoning.strip()
            return _parse_json_object(content)
        except Exception as e:  # noqa: BLE001 - retry network/API failures
            last_err = e
            time.sleep(1.2 * (attempt + 1))
    raise RuntimeError(f"DeepSeek chat_json failed after {retries} retries: {last_err}")


def _parse_json_object(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        raise ValueError("Empty model output")
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError(f"No JSON object in model output: {text[:200]!r}")
    data = json.loads(m.group(0))
    if not isinstance(data, dict):
        raise ValueError("Parsed JSON is not an object")
    return data
