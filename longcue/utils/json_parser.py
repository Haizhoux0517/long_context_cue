from __future__ import annotations

import json
import logging
import re
from collections.abc import Iterable
from copy import deepcopy
from typing import Any

VISIBLE_PASSAGE_PATTERN = re.compile(r"\[passage_id:\s*(p?\d+)\]", re.IGNORECASE)
PASSAGE_BLOCK_PATTERN = re.compile(
    r"\[passage_id:\s*(p?\d+)\]\s*(.*?)(?=\n\s*\[passage_id:\s*p?\d+\]|\Z)",
    re.IGNORECASE | re.DOTALL,
)
NORMALIZABLE_PASSAGE_ID_PATTERN = re.compile(r"^p?(\d+)$", re.IGNORECASE)
PASSAGE_REFERENCE_ANSWER_PATTERN = re.compile(
    r"^(?:section|passage)_\d+$", re.IGNORECASE
)


def extract_json_object(text: str) -> dict[str, Any] | None:
    """Return the first decodable JSON object embedded in noisy model text."""
    for start, character in enumerate(text):
        if character != "{":
            continue
        candidate = _balanced_object(text[start:])
        if candidate is None:
            continue
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


def parse_json_response(
    text: str,
    expected_fields: Iterable[str],
    fallback: dict[str, Any],
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    parsed = extract_json_object(text)
    result = deepcopy(fallback)
    expected = tuple(expected_fields)
    if parsed is None:
        result["parse_error"] = "json_object_not_found"
        _log_failure(logger, "No JSON object found", text)
        return result

    missing = [field for field in expected if field not in parsed]
    result.update(parsed)
    if missing:
        result["parse_error"] = f"missing_fields:{','.join(missing)}"
        _log_failure(logger, f"Missing JSON fields {missing}", text)
    return result


def extract_passage_ids(text: str) -> list[str]:
    passage_ids: list[str] = []
    for match in VISIBLE_PASSAGE_PATTERN.finditer(text):
        normalized = normalize_passage_id(match.group(1))
        if normalized and normalized not in passage_ids:
            passage_ids.append(normalized)
    return passage_ids


def extract_passage_map(text: str) -> dict[str, str]:
    """Extract visible passage IDs and their canonical text from a prompt/context.

    LLMs are allowed to choose passage IDs, but we should not trust any text they
    return for those IDs. This helper recovers the authoritative passage text from
    the supplied context so downstream compression/answering cannot be driven by
    model-fabricated evidence text.
    """
    passages: dict[str, str] = {}
    for match in PASSAGE_BLOCK_PATTERN.finditer(text.strip()):
        passage_id = normalize_passage_id(match.group(1))
        if passage_id is None or passage_id in passages:
            continue
        passage_text = match.group(2).strip()
        passages[passage_id] = passage_text
    return passages


def normalize_passage_id(value: Any) -> str | None:
    match = NORMALIZABLE_PASSAGE_ID_PATTERN.fullmatch(str(value).strip())
    if match is None:
        return None
    return f"p{int(match.group(1)):04d}"


def normalize_evidence_ids(
    value: Any,
    *,
    available_passage_ids: Iterable[str] | None = None,
    max_ids: int = 3,
) -> list[str]:
    if isinstance(value, (str, int)):
        raw_ids = [value]
    elif isinstance(value, Iterable):
        raw_ids = list(value)
    else:
        raw_ids = []
    allowed = (
        {
            normalized
            for item in available_passage_ids
            if (normalized := normalize_passage_id(item)) is not None
        }
        if available_passage_ids is not None
        else None
    )
    normalized_ids: list[str] = []
    for item in raw_ids:
        normalized = normalize_passage_id(item)
        if normalized is None or (allowed is not None and normalized not in allowed):
            continue
        if normalized not in normalized_ids:
            normalized_ids.append(normalized)
        if len(normalized_ids) >= max_ids:
            break
    return normalized_ids


def sanitize_answer(value: Any) -> tuple[str, str | None]:
    answer = str(value or "").strip()
    if PASSAGE_REFERENCE_ANSWER_PATTERN.fullmatch(answer):
        return "", "passage_reference_answer"
    return answer, None


def _balanced_object(text: str) -> str | None:
    depth = 0
    in_string = False
    escaped = False
    for index, character in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return text[: index + 1]
            if depth < 0:
                return None
    return None


def _log_failure(logger: logging.Logger | None, message: str, text: str) -> None:
    if logger is not None:
        logger.warning("%s. Output prefix: %r", message, text[:300])
