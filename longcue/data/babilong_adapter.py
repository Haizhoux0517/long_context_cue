from __future__ import annotations

import logging
from collections import Counter
from collections.abc import Iterable
from typing import Any

from .adapter_utils import (
    add_passage_ids_to_context,
    answer_text,
    first_present,
    raw_record_metadata,
    sample_from_parts,
    source_sample_id,
    text_value,
)
from .schema import BenchmarkSample

BABILONG_CONFIGS = ("0k", "1k", "2k", "4k", "8k", "16k", "32k", "128k")


def load_babilong_cue(
    configs: list[str],
    tasks: list[str],
    *,
    limit_per_task: int | None = None,
    logger: logging.Logger | None = None,
) -> tuple[list[BenchmarkSample], dict[str, Any]]:
    from datasets import load_dataset

    _warning(
        logger,
        "BABILong adapter has no oracle evidence for converted samples; CUE is disabled.",
    )
    samples: list[BenchmarkSample] = []
    config_stats: dict[str, Any] = {}
    for config in configs:
        if config not in BABILONG_CONFIGS:
            _warning(logger, "Skipping unsupported BABILong config %s", config)
            config_stats[config] = {"converted": 0, "unsupported": True}
            continue
        try:
            dataset = load_dataset("RMT-team/babilong", config)
        except Exception as exc:  # pragma: no cover - network/runtime dependent
            _warning(logger, "BABILong load failed for config %s: %s", config, exc)
            config_stats[config] = {"converted": 0, "load_error": True}
            continue
        config_stats[config] = {}
        available_tasks = list(dataset.keys()) if hasattr(dataset, "keys") else []
        for task in tasks:
            if task not in available_tasks:
                _warning(logger, "BABILong config %s does not contain task %s", config, task)
                config_stats[config][task] = {"converted": 0, "missing_task": True}
                continue
            converted, stats = convert_babilong_records(
                dataset[task],
                config=config,
                task=task,
                limit=limit_per_task,
                logger=logger,
            )
            samples.extend(converted)
            config_stats[config][task] = stats
            _info(logger, "Converted %d BABILong %s/%s samples", len(converted), config, task)
    return samples, {"converted": len(samples), "configs": config_stats}


def convert_babilong_records(
    records: Iterable[dict[str, Any]],
    *,
    config: str,
    task: str,
    limit: int | None = None,
    logger: logging.Logger | None = None,
) -> tuple[list[BenchmarkSample], dict[str, Any]]:
    samples: list[BenchmarkSample] = []
    skips: Counter[str] = Counter()
    for index, record in enumerate(records):
        if limit is not None and len(samples) >= limit:
            break
        if not isinstance(record, dict):
            skips["non_mapping_record"] += 1
            continue
        sample = convert_babilong_record(record, config=config, task=task, index=index)
        if sample is None:
            skips["invalid_record"] += 1
            _warning(logger, "Skipping invalid BABILong %s/%s record %d", config, task, index)
            continue
        samples.append(sample)
    return samples, {"converted": len(samples), "skipped": sum(skips.values()), "skip_reasons": dict(skips)}


def convert_babilong_record(
    record: dict[str, Any], *, config: str, task: str, index: int
) -> BenchmarkSample | None:
    question_value = first_present(record, ("question", "query", "prompt"))
    context_value = first_present(record, ("long_context", "context", "input", "story"))
    answer_value = first_present(record, ("gold_answer", "target", "answer", "answers", "output"))
    question = text_value(question_value).strip()
    long_context = add_passage_ids_to_context(text_value(context_value))
    answer = answer_text(answer_value).strip()
    if not question or not long_context or not answer:
        return None
    raw_id = first_present(record, ("id", "_id", "sample_id"))
    return sample_from_parts(
        sample_id=f"babilong_{config}_{task}_{source_sample_id('babilong', raw_id, index)}",
        source="babilong",
        question=question,
        gold_answer=answer,
        long_context=long_context,
        evidence_position="unknown",
        evidence_density="unknown",
        distractor_similarity="unknown",
        reasoning_type="unknown",
        metadata={
            "config": config,
            "task": task,
            "cue_applicable": False,
            "original": raw_record_metadata(record),
        },
        original_answer=answer_value,
    )


def _warning(logger: logging.Logger | None, message: str, *args: Any) -> None:
    if logger is not None:
        logger.warning(message, *args)


def _info(logger: logging.Logger | None, message: str, *args: Any) -> None:
    if logger is not None:
        logger.info(message, *args)
