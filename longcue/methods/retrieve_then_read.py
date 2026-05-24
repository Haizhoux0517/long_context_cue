from __future__ import annotations

import logging
import re
from typing import Any

from longcue.data.schema import BenchmarkSample
from longcue.models.base import BaseModelClient
from longcue.prompts.templates import direct_answer_prompt
from longcue.utils.token_utils import chunk_words

from .common import parse_answer, result_payload

WORD_PATTERN = re.compile(r"\w+")


def run(
    sample: BenchmarkSample,
    client: BaseModelClient,
    max_tokens: int = 512,
    temperature: float = 0.0,
    logger: logging.Logger | None = None,
    retrieval: dict[str, Any] | None = None,
    **_: Any,
) -> dict[str, Any]:
    settings = retrieval or {}
    chunks = chunk_words(
        sample.long_context,
        chunk_size=int(settings.get("chunk_size", 220)),
        overlap=int(settings.get("overlap", 40)),
    )
    retrieved = retrieve_top_k(sample.question, chunks, top_k=int(settings.get("top_k", 3)))
    context = "\n\n".join(retrieved)
    prompt = direct_answer_prompt(
        sample.question,
        context,
        task="RETRIEVE_THEN_READ",
        reasoning_type=sample.reasoning_type,
        answer_type=sample.answer_type,
    )
    raw = client.generate(prompt, max_tokens=max_tokens, temperature=temperature)
    return result_payload(
        "retrieve_then_read",
        raw,
        parse_answer(raw, logger, passage_text=prompt),
        prompt,
        intermediate={"retrieved_chunks": retrieved, "chunk_count": len(chunks)},
    )


def retrieve_top_k(question: str, chunks: list[str], top_k: int = 3) -> list[str]:
    if not chunks or top_k <= 0:
        return []
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer

        matrix = TfidfVectorizer().fit_transform(chunks + [question])
        scores = (matrix[:-1] @ matrix[-1].T).toarray().ravel()
    except ImportError:
        question_terms = set(WORD_PATTERN.findall(question.lower()))
        scores = [
            len(question_terms.intersection(WORD_PATTERN.findall(chunk.lower())))
            for chunk in chunks
        ]
    ranked = sorted(enumerate(scores), key=lambda item: (-float(item[1]), item[0]))
    return [chunks[index] for index, _ in ranked[: min(top_k, len(chunks))]]
