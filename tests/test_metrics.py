import pytest

from longcue.evaluation.answer_metrics import (
    exact_match,
    exact_match_relaxed,
    token_f1,
    token_f1_relaxed,
)
from longcue.evaluation.evidence_metrics import citation_grounding, evidence_scores
from longcue.evaluation.normalization import normalize_answer


def test_answer_normalization_and_exact_match() -> None:
    assert normalize_answer("The Arcturus Systems.") == "arcturus systems"
    assert exact_match("Arcturus Systems", "the Arcturus Systems.") == 1.0
    assert exact_match("Helios", "Arcturus") == 0.0


def test_token_f1() -> None:
    assert token_f1("Meridian City", "Meridian City 0001") == pytest.approx(0.8)
    assert token_f1("", "answer") == 0.0


def test_relaxed_metrics_keep_strict_copy_behavior() -> None:
    assert exact_match("Zurich", "Zurich") == 1.0
    assert exact_match("Zurich", "Zurich-00228") == 0.0


def test_relaxed_metrics_fold_accents_and_synthetic_suffixes() -> None:
    assert exact_match_relaxed(
        "Zürich", "Zurich-00228", answer_type="entity", reasoning_type="multi_hop"
    ) == 1.0
    assert token_f1_relaxed(
        "Arcturus Systems",
        "Arcturus Systems 00563",
        answer_type="entity",
        reasoning_type="single_hop",
    ) == pytest.approx(1.0)


def test_relaxed_metrics_preserve_arithmetic_numbers() -> None:
    assert exact_match_relaxed(
        "51", "00051", answer_type="number", reasoning_type="arithmetic"
    ) == 0.0
    assert token_f1_relaxed(
        "51", "00051", answer_type="number", reasoning_type="arithmetic"
    ) == 0.0


def test_evidence_metrics() -> None:
    scores = evidence_scores(["p0001", "p0003"], ["p0001", "p0002"])
    assert scores["evidence_precision"] == pytest.approx(0.5)
    assert scores["evidence_recall"] == pytest.approx(0.5)
    assert scores["evidence_f1"] == pytest.approx(0.5)
    assert citation_grounding(["p0003", "p0002"], ["p0001", "p0002"]) == 1.0
