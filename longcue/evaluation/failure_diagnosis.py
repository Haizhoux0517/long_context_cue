from __future__ import annotations

from collections.abc import Iterable

MULTI_EVIDENCE_REASONING = {
    "multi_hop",
    "comparison",
    "arithmetic",
    "contradiction",
}


def diagnose_failure(
    gold_evidence_ids: Iterable[str],
    predicted_evidence_ids: Iterable[str],
    answer_correct: bool,
    reasoning_type: str,
) -> str:
    gold = set(gold_evidence_ids)
    predicted = set(predicted_evidence_ids)
    if answer_correct:
        return "success"
    if not predicted:
        return "evidence_localization_failure"
    overlap = gold.intersection(predicted)
    if not overlap:
        return "evidence_selection_failure"
    missing_gold = gold.difference(predicted)
    extra_evidence = predicted.difference(gold)
    if reasoning_type in MULTI_EVIDENCE_REASONING and missing_gold:
        return "evidence_integration_failure"
    if extra_evidence:
        return "evidence_selection_failure"
    if gold.issubset(predicted):
        return "answer_conversion_failure"
    return "evidence_integration_failure"
