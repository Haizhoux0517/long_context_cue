from __future__ import annotations

import csv
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from statistics import mean
from typing import Any

AGGREGATE_GROUP_FIELDS = (
    "source",
    "model_name",
    "method",
    "reasoning_type",
    "context_length",
    "evidence_position",
    "evidence_density",
    "distractor_similarity",
)

MEAN_FIELDS = (
    "exact_match_strict",
    "answer_f1_strict",
    "exact_match_relaxed",
    "answer_f1_relaxed",
    "exact_match",
    "answer_f1",
    "evidence_precision",
    "evidence_recall",
    "evidence_f1",
    "citation_grounding",
)


def aggregate_metrics(
    metric_records: Iterable[dict[str, Any]],
    group_fields: tuple[str, ...] = AGGREGATE_GROUP_FIELDS,
) -> list[dict[str, Any]]:
    buckets: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for record in metric_records:
        buckets[tuple(record.get(field, "unknown") for field in group_fields)].append(record)

    rows: list[dict[str, Any]] = []
    for key, records in sorted(buckets.items(), key=lambda item: str(item[0])):
        row = dict(zip(group_fields, key))
        row["n"] = len(records)
        for field in MEAN_FIELDS:
            row[field] = mean(float(record[field]) for record in records)
        rows.append(row)
    return rows


def robustness_drop_rows(
    metric_records: Iterable[dict[str, Any]], score_field: str = "exact_match"
) -> list[dict[str, Any]]:
    group_fields = (
        "source",
        "model_name",
        "method",
        "reasoning_type",
        "context_length",
        "evidence_position",
        "evidence_density",
    )
    buckets: dict[tuple[Any, ...], dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for record in metric_records:
        key = tuple(record.get(field, "unknown") for field in group_fields)
        buckets[key][str(record["distractor_similarity"])].append(
            float(record[score_field])
        )

    rows: list[dict[str, Any]] = []
    for key, scores in sorted(buckets.items(), key=lambda item: str(item[0])):
        if "none" not in scores:
            continue
        baseline = mean(scores["none"])
        for setting in ("high", "conflicting"):
            if setting not in scores:
                continue
            row = dict(zip(group_fields, key))
            row.update(
                {
                    "score_field": score_field,
                    "distractor_similarity": setting,
                    "score_none": baseline,
                    "score_distractor": mean(scores[setting]),
                    "robustness_drop": baseline - mean(scores[setting]),
                    "n_none": len(scores["none"]),
                    "n_distractor": len(scores[setting]),
                }
            )
            rows.append(row)
    return rows


def write_csv(rows: Iterable[dict[str, Any]], path: str | Path) -> Path:
    serialized = list(rows)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = _fieldnames(serialized)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(serialized)
    return output_path


def write_markdown_table(rows: Iterable[dict[str, Any]], path: str | Path) -> Path:
    serialized = list(rows)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = _fieldnames(serialized)
    with output_path.open("w", encoding="utf-8") as handle:
        if not fieldnames:
            handle.write("_No rows._\n")
            return output_path
        handle.write("| " + " | ".join(fieldnames) + " |\n")
        handle.write("| " + " | ".join("---" for _ in fieldnames) + " |\n")
        for row in serialized:
            values = [_format_cell(row.get(field, "")) for field in fieldnames]
            handle.write("| " + " | ".join(values) + " |\n")
    return output_path


def _fieldnames(rows: list[dict[str, Any]]) -> list[str]:
    fieldnames: list[str] = []
    for row in rows:
        for field in row:
            if field not in fieldnames:
                fieldnames.append(field)
    return fieldnames


def _format_cell(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value).replace("|", "\\|").replace("\n", " ")
