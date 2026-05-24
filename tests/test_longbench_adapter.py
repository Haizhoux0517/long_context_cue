import json

import longcue.data.longbench_adapter as longbench_adapter
from longcue.data.longbench_adapter import (
    convert_longbench_records,
    load_local_longbench_records,
    load_longbench_cue,
)


def test_longbench_mock_records_convert_without_oracle_evidence() -> None:
    samples, stats = convert_longbench_records(
        [
            {
                "_id": "lb1",
                "input": "Who won?",
                "context": "A long article says Meridian won.",
                "answers": ["Meridian"],
            }
        ],
        task="hotpotqa",
    )
    assert stats["converted"] == 1
    assert samples[0].source == "longbench"
    assert samples[0].question == "Who won?"
    assert "[passage_id: p0001]" in samples[0].long_context
    assert samples[0].oracle_evidence == []
    assert samples[0].metadata["cue_applicable"] is False
    assert samples[0].reasoning_type == "multi_hop"
    assert samples[0].answer_type == "list"
    assert samples[0].id == "longbench_hotpotqa_0"


def test_longbench_local_jsonl_fallback_converts_without_network(
    tmp_path, monkeypatch
) -> None:
    local_dir = tmp_path / "LongBench"
    local_dir.mkdir()
    with (local_dir / "narrativeqa.jsonl").open("w", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "context": "The story says Avery crossed the bridge.",
                    "input": "Who crossed the bridge?",
                    "answers": ["Avery"],
                }
            )
            + "\n"
        )
    monkeypatch.setattr(
        longbench_adapter, "_load_task_via_dataset_script", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        longbench_adapter, "_load_task_via_hf_data_files", lambda *args, **kwargs: None
    )
    samples, stats = load_longbench_cue(
        ["narrativeqa"], local_dir=local_dir, limit_per_task=20
    )
    assert len(samples) == 1
    assert stats["tasks"]["narrativeqa"]["load_strategy"] == "local_file"
    assert samples[0].reasoning_type == "retrieval"
    assert samples[0].gold_answer == "Avery"


def test_longbench_local_json_file_supports_field_fallbacks(tmp_path) -> None:
    local_dir = tmp_path / "LongBench"
    local_dir.mkdir()
    (local_dir / "gov_report.json").write_text(
        json.dumps(
            [
                {
                    "document": "A long government report.",
                    "instruction": "Summarize the report.",
                    "label": "A concise summary.",
                }
            ]
        ),
        encoding="utf-8",
    )
    records = load_local_longbench_records(local_dir, "gov_report")
    assert records is not None
    samples, stats = convert_longbench_records(records, task="gov_report")
    assert stats["converted"] == 1
    assert samples[0].long_context.startswith("[passage_id: p0001]")
    assert "A long government report." in samples[0].long_context
    assert samples[0].question == "Summarize the report."
    assert samples[0].reasoning_type == "summarization"
    assert samples[0].answer_type == "string"
