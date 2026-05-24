from __future__ import annotations

import logging
from typing import Any

from longcue.data.schema import BenchmarkSample
from longcue.models.base import BaseModelClient
from longcue.prompts.templates import (
    evidence_answer_prompt,
    evidence_compression_prompt,
    evidence_extraction_prompt,
)
from longcue.utils.json_parser import (
    extract_passage_ids,
    extract_passage_map,
    normalize_passage_id,
    parse_json_response,
)

from .common import parse_answer, result_payload


def run(
    sample: BenchmarkSample,
    client: BaseModelClient,
    max_tokens: int = 512,
    temperature: float = 0.0,
    logger: logging.Logger | None = None,
    **_: Any,
) -> dict[str, Any]:
    trace = evidence_first_trace(
        sample=sample,
        client=client,
        max_tokens=max_tokens,
        temperature=temperature,
        logger=logger,
    )
    return result_payload(
        "evidence_first",
        trace["answer_raw"],
        trace["answer"],
        trace["answer_prompt"],
        intermediate={
            "extraction_prompt": trace["extraction_prompt"],
            "extraction_raw": trace["extraction_raw"],
            "extraction": trace["extraction"],
            "compression_prompt": trace["compression_prompt"],
            "compression_raw": trace["compression_raw"],
            "compression": trace["compression"],
            "selected_evidence_ids": trace["selected_evidence_ids"],
            "evidence_summary": trace["evidence_summary"],
            "final_answer": trace["answer"].get("answer", ""),
        },
    )


def evidence_first_trace(
    sample: BenchmarkSample,
    client: BaseModelClient,
    max_tokens: int,
    temperature: float,
    logger: logging.Logger | None,
) -> dict[str, Any]:
    extraction_prompt = evidence_extraction_prompt(
        sample.question,
        sample.long_context,
        reasoning_type=sample.reasoning_type,
        answer_type=sample.answer_type,
    )
    extraction_raw = client.generate(
        extraction_prompt, max_tokens=max(max_tokens, 512), temperature=temperature
    )
    extraction = parse_json_response(
        extraction_raw,
        expected_fields=("selected_evidence",),
        fallback={"selected_evidence": []},
        logger=logger,
    )
    passage_text_by_id = extract_passage_map(sample.long_context)
    selected_evidence = _normalize_selected_evidence(
        extraction.get("selected_evidence"),
        available_passage_ids=extract_passage_ids(extraction_prompt),
        passage_text_by_id=passage_text_by_id,
    )
    extraction["selected_evidence"] = selected_evidence

    compression_prompt = evidence_compression_prompt(
        sample.question,
        selected_evidence,
        reasoning_type=sample.reasoning_type,
        answer_type=sample.answer_type,
    )
    compression_raw = client.generate(
        compression_prompt, max_tokens=max_tokens, temperature=temperature
    )
    compression = parse_json_response(
        compression_raw,
        expected_fields=("evidence_summary",),
        fallback={"evidence_summary": ""},
        logger=logger,
    )
    evidence_summary = str(compression.get("evidence_summary", ""))
    compression["evidence_summary"] = evidence_summary

    answer_prompt = evidence_answer_prompt(
        sample.question,
        evidence_summary,
        selected_evidence,
        reasoning_type=sample.reasoning_type,
        answer_type=sample.answer_type,
    )
    answer_raw = client.generate(answer_prompt, max_tokens=max_tokens, temperature=temperature)
    return {
        "extraction_prompt": extraction_prompt,
        "extraction_raw": extraction_raw,
        "extraction": extraction,
        "compression_prompt": compression_prompt,
        "compression_raw": compression_raw,
        "compression": compression,
        "selected_evidence": selected_evidence,
        "selected_evidence_ids": [item["evidence_id"] for item in selected_evidence],
        "evidence_summary": evidence_summary,
        "answer_prompt": answer_prompt,
        "answer_raw": answer_raw,
        "answer": parse_answer(answer_raw, logger, passage_text=answer_prompt),
    }


def _normalize_selected_evidence(
    value: Any,
    *,
    available_passage_ids: list[str] | None = None,
    passage_text_by_id: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    allowed = set(available_passage_ids) if available_passage_ids is not None else None
    selected: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        evidence_id = normalize_passage_id(item.get("evidence_id", ""))
        if evidence_id is None or (allowed is not None and evidence_id not in allowed):
            continue
        if any(existing["evidence_id"] == evidence_id for existing in selected):
            continue
        canonical_text = (passage_text_by_id or {}).get(evidence_id)
        selected.append(
            {
                "evidence_id": evidence_id,
                # Trust the model only for the selected ID. The text is always
                # recovered from the original context when available, because
                # small LLMs often hallucinate passage text during extraction.
                "text": canonical_text if canonical_text is not None else str(item.get("text", "")),
                "relevance_score": float(item.get("relevance_score", 0.0) or 0.0),
            }
        )
        if len(selected) >= 3:
            break
    return selected
