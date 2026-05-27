from __future__ import annotations

import logging
from typing import Any

from longcue.data.schema import BenchmarkSample
from longcue.models.base import BaseModelClient
from longcue.prompts.templates import direct_answer_prompt

from .common import parse_answer, result_payload
from .retrievers import retrieve_chunks


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
    retrieved_chunks = retrieve_chunks(
        sample=sample,
        retriever=str(settings.get("retriever", "lexical")),
        top_k=int(settings.get("top_k", 3)),
        chunk_size=int(settings.get("chunk_size", 220)),
        overlap=int(settings.get("overlap", 40)),
        dense_model_name=str(
            settings.get("dense_model_name", "sentence-transformers/all-MiniLM-L6-v2")
        ),
        rrf_k=int(settings.get("rrf_k", 60)),
        iterative_seed_k=int(settings.get("iterative_seed_k", 2)),
        iterative_expansion_words=int(settings.get("iterative_expansion_words", 96)),
    )
    retrieved = [chunk.text for chunk in retrieved_chunks]
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
        intermediate={
            "retrieved_chunks": retrieved,
            "retrieved_passage_ids": [
                list(chunk.passage_ids) for chunk in retrieved_chunks
            ],
            "chunk_count": len(retrieved_chunks),
            "retriever": str(settings.get("retriever", "lexical")),
        },
    )


def retrieve_top_k(question: str, chunks: list[str], top_k: int = 3) -> list[str]:
    """Backward-compatible lexical helper retained for older imports/tests."""
    from longcue.data.schema import BenchmarkSample

    sample = BenchmarkSample(
        id="compat_retrieval_sample",
        question=question,
        gold_answer="unknown",
        oracle_evidence=[],
        long_context="\n\n".join(chunks) if chunks else "empty context",
        distractors=[],
        evidence_position="unknown",
        context_length=0,
        evidence_density="unknown",
        distractor_similarity="unknown",
        reasoning_type="unknown",
        source="controlled",
        answer_type="unknown",
    )
    return [
        chunk.text
        for chunk in retrieve_chunks(sample=sample, retriever="lexical", top_k=top_k)
    ]
