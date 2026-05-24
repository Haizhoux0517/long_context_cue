from longcue.methods.common import parse_answer
from longcue.utils.json_parser import extract_json_object, parse_json_response


def test_extract_json_object_from_messy_text() -> None:
    parsed = extract_json_object('prefix ```json\n{"answer": "A", "evidence_ids": ["e1"]}\n```')
    assert parsed == {"answer": "A", "evidence_ids": ["e1"]}


def test_parse_json_response_uses_structured_fallback() -> None:
    parsed = parse_json_response(
        "not json",
        expected_fields=("answer", "evidence_ids"),
        fallback={"answer": "", "evidence_ids": []},
    )
    assert parsed["answer"] == ""
    assert parsed["evidence_ids"] == []
    assert parsed["parse_error"] == "json_object_not_found"


def test_parse_json_response_marks_missing_fields() -> None:
    parsed = parse_json_response(
        '{"answer": "Nova"}',
        expected_fields=("answer", "evidence_ids"),
        fallback={"answer": "", "evidence_ids": []},
    )
    assert parsed["answer"] == "Nova"
    assert parsed["evidence_ids"] == []
    assert parsed["parse_error"] == "missing_fields:evidence_ids"


def test_parse_json_response_handles_json_only_output() -> None:
    parsed = parse_json_response(
        '{"answer": "Nova", "evidence_ids": ["p0001"]}',
        expected_fields=("answer", "evidence_ids"),
        fallback={"answer": "", "evidence_ids": []},
    )
    assert parsed == {"answer": "Nova", "evidence_ids": ["p0001"]}


def test_parse_json_response_handles_small_surrounding_text() -> None:
    parsed = parse_json_response(
        'Result:\n{"answer": "Nova", "evidence_ids": ["p0001"]}\nDone.',
        expected_fields=("answer", "evidence_ids"),
        fallback={"answer": "", "evidence_ids": []},
    )
    assert parsed["answer"] == "Nova"
    assert parsed["evidence_ids"] == ["p0001"]


def test_parse_answer_normalizes_filters_and_truncates_evidence_ids() -> None:
    parsed = parse_answer(
        '{"answer": "Nova", "evidence_ids": ["999", "235", "p236", "p0237", "238"], "explanation": "short"}',
        passage_text=(
            "[passage_id: p0235] alpha\n"
            "[passage_id: p0236] beta\n"
            "[passage_id: p0237] gamma\n"
            "[passage_id: p0238] delta"
        ),
    )
    assert parsed["evidence_ids"] == ["p0235", "p0236", "p0237"]


def test_parse_answer_rejects_passage_reference_answer() -> None:
    parsed = parse_answer(
        '{"answer": "section_234", "evidence_ids": ["p0001"], "explanation": "short"}',
        passage_text="[passage_id: p0001] section text",
    )
    assert parsed["answer"] == ""
    assert parsed["answer_validation_error"] == "passage_reference_answer"
