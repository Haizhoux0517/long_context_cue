from __future__ import annotations

import logging
from typing import Any

from collections.abc import Iterable

from longcue.utils.json_parser import (
    extract_passage_ids,
    normalize_evidence_ids,
    parse_json_response,
    sanitize_answer,
)


def answer_fallback() -> dict[str, Any]:
    return {"answer": "", "evidence_ids": [], "explanation": ""}


def parse_answer(
    raw: str,
    logger: logging.Logger | None = None,
    *,
    passage_text: str | None = None,
    available_passage_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    parsed = parse_json_response(
        raw,
        expected_fields=("answer", "evidence_ids", "explanation"),
        fallback=answer_fallback(),
        logger=logger,
    )
    parsed["answer"], answer_error = sanitize_answer(parsed.get("answer", ""))
    if answer_error:
        parsed["answer_validation_error"] = answer_error
    if available_passage_ids is None and passage_text is not None:
        available_passage_ids = extract_passage_ids(passage_text)
    parsed["evidence_ids"] = normalize_evidence_ids(
        parsed.get("evidence_ids", []),
        available_passage_ids=available_passage_ids,
        max_ids=3,
    )
    parsed["explanation"] = str(parsed.get("explanation", ""))
    return parsed


def result_payload(
    method: str,
    raw_response: str,
    prediction: dict[str, Any],
    prompt: str,
    intermediate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "method": method,
        "raw_response": raw_response,
        "prediction": prediction,
        "prompt": prompt,
        "intermediate": intermediate or {},
    }
