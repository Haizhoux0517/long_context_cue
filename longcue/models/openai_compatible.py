from __future__ import annotations

import os
from typing import Any

import requests

from .base import BaseModelClient


class OpenAICompatibleClient(BaseModelClient):
    """Minimal client for providers exposing the chat completions protocol."""

    def __init__(
        self,
        model_name: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        self.model_name = model_name or os.getenv("OPENAI_COMPATIBLE_MODEL", "")
        self.base_url = (base_url or os.getenv("OPENAI_COMPATIBLE_BASE_URL", "")).rstrip(
            "/"
        )
        self.api_key = api_key or os.getenv("OPENAI_COMPATIBLE_API_KEY", "")
        self.timeout = timeout
        if not self.model_name or not self.base_url:
            raise ValueError(
                "OpenAI-compatible model_name and base URL are required. "
                "Set config model.model_name and OPENAI_COMPATIBLE_BASE_URL."
            )

    def generate(
        self, prompt: str, max_tokens: int = 512, temperature: float = 0.0
    ) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json={
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": "Return valid JSON that follows the user schema.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        return str(payload["choices"][0]["message"]["content"])
