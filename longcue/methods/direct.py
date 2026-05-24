from __future__ import annotations

import logging
from typing import Any

from longcue.data.schema import BenchmarkSample
from longcue.models.base import BaseModelClient
from longcue.prompts.templates import direct_answer_prompt

from .common import parse_answer, result_payload


def run(
    sample: BenchmarkSample,
    client: BaseModelClient,
    max_tokens: int = 512,
    temperature: float = 0.0,
    logger: logging.Logger | None = None,
    **_: Any,
) -> dict[str, Any]:
    prompt = direct_answer_prompt(
        sample.question,
        sample.long_context,
        reasoning_type=sample.reasoning_type,
        answer_type=sample.answer_type,
    )
    raw = client.generate(prompt, max_tokens=max_tokens, temperature=temperature)
    return result_payload(
        "direct", raw, parse_answer(raw, logger, passage_text=prompt), prompt
    )
