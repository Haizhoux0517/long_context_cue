from longcue.prompts.templates import (
    direct_answer_prompt,
    evidence_answer_prompt,
    evidence_extraction_prompt,
)


def test_direct_prompt_uses_rules_without_semantic_examples() -> None:
    prompt = direct_answer_prompt(
        "Where is the target headquartered?",
        "[passage_id: p0001] <context passage>",
        reasoning_type="multi_hop",
        answer_type="entity",
    )
    assert "System X" not in prompt
    assert "Company Y" not in prompt
    assert "system must support multiple users" not in prompt
    assert '"answer": "yes"' not in prompt.lower()
    assert '"answer": "no"' not in prompt.lower()
    assert "Do not answer yes/no unless" in prompt
    assert "Reasoning type: multi_hop" in prompt
    assert "Expected answer type: entity" in prompt


def test_multi_hop_answer_prompt_requires_joint_reasoning() -> None:
    prompt = direct_answer_prompt(
        "What property belongs to the linked entity?",
        "[passage_id: p0001] <context passage>",
        reasoning_type="multi_hop",
        answer_type="entity",
    )
    assert "combine all necessary passages" in prompt


def test_evidence_extraction_prompt_requests_jointly_sufficient_passages() -> None:
    prompt = evidence_extraction_prompt(
        "What is the final result?",
        "[passage_id: p0001] <context passage>",
        reasoning_type="arithmetic",
        answer_type="number",
    )
    assert "jointly sufficient" in prompt
    assert "select all necessary supporting passages" in prompt


def test_evidence_first_answer_places_final_question_before_json_instruction() -> None:
    question = "Where is the linked entity headquartered?"
    prompt = evidence_answer_prompt(
        question,
        "<evidence summary>",
        [{"evidence_id": "p0001", "text": "<selected passage text>"}],
        reasoning_type="multi_hop",
        answer_type="entity",
    )
    question_marker = f"Final question: {question}"
    assert question_marker in prompt
    tail = prompt.split(question_marker, maxsplit=1)[1].lstrip()
    assert tail.startswith("Return exactly one JSON object")
