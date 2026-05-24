from __future__ import annotations

from collections.abc import Iterable


def evidence_scores(
    predicted_ids: Iterable[str], gold_ids: Iterable[str]
) -> dict[str, float]:
    predicted = set(predicted_ids)
    gold = set(gold_ids)
    overlap = predicted.intersection(gold)
    precision = len(overlap) / len(predicted) if predicted else 0.0
    recall = len(overlap) / len(gold) if gold else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall > 0
        else 0.0
    )
    return {
        "evidence_precision": precision,
        "evidence_recall": recall,
        "evidence_f1": f1,
    }


def citation_grounding(predicted_ids: Iterable[str], gold_ids: Iterable[str]) -> float:
    return float(bool(set(predicted_ids).intersection(gold_ids)))
