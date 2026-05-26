from longcue.data.twowiki_adapter import convert_2wikimultihopqa_records, extract_2wiki_evidence


def test_twowiki_hotpot_style_alignment_and_conversion() -> None:
    record = {
        "id": "tw1",
        "question": "Where is the company that acquired NovaMind headquartered?",
        "answer": "Zurich",
        "type": "bridge",
        "context": {
            "title": ["NovaMind", "Arcturus", "Noise"],
            "sentences": [
                ["NovaMind was acquired by Arcturus Systems."],
                ["Arcturus Systems is headquartered in Zurich."],
                ["Noise paragraph is unrelated."],
            ],
        },
        "supporting_facts": {"title": ["NovaMind", "Arcturus"], "sent_id": [0, 0]},
        "evidences": [["NovaMind", "acquired by", "Arcturus Systems"]],
    }
    evidence, distractors = extract_2wiki_evidence(record)
    assert [item.title for item in evidence] == ["NovaMind", "Arcturus"]
    assert distractors[0].title == "Noise"

    samples, stats = convert_2wikimultihopqa_records([record], limit=1, context_lengths=[4000])
    assert stats["converted"] == 1
    assert samples[0].source == "2wikimultihopqa"
    assert samples[0].reasoning_type == "multi_hop"
    assert samples[0].metadata["2wiki_type"] == "bridge"
    assert samples[0].metadata["cue_applicable"] is True
    assert len(samples[0].oracle_evidence) == 2
    assert "[passage_id:" in samples[0].long_context
    assert "[evidence_id:" not in samples[0].long_context


def test_twowiki_skips_unaligned_supporting_facts() -> None:
    samples, stats = convert_2wikimultihopqa_records(
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


def test_twowiki_evidences_text_fallback() -> None:
    record = {
        "id": "tw2",
        "question": "Who founded the organization?",
        "answer": "Ada Lovelace",
        "type": "inference",
        "context": [["Distractor", ["This is unrelated."]]],
        "evidences": [
            {"title": "Analytical Society", "text": "The Analytical Society was founded by Ada Lovelace."}
        ],
    }
    samples, stats = convert_2wikimultihopqa_records([record], limit=1, context_lengths=[4000])
    assert stats["converted"] == 1
    assert samples[0].oracle_evidence[0].title == "Analytical Society"
    assert samples[0].metadata["hop_count"] == 1
