from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .io import load_jsonl, save_samples
from .schema import BenchmarkSample


def merge_dataset_paths(
    paths: list[str | Path], output_path: str | Path | None = None
) -> tuple[list[BenchmarkSample], dict[str, Any]]:
    merged: list[BenchmarkSample] = []
    seen_records: set[str] = set()
    seen_ids: set[str] = set()
    stats: Counter[str] = Counter()
    by_source: Counter[str] = Counter()
    for path in paths:
        for raw_record in load_jsonl(path):
            stats["input_records"] += 1
            sample = BenchmarkSample.from_dict(raw_record)
            canonical = json.dumps(sample.to_dict(), sort_keys=True, ensure_ascii=True)
            if canonical in seen_records:
                stats["exact_duplicates_removed"] += 1
                continue
            seen_records.add(canonical)
            if sample.id in seen_ids:
                sample = _with_unique_id(sample, seen_ids)
                stats["ids_rewritten"] += 1
            seen_ids.add(sample.id)
            merged.append(sample)
            by_source[sample.source] += 1
    stats["output_records"] = len(merged)
    summary = dict(stats)
    summary["by_source"] = dict(by_source)
    if output_path is not None:
        save_samples(merged, output_path)
    return merged, summary


def _with_unique_id(sample: BenchmarkSample, seen_ids: set[str]) -> BenchmarkSample:
    base = f"{sample.source}_{sample.id}"
    candidate = base
    suffix = 2
    while candidate in seen_ids:
        candidate = f"{base}_{suffix}"
        suffix += 1
    payload = sample.to_dict()
    payload["id"] = candidate
    return BenchmarkSample.from_dict(payload)
