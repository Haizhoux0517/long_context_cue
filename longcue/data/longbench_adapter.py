from __future__ import annotations

import json
import logging
import zipfile
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .adapter_utils import (
    add_passage_ids_to_context,
    answer_text,
    first_present,
    iter_json_records,
    raw_record_metadata,
    sample_from_parts,
    text_value,
)
from .schema import BenchmarkSample

LONGBENCH_DATASET_IDS = ("zai-org/LongBench", "THUDM/LongBench")
LONGBENCH_HF_DATA_FILES = (
    (
        "zai-org/LongBench",
        "parquet",
        "https://huggingface.co/datasets/zai-org/LongBench/resolve/52edb9d18ea01d49ec7580fefcfe6b9d97a0fa96/{task}/test-00000-of-00001.parquet",
    ),
)
LONGBENCH_RETRIEVAL_TASKS = {
    "narrativeqa",
    "qasper",
    "multifieldqa_en",
    "multifieldqa_zh",
    "dureader",
}
LONGBENCH_MULTI_HOP_TASKS = {"hotpotqa", "2wikimqa", "musique"}
LONGBENCH_SUMMARIZATION_TASKS = {
    "gov_report",
    "qmsum",
    "multi_news",
    "vcsum",
}


def load_longbench_cue(
    tasks: list[str],
    *,
    limit_per_task: int | None = None,
    split: str = "test",
    local_dir: str | Path | None = None,
    logger: logging.Logger | None = None,
) -> tuple[list[BenchmarkSample], dict[str, Any]]:
    _warning(
        logger,
        "LongBench adapter has no oracle evidence for selected tasks; CUE is disabled for converted samples.",
    )
    samples: list[BenchmarkSample] = []
    task_stats: dict[str, Any] = {}
    for task in tasks:
        records, load_strategy = _load_task(task, split, local_dir, logger)
        if records is None:
            task_stats[task] = {"converted": 0, "skipped": 0, "load_error": True}
            continue
        converted, stats = convert_longbench_records(
            records, task=task, limit=limit_per_task, logger=logger
        )
        samples.extend(converted)
        stats["load_strategy"] = load_strategy
        task_stats[task] = stats
        _info(logger, "Converted %d LongBench %s samples", len(converted), task)
    if not samples:
        _warning(
            logger,
            "No LongBench samples were converted. If Hugging Face loading fails, download LongBench task files and pass --local-dir data/raw/LongBench with files such as narrativeqa.jsonl.",
        )
    return samples, {"converted": len(samples), "tasks": task_stats}


def convert_longbench_records(
    records: Iterable[dict[str, Any]],
    *,
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
        sample = convert_longbench_record(record, task=task, index=index)
        if sample is None:
            skips["invalid_record"] += 1
            _warning(logger, "Skipping invalid LongBench %s record %d", task, index)
            continue
        samples.append(sample)
    return samples, {"converted": len(samples), "skipped": sum(skips.values()), "skip_reasons": dict(skips)}


def convert_longbench_record(
    record: dict[str, Any], *, task: str, index: int
) -> BenchmarkSample | None:
    question_value = first_present(
        record, ("question", "query", "instruction", "input", "prompt")
    )
    context_value = first_present(
        record,
        ("long_context", "context", "input", "document", "documents", "passage"),
    )
    answer_value = first_present(
        record, ("gold_answer", "answers", "answer", "output", "label", "target")
    )
    question = text_value(question_value).strip()
    long_context = add_passage_ids_to_context(text_value(context_value))
    answer = answer_text(answer_value).strip()
    if not question or not long_context or not answer:
        return None
    return sample_from_parts(
        sample_id=f"longbench_{task}_{index}",
        source="longbench",
        question=question,
        gold_answer=answer,
        long_context=long_context,
        evidence_position="unknown",
        evidence_density="unknown",
        distractor_similarity="unknown",
        reasoning_type=_longbench_reasoning(task),
        answer_type=_longbench_answer_type(answer_value, answer),
        metadata={
            "task": task,
            "cue_applicable": False,
            "original": raw_record_metadata(record),
        },
        original_answer=answer_value,
    )


def load_local_longbench_records(
    local_dir: str | Path, task: str, logger: logging.Logger | None = None
) -> list[dict[str, Any]] | None:
    root = Path(local_dir)
    candidates = [
        root / f"{task}.jsonl",
        root / f"{task}.json",
        root / "data" / f"{task}.jsonl",
        root / "data" / f"{task}.json",
    ]
    seen_paths: set[Path] = set()
    for candidate in candidates + sorted(root.rglob(f"{task}.jsonl")) + sorted(root.rglob(f"{task}.json")):
        if candidate in seen_paths or not candidate.is_file():
            continue
        seen_paths.add(candidate)
        records = [record for _, record in iter_json_records(candidate)]
        if records:
            _info(logger, "Loaded LongBench %s from local file %s", task, candidate)
            return records
        _warning(logger, "LongBench local file %s did not contain JSON records", candidate)
    _warning(
        logger,
        "No local LongBench file found for task %s under %s",
        task,
        root,
    )
    return None


def _load_task(
    task: str,
    split: str,
    local_dir: str | Path | None,
    logger: logging.Logger | None,
) -> tuple[Any | None, str]:
    dataset = _load_task_via_dataset_script(task, split, logger)
    if dataset is not None:
        return dataset, "hf_dataset"
    if local_dir is not None:
        local_records = load_local_longbench_records(local_dir, task, logger)
        if local_records is not None:
            return local_records, "local_file"
    hub_records = _load_task_via_hf_data_files(task, logger)
    if hub_records is not None:
        return hub_records, "hf_data_file"
    return None, ""


def _load_task_via_dataset_script(task: str, split: str, logger: logging.Logger | None) -> Any | None:
    from datasets import load_dataset

    for dataset_id in LONGBENCH_DATASET_IDS:
        try:
            return load_dataset(dataset_id, task, split=split)
        except Exception as exc:  # pragma: no cover - network/runtime dependent
            if _scripts_unsupported(exc):
                _warning(
                    logger,
                    "LongBench scripted loading is unsupported for %s/%s; trying data-file fallback.",
                    dataset_id,
                    task,
                )
            else:
                _warning(logger, "LongBench load failed for %s/%s: %s", dataset_id, task, exc)
    return None


def _load_task_via_hf_data_files(task: str, logger: logging.Logger | None) -> Any | None:
    from datasets import load_dataset

    for dataset_id, file_format, url_template in LONGBENCH_HF_DATA_FILES:
        url = url_template.format(task=task)
        try:
            return load_dataset(file_format, data_files=url, split="train")
        except Exception as exc:  # pragma: no cover - network/runtime dependent
            _warning(
                logger,
                "LongBench data-file fallback failed for %s/%s via %s: %s",
                dataset_id,
                task,
                file_format,
                exc,
            )
    zip_records = _load_task_from_thudm_zip(task, logger)
    if zip_records is not None:
        return zip_records
    return None


def _load_task_from_thudm_zip(
    task: str, logger: logging.Logger | None
) -> list[dict[str, Any]] | None:
    try:
        from huggingface_hub import hf_hub_download

        archive_path = hf_hub_download(
            repo_id="THUDM/LongBench",
            repo_type="dataset",
            filename="data.zip",
        )
        member = f"data/{task}.jsonl"
        with zipfile.ZipFile(archive_path) as archive:
            if member not in archive.namelist():
                _warning(logger, "LongBench data.zip does not contain %s", member)
                return None
            records: list[dict[str, Any]] = []
            with archive.open(member) as handle:
                for raw_line in handle:
                    try:
                        payload = json.loads(raw_line.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        continue
                    if isinstance(payload, dict):
                        records.append(payload)
            if records:
                _info(logger, "Loaded LongBench %s from THUDM/LongBench data.zip", task)
                return records
    except Exception as exc:  # pragma: no cover - network/runtime dependent
        _warning(logger, "LongBench data.zip fallback failed for %s: %s", task, exc)
    return None


def _longbench_reasoning(task: str) -> str:
    normalized = task.lower()
    if normalized in LONGBENCH_MULTI_HOP_TASKS:
        return "multi_hop"
    if normalized in LONGBENCH_RETRIEVAL_TASKS:
        return "retrieval"
    if normalized in LONGBENCH_SUMMARIZATION_TASKS:
        return "summarization"
    return "unknown"


def _longbench_answer_type(answer_value: Any, answer: str) -> str:
    if isinstance(answer_value, (list, tuple)):
        return "list"
    return "string" if answer else "unknown"


def _scripts_unsupported(exc: Exception) -> bool:
    message = str(exc).lower()
    return "dataset scripts are no longer supported" in message or "found longbench.py" in message


def _warning(logger: logging.Logger | None, message: str, *args: Any) -> None:
    if logger is not None:
        logger.warning(message, *args)


def _info(logger: logging.Logger | None, message: str, *args: Any) -> None:
    if logger is not None:
        logger.info(message, *args)
