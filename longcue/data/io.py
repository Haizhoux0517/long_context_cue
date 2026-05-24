from __future__ import annotations

import gzip
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .schema import BenchmarkSample


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}") from exc
    return records


def load_samples(path: str | Path) -> list[BenchmarkSample]:
    return [BenchmarkSample.from_dict(record) for record in load_jsonl(path)]


def save_jsonl(records: Iterable[dict[str, Any]], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    opener = gzip.open if output_path.suffix == ".gz" else Path.open
    with opener(output_path, "wt", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True))
            handle.write("\n")
    return output_path


def save_samples(samples: Iterable[BenchmarkSample], path: str | Path) -> Path:
    return save_jsonl((sample.to_dict() for sample in samples), path)
