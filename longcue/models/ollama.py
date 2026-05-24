from __future__ import annotations

import os
from typing import Any

import requests

from .base import BaseModelClient


class OllamaClient(BaseModelClient):
    def __init__(
        self,
        model_name: str = "llama3.1",
        base_url: str | None = None,
        timeout: float = 600.0,
        num_ctx: int | None = None,
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

    def generate(
        self, prompt: str, max_tokens: int = 512, temperature: float = 0.0
    ) -> str:
        options: dict[str, Any] = {
            "temperature": temperature,
            "num_predict": max_tokens,
            "num_ctx": self.num_ctx,
        }

        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model_name,
                "stream": False,
                "messages": [{"role": "user", "content": prompt}],
                "options": options,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        return str(payload["message"]["content"])