from longcue.data.adapter_utils import sample_from_parts
from longcue.data.io import save_samples
from longcue.data.merge import merge_dataset_paths


def test_merge_deduplicates_and_rewrites_colliding_ids(tmp_path) -> None:
    first = sample_from_parts(
        sample_id="shared",
        source="controlled",
        question="Q1?",
        gold_answer="A1",
        long_context="context one",
        context_length=2,
    )
    second = sample_from_parts(
        sample_id="shared",
        source="longbench",
        question="Q2?",
        gold_answer="A2",
        long_context="context two",
        context_length=2,
    )
    path_a = save_samples([first, first], tmp_path / "a.jsonl")
    path_b = save_samples([second], tmp_path / "b.jsonl")
    merged, stats = merge_dataset_paths([path_a, path_b], tmp_path / "merged.jsonl")
    assert len(merged) == 2
    assert len({sample.id for sample in merged}) == 2
    assert stats["exact_duplicates_removed"] == 1
    assert stats["ids_rewritten"] == 1
