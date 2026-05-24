import pytest

from longcue.evaluation.cue import compute_cue, compute_cue_rows


def test_compute_raw_and_clipped_cue() -> None:
    scores = compute_cue(0.2, 0.8, 0.5)
    assert scores["cue_raw"] == pytest.approx(0.5)
    assert scores["cue_clipped"] == pytest.approx(0.5)


def test_compute_cue_rejects_oracle_not_above_baseline() -> None:
    with pytest.raises(ValueError):
        compute_cue(0.4, 0.4, 0.6)


def test_compute_cue_rows_groups_long_method() -> None:
    base = {
        "model_name": "mock",
        "reasoning_type": "single_hop",
        "context_length": 4000,
        "evidence_position": "front",
        "evidence_density": "low",
        "distractor_similarity": "none",
        "cue_applicable": True,
    }
    rows = compute_cue_rows(
        [
            base | {"method": "no_evidence", "exact_match": 0.0},
            base | {"method": "oracle", "exact_match": 1.0},
            base | {"method": "direct", "exact_match": 1.0},
        ]
    )
    assert rows[0]["long_method"] == "direct"
    assert rows[0]["cue_valid"] is True
    assert rows[0]["cue_clipped"] == 1.0


def test_compute_cue_rows_invalid_when_oracle_evidence_empty() -> None:
    base = {
        "model_name": "mock",
        "reasoning_type": "retrieval",
        "context_length": 4000,
        "evidence_position": "unknown",
        "evidence_density": "unknown",
        "distractor_similarity": "unknown",
        "cue_applicable": False,
    }
    rows = compute_cue_rows(
        [
            base | {"method": "no_evidence", "exact_match": 0.0},
            base | {"method": "oracle", "exact_match": 1.0},
            base | {"method": "direct", "exact_match": 0.5},
        ]
    )
    assert rows[0]["cue_valid"] is False
    assert rows[0]["cue_invalid_reason"] == "empty_oracle_evidence"
    assert rows[0]["cue_raw"] == ""


def test_compute_cue_rows_invalid_when_oracle_not_above_no_evidence() -> None:
    base = {
        "model_name": "mock",
        "reasoning_type": "single_hop",
        "context_length": 4000,
        "evidence_position": "front",
        "evidence_density": "low",
        "distractor_similarity": "none",
        "cue_applicable": True,
    }
    rows = compute_cue_rows(
        [
            base | {"method": "no_evidence", "exact_match": 1.0},
            base | {"method": "oracle", "exact_match": 1.0},
            base | {"method": "direct", "exact_match": 1.0},
        ]
    )
    assert rows[0]["cue_valid"] is False
    assert rows[0]["cue_invalid_reason"] == "oracle_not_above_no_evidence"
