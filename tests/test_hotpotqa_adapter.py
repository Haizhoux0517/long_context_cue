from longcue.data.hotpotqa_adapter import convert_hotpotqa_records, extract_hotpot_evidence


def test_hotpotqa_dict_alignment_and_conversion() -> None:
    record = {
        "id": "hp1",
        "question": "Where is the acquirer headquartered?",
        "answer": "Zurich",
        "type": "bridge",
        "level": "hard",
        "context": {
            "title": ["NovaMind", "Arcturus", "Noise"],
            "sentences": [
                ["NovaMind was acquired by Arcturus Systems."],
                ["Arcturus Systems is headquartered in Zurich."],
                ["Noise paragraph is unrelated."],
            ],
        },
        "supporting_facts": {"title": ["NovaMind", "Arcturus"], "sent_id": [0, 0]},
    }
    evidence, distractors = extract_hotpot_evidence(record)
    assert [item.title for item in evidence] == ["NovaMind", "Arcturus"]
    assert distractors[0].title == "Noise"

    samples, stats = convert_hotpotqa_records([record], limit=1, context_lengths=[4000])
    assert stats["converted"] == 1
    assert samples[0].source == "hotpotqa"
    assert samples[0].reasoning_type == "multi_hop"
    assert len(samples[0].oracle_evidence) == 2
    assert samples[0].metadata["cue_applicable"] is True
    assert "[evidence_id:" not in samples[0].long_context


def test_hotpotqa_skips_unaligned_supporting_facts() -> None:
    samples, stats = convert_hotpotqa_records(
        [
            {
                "question": "Q?",
                "answer": "A",
                "context": [["Title", ["Sentence."]]],
                "supporting_facts": [["Missing", 0]],
            }
        ],
        context_lengths=[4000],
    )
    assert samples == []
    assert stats["skip_reasons"]["unaligned_supporting_fact"] == 1
