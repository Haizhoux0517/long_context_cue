from __future__ import annotations

from collections import Counter

from .normalization import (
    answer_tokens,
    answer_tokens_relaxed,
    normalize_answer,
    normalize_answer_relaxed,
)


def exact_match(prediction: str, gold_answer: str) -> float:
    return float(normalize_answer(prediction) == normalize_answer(gold_answer))


def token_f1(prediction: str, gold_answer: str) -> float:
    return _token_f1(answer_tokens(prediction), answer_tokens(gold_answer))


def exact_match_relaxed(
    prediction: str,
    gold_answer: str,
    *,
    answer_type: str = "unknown",
    reasoning_type: str = "unknown",
) -> float:
    return float(
        normalize_answer_relaxed(
            prediction, answer_type=answer_type, reasoning_type=reasoning_type
        )
        == normalize_answer_relaxed(
            gold_answer, answer_type=answer_type, reasoning_type=reasoning_type
        )
    )


def token_f1_relaxed(
    prediction: str,
    gold_answer: str,
    *,
    answer_type: str = "unknown",
    reasoning_type: str = "unknown",
) -> float:
    return _token_f1(
        answer_tokens_relaxed(
            prediction, answer_type=answer_type, reasoning_type=reasoning_type
        ),
        answer_tokens_relaxed(
            gold_answer, answer_type=answer_type, reasoning_type=reasoning_type
        ),
    )


def _token_f1(predicted_tokens: list[str], gold_tokens: list[str]) -> float:
    if not predicted_tokens and not gold_tokens:
        return 1.0
    if not predicted_tokens or not gold_tokens:
        return 0.0
    overlap = Counter(predicted_tokens) & Counter(gold_tokens)
    common = sum(overlap.values())
    if common == 0:
        return 0.0
    precision = common / len(predicted_tokens)
    recall = common / len(gold_tokens)
    return 2 * precision * recall / (precision + recall)
