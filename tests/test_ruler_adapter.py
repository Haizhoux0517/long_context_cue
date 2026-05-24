import json

from longcue.data.ruler_adapter import convert_ruler_path, convert_ruler_record, map_ruler_reasoning


def test_ruler_record_inference_and_task_mapping() -> None:
    sample = convert_ruler_record(
        {
            "id": "r1",
            "task": "niah_single",
            "input": "Needle context and question.",
            "question": "What is the key?",
            "outputs": ["value-7"],
            "length": 4096,
        },
        index=0,
    )
    assert sample is not None
    assert sample.source == "ruler"
    assert sample.reasoning_type == "retrieval"
    assert sample.context_length == 4096
    assert sample.metadata["cue_applicable"] is False
    assert map_ruler_reasoning("variable_tracking") == "multi_hop"
    assert map_ruler_reasoning("aggregation") == "aggregation"


def test_ruler_path_skips_invalid_records(tmp_path) -> None:
    nested = tmp_path / "ruler" / "niah"
    nested.mkdir(parents=True)
    with (nested / "samples.jsonl").open("w", encoding="utf-8") as handle:
        handle.write(json.dumps({"input": "Context", "question": "Q?", "answer": "A"}) + "\n")
        handle.write(json.dumps({"input": "Context only"}) + "\n")
    samples, stats = convert_ruler_path(tmp_path / "ruler")
    assert len(samples) == 1
    assert stats["skipped"] == 1
