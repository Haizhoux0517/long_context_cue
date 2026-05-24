from __future__ import annotations

import logging
from collections import Counter
from pathlib import Path
from typing import Any

from longcue.utils.token_utils import estimate_tokens

from .adapter_utils import (
    answer_text,
    first_present,
    iter_json_records,
    raw_record_metadata,
    sample_from_parts,
    source_sample_id,
    text_value,
)
from .schema import BenchmarkSample


def convert_ruler_path(
    input_path: str | Path, logger: logging.Logger | None = None
) -> tuple[list[BenchmarkSample], dict[str, Any]]:
    _log(
        logger,
        "RULER adapter leaves oracle evidence empty when local records do not expose it; CUE is disabled.",
    )
    samples: list[BenchmarkSample] = []
    skips: Counter[str] = Counter()
    for index, item in enumerate(_safe_records(input_path, logger)):
        file_path, record = item
        sample = convert_ruler_record(
            record,
            index=index,
            task_hint=_task_hint(file_path, record),
            input_path=file_path,
        )
        if sample is None:
            skips["invalid_record"] += 1
            _log(logger, "Skipping invalid RULER record %s in %s", index, file_path)
            continue
        samples.append(sample)
    return samples, {"converted": len(samples), "skipped": sum(skips.values()), "skip_reasons": dict(skips)}


def convert_ruler_record(
    record: dict[str, Any],
    *,
    index: int,
    task_hint: str = "",
    input_path: str | Path | None = None,
) -> BenchmarkSample | None:
    answer_value = first_present(
        record,
        ("gold_answer", "answer", "answers", "output", "outputs", "target", "targets"),
    )
    long_context_value = first_present(
        record, ("long_context", "context", "document", "documents", "input", "prompt")
    )
    question_value = first_present(record, ("question", "query", "instruction", "prompt"))
    if question_value is None and record.get("input") is not None:
        question_value = record.get("input")
    answer = answer_text(answer_value).strip()
    long_context = text_value(long_context_value).strip()
    question = text_value(question_value).strip()
    if not answer or not long_context or not question:
        return None
    task_name = str(
        first_present(record, ("task", "task_name", "name", "benchmark", "dataset"))
        or task_hint
        or "unknown"
    )
    context_length = _context_length(record, long_context)
    metadata: dict[str, Any] = {
        "task": task_name,
        "cue_applicable": False,
        "original": raw_record_metadata(record),
    }
    if input_path is not None:
        metadata["input_path"] = str(input_path)
    return sample_from_parts(
        sample_id=source_sample_id("ruler", first_present(record, ("id", "sample_id", "_id")), index),
        source="ruler",
        question=question,
        gold_answer=answer,
        long_context=long_context,
        context_length=context_length,
        evidence_position="unknown",
        evidence_density="unknown",
        distractor_similarity="unknown",
        reasoning_type=map_ruler_reasoning(task_name),
        metadata=metadata,
        original_answer=answer_value,
    )


def map_ruler_reasoning(task_name: str) -> str:
    normalized = task_name.lower().replace("-", " ").replace("_", " ")
    if any(token in normalized for token in ("niah", "needle")):
        return "retrieval"
    if "variable" in normalized or "tracing" in normalized or "trace" in normalized:
        return "multi_hop"
    if "aggregation" in normalized or "aggregate" in normalized:
        return "aggregation"
    if "qa" in normalized:
        return "retrieval"
    return "unknown"


def _safe_records(
    input_path: str | Path, logger: logging.Logger | None
) -> list[tuple[Path, dict[str, Any]]]:
    try:
        return list(iter_json_records(input_path))
    except (OSError, ValueError, TypeError) as exc:
        _log(logger, "Unable to read RULER input %s: %s", input_path, exc)
        return []


def _task_hint(file_path: Path, record: dict[str, Any]) -> str:
    del record
    return file_path.stem


def _context_length(record: dict[str, Any], long_context: str) -> int:
    raw_length = first_present(record, ("context_length", "length", "tokens", "token_length"))
    try:
        return int(raw_length)
    except (TypeError, ValueError):
        return estimate_tokens(long_context)


def _log(logger: logging.Logger | None, message: str, *args: Any) -> None:
    if logger is not None:
        logger.warning(message, *args)
