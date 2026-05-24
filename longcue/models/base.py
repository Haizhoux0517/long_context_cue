from __future__ import annotations

from abc import ABC, abstractmethod


class BaseModelClient(ABC):
    model_name: str

    @abstractmethod
    def generate(
        self, prompt: str, max_tokens: int = 512, temperature: float = 0.0
    ) -> str:
        raise NotImplementedError
