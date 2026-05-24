from longcue.data.generator import ControlledBenchmarkGenerator
from longcue.utils.token_utils import estimate_tokens


def test_generator_is_deterministic_and_populates_schema() -> None:
    first = ControlledBenchmarkGenerator(
        sample_count=3, seed=21, context_lengths=(4000,)
    ).generate()
    second = ControlledBenchmarkGenerator(
        sample_count=3, seed=21, context_lengths=(4000,)
    ).generate()
    assert [sample.to_dict() for sample in first] == [sample.to_dict() for sample in second]
    assert len(first) == 3
    assert first[0].gold_evidence_ids
    assert "[passage_id:" in first[0].long_context
    assert "[evidence_id:" not in first[0].long_context
    assert "[distractor_id:" not in first[0].long_context
    assert estimate_tokens(first[0].long_context) == 4000
