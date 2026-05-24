from longcue.methods.evidence_first import _normalize_selected_evidence
from longcue.utils.json_parser import extract_passage_map
from longcue.prompts.templates import evidence_extraction_prompt, evidence_compression_prompt


def test_extract_passage_map_recovers_canonical_text() -> None:
    context = (
        "[passage_id: p0001] NovaMind-00228 was acquired by Arcturus Systems 00228.\n\n"
        "[passage_id: p0002] Arcturus Systems 00228 is headquartered in Zurich-00228.\n\n"
        "[passage_id: p0003] A draft claims the headquarters is Toronto."
    )
    passage_map = extract_passage_map(context)
    assert passage_map["p0001"] == "NovaMind-00228 was acquired by Arcturus Systems 00228."
    assert passage_map["p0002"] == "Arcturus Systems 00228 is headquartered in Zurich-00228."
    assert passage_map["p0003"] == "A draft claims the headquarters is Toronto."


def test_evidence_first_uses_canonical_text_not_model_text() -> None:
    context = (
        "[passage_id: p0001] NovaMind-00228 was acquired by Arcturus Systems 00228.\n\n"
        "[passage_id: p0002] Arcturus Systems 00228 is headquartered in Zurich-00228."
    )
    passage_map = extract_passage_map(context)
    selected = _normalize_selected_evidence(
        [
            {
                "evidence_id": "p0001",
                "text": "You are welcome to visit us at our new headquarters in Toronto, Canada.",
                "relevance_score": 0.85,
            }
        ],
        available_passage_ids=["p0001", "p0002"],
        passage_text_by_id=passage_map,
    )
    assert selected == [
        {
            "evidence_id": "p0001",
            "text": "NovaMind-00228 was acquired by Arcturus Systems 00228.",
            "relevance_score": 0.85,
        }
    ]


def test_evidence_extraction_warns_against_conflicting_distractors() -> None:
    prompt = evidence_extraction_prompt(
        "Where is the company that acquired NovaMind headquartered?",
        "[passage_id: p0001] NovaMind was acquired by Arcturus.\n\n[passage_id: p0002] Arcturus is headquartered in Zurich.",
        reasoning_type="multi_hop",
        answer_type="entity",
    )
    assert "jointly sufficient" in prompt
    assert "intermediate entity" in prompt
    assert "conflicting distractor" in prompt
    assert "do not rewrite, infer, or invent passage text" in prompt


def test_evidence_compression_forbids_outside_facts() -> None:
    prompt = evidence_compression_prompt(
        "Where is the company headquartered?",
        [{"evidence_id": "p0002", "text": "Arcturus is headquartered in Zurich-00228."}],
        reasoning_type="multi_hop",
        answer_type="entity",
    )
    assert "Use only the selected passages" in prompt
    assert "do not add outside facts" in prompt
    assert "Preserve exact entity names" in prompt
