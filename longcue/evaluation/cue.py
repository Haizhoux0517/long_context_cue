from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from statistics import mean
from typing import Any

CUE_GROUP_FIELDS = (
    "source",
    "model_name",
    "reasoning_type",
    "context_length",
    "evidence_position",
    "evidence_density",
    "distractor_similarity",
)


def compute_cue(
    score_no_evidence: float,
    score_oracle: float,
    score_long: float,
) -> dict[str, float]:
    denominator = score_oracle - score_no_evidence
    if denominator <= 0:
        raise ValueError("CUE requires oracle score above no-evidence score.")
    raw = (score_long - score_no_evidence) / denominator
    return {"cue_raw": raw, "cue_clipped": min(max(raw, 0.0), 1.0)}


def compute_cue_rows(
    metric_records: Iterable[dict[str, Any]],
    score_field: str = "exact_match",
    group_fields: tuple[str, ...] = CUE_GROUP_FIELDS,
) -> list[dict[str, Any]]:
    grouped_scores: dict[tuple[Any, ...], dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for record in metric_records:
        key = tuple(record.get(field, "unknown") for field in group_fields)
        grouped_scores[key][str(record["method"])].append(record)

    rows: list[dict[str, Any]] = []
    for key, method_records in grouped_scores.items():
        long_methods = sorted(
            method for method in method_records if method not in {"no_evidence", "oracle"}
        )
        for method in long_methods:
            records = method_records[method]
            row = dict(zip(group_fields, key))
            score_no = _mean_score(method_records.get("no_evidence", []), score_field)
            score_oracle = _mean_score(method_records.get("oracle", []), score_field)
            score_long = _mean_score(records, score_field)
            invalid_reason = _invalid_reason(method_records, score_no, score_oracle)
            row.update(
                {
                    "long_method": method,
                    "score_field": score_field,
                    "score_no_evidence": score_no,
                    "score_oracle": score_oracle,
                    "score_long": score_long,
                    "n": len(records),
                    "cue_valid": not bool(invalid_reason),
                    "cue_invalid_reason": invalid_reason,
                    "cue_raw": "",
                    "cue_clipped": "",
                }
            )
            if not invalid_reason and score_no is not None and score_oracle is not None and score_long is not None:
                row.update(compute_cue(score_no, score_oracle, score_long))
            rows.append(row)
    return rows


def _mean_score(records: list[dict[str, Any]], score_field: str) -> float | None:
    if not records:
        return None
    return mean(float(record[score_field]) for record in records)


def _invalid_reason(
    method_records: dict[str, list[dict[str, Any]]],
    score_no: float | None,
    score_oracle: float | None,
) -> str:
    if not method_records.get("no_evidence"):
        return "missing_no_evidence"
    if not method_records.get("oracle"):
        return "missing_oracle"
    if any(
        not bool(record.get("cue_applicable", False))
        for records in method_records.values()
        for record in records
    ):
        return "empty_oracle_evidence"
    if score_no is None or score_oracle is None:
        return "missing_oracle"
    if score_oracle <= score_no:
        return "oracle_not_above_no_evidence"
    return ""
