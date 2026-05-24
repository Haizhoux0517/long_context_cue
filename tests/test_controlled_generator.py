from longcue.data.controlled_generator import (
    CONTROLLED_CONTEXT_LENGTHS,
    CONTROLLED_DISTRACTOR_SIMILARITIES,
    CONTROLLED_EVIDENCE_POSITIONS,
    CONTROLLED_REASONING_TYPES,
    ControlledCUEGenerator,
)


def test_controlled_generator_grid_and_determinism() -> None:
    generator = ControlledCUEGenerator(
        num_per_cell=2,
        seed=7,
        context_lengths=(4000,),
        evidence_positions=("front", "scattered"),
        distractor_similarities=("none",),
        reasoning_types=("single_hop", "arithmetic"),
    )
    first = generator.generate()
    second = generator.generate()
    assert [sample.to_dict() for sample in first] == [sample.to_dict() for sample in second]
    assert len(first) == 8
    assert first[0].source == "controlled"
    assert first[0].oracle_evidence[0].evidence_id == "p0001"
    assert "[passage_id:" in first[0].long_context
    assert "[evidence_id:" not in first[0].long_context
    assert "[distractor_id:" not in first[0].long_context
    assert f"[passage_id: {first[0].gold_evidence_ids[0]}]" in first[0].long_context


def test_controlled_default_cell_count_formula() -> None:
    assert (
        len(CONTROLLED_CONTEXT_LENGTHS)
        * len(CONTROLLED_EVIDENCE_POSITIONS)
        * len(CONTROLLED_DISTRACTOR_SIMILARITIES)
        * len(CONTROLLED_REASONING_TYPES)
        * 5
        == 1280
    )
