from __future__ import annotations

import os
from typing import Any

import requests

from .base import BaseModelClient


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


class OllamaClient(BaseModelClient):
    def __init__(
        self,
        model_name: str = "llama3.1",
        base_url: str | None = None,
        timeout: float = 600.0,
        num_ctx: int | None = None,
        think: bool | None = None,
        json_mode: bool | None = None,
    ) -> None:
        self.model_name = model_name
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip(
            "/"
        )
        self.timeout = timeout

        # Default to 32768 so long-context runs do not silently fall back to
        # Ollama's smaller default context window. Can be overridden by:
        #   OLLAMA_NUM_CTX=16384 python -m longcue.run_experiment ...
        self.num_ctx = int(os.getenv("OLLAMA_NUM_CTX", str(num_ctx or 32768)))

        # Qwen3-style thinking models may put reasoning in message.thinking and
        # leave message.content empty or too short for the JSON parser.
        # This is an inference-control setting, not a prompt change.
        self.think = _env_bool("OLLAMA_THINK", think if think is not None else False)

        # Keep JSON mode off by default to avoid changing prior Qwen2.5 runs.
        # If needed for debugging structured-output failures:
        #   OLLAMA_JSON_MODE=true python -m longcue.run_experiment ...
        self.json_mode = _env_bool(
            "OLLAMA_JSON_MODE", json_mode if json_mode is not None else False
        )

    def generate(
        self, prompt: str, max_tokens: int = 512, temperature: float = 0.0
    ) -> str:
        options: dict[str, Any] = {
            "temperature": temperature,
            "num_predict": max_tokens,
            "num_ctx": self.num_ctx,
        }

        payload: dict[str, Any] = {
            "model": self.model_name,
            "stream": False,
            "think": self.think,
            "messages": [{"role": "user", "content": prompt}],
            "options": options,
        }

        if self.json_mode:
            payload["format"] = "json"

        response = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()

        data: dict[str, Any] = response.json()
        message = data.get("message", {})
        content = message.get("content", "")

        return str(content or "")