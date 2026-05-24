from longcue.data.babilong_adapter import convert_babilong_records


def test_babilong_mock_record_uses_input_question_and_target() -> None:
    samples, stats = convert_babilong_records(
        [{"input": "Mary went to the kitchen.", "question": "Where is Mary?", "target": "kitchen"}],
        config="8k",
        task="qa1",
    )
    assert stats["converted"] == 1
    assert samples[0].source == "babilong"
    assert samples[0].gold_answer == "kitchen"
    assert "[passage_id: p0001]" in samples[0].long_context
    assert samples[0].metadata["config"] == "8k"
    assert samples[0].metadata["cue_applicable"] is False
    assert samples[0].oracle_evidence == []
