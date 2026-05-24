from __future__ import annotations

from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

from longcue.evaluation.aggregate import write_csv, write_markdown_table

from .schema import BenchmarkSample

DISTRIBUTION_FIELDS = (
    "source",
    "context_length",
    "evidence_position",
    "distractor_similarity",
    "reasoning_type",
)


def dataset_stats(samples: list[BenchmarkSample]) -> dict[str, Any]:
    return {
        "num_samples": len(samples),
        "average_context_length": mean(sample.context_length for sample in samples)
        if samples
        else 0.0,
        "missing_oracle_evidence_count": sum(
            1 for sample in samples if not sample.oracle_evidence
        ),
        "average_oracle_evidence_items": mean(
            len(sample.oracle_evidence) for sample in samples
        )
        if samples
        else 0.0,
        "average_distractors": mean(len(sample.distractors) for sample in samples)
        if samples
        else 0.0,
        "distributions": {
            field: dict(Counter(str(getattr(sample, field)) for sample in samples))
            for field in DISTRIBUTION_FIELDS
        },
    }


def stats_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        {"section": "summary", "metric": key, "value": value, "count": ""}
        for key, value in report.items()
        if key != "distributions"
    ]
    for field, distribution in report.get("distributions", {}).items():
        rows.extend(
            {
                "section": "distribution",
                "metric": field,
                "value": value,
                "count": count,
            }
            for value, count in sorted(distribution.items(), key=lambda item: str(item[0]))
        )
    return rows


def write_dataset_stats(
    report: dict[str, Any],
    *,
    dataset_path: str | Path,
    output_dir: str | Path = "outputs/dataset_stats",
) -> dict[str, Path]:
    stem = Path(dataset_path).stem
    rows = stats_rows(report)
    output = Path(output_dir)
    return {
        "csv": write_csv(rows, output / f"{stem}_stats.csv"),
        "markdown": write_markdown_table(rows, output / f"{stem}_stats.md"),
    }
