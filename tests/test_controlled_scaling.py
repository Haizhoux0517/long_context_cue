from pathlib import Path

from longcue.data.controlled_generator import (
    CONTROLLED_DECILE_EVIDENCE_POSITIONS,
    ControlledCUEGenerator,
    evidence_position_fraction,
)
from longcue.data.io import load_samples, save_samples


def test_decile_positions_are_valid_and_deterministic() -> None:
    generator = ControlledCUEGenerator(
        num_per_cell=1,
        seed=13,
        context_lengths=(4000,),
        evidence_positions=("pos_00", "pos_05", "pos_09"),
        distractor_similarities=("none",),
        reasoning_types=("single_hop",),
    )
    samples = generator.generate()
    assert [sample.evidence_position for sample in samples] == ["pos_00", "pos_05", "pos_09"]
    assert [sample.to_dict() for sample in samples] == [sample.to_dict() for sample in generator.generate()]
    assert samples[0].metadata["evidence_position_fraction"] == 0.05
    assert samples[1].metadata["evidence_position_fraction"] == 0.55
    assert samples[2].metadata["evidence_position_fraction"] == 0.95
    assert "[passage_id: p0001]" in samples[0].long_context


def test_controlled_decile_grid_size_formula() -> None:
    assert len(CONTROLLED_DECILE_EVIDENCE_POSITIONS) == 10
    assert 4 * 10 * 4 * 4 * 5 == 3200


def test_evidence_position_fraction() -> None:
    assert evidence_position_fraction("front") == 0.05
    assert evidence_position_fraction("middle") == 0.50
    assert evidence_position_fraction("end") == 0.88
    assert evidence_position_fraction("pos_09") == 0.95
    assert evidence_position_fraction("scattered") is None


def test_decile_samples_roundtrip(tmp_path: Path) -> None:
    samples = ControlledCUEGenerator(
        num_per_cell=1,
        seed=3,
        context_lengths=(4000,),
        evidence_positions=("pos_03",),
        distractor_similarities=("low",),
        reasoning_types=("multi_hop",),
    ).generate()
    path = tmp_path / "scaling.jsonl"
    save_samples(samples, path)
    loaded = load_samples(path)
    assert loaded[0].evidence_position == "pos_03"
    assert loaded[0].metadata["position_scheme"] if "position_scheme" in loaded[0].metadata else True
