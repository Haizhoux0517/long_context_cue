from longcue.data.adapter_utils import sample_from_parts
from longcue.data.schema import Distractor, Evidence
from longcue.data.stats import dataset_stats, write_dataset_stats


def test_dataset_stats_and_writers(tmp_path) -> None:
    samples = [
        sample_from_parts(
            sample_id="c1",
            source="controlled",
            question="Q1?",
            gold_answer="A1",
            long_context="word " * 20,
            oracle_evidence=[Evidence("e1", "gold")],
            distractors=[Distractor("d1", "noise")],
            context_length=20,
            evidence_position="front",
            evidence_density="low",
            distractor_similarity="high",
            reasoning_type="single_hop",
        ),
        sample_from_parts(
            sample_id="l1",
            source="longbench",
            question="Q2?",
            gold_answer="A2",
            long_context="word " * 10,
            context_length=10,
        ),
    ]
    report = dataset_stats(samples)
    assert report["num_samples"] == 2
    assert report["missing_oracle_evidence_count"] == 1
    assert report["distributions"]["source"] == {"controlled": 1, "longbench": 1}
    artifacts = write_dataset_stats(
        report, dataset_path="demo.jsonl", output_dir=tmp_path / "stats"
    )
    assert artifacts["csv"].exists()
    assert artifacts["markdown"].exists()
