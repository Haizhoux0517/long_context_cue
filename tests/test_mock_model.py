import json
import random

from longcue.data.controlled_generator import make_controlled_task
from longcue.models.mock import MockModelClient
from longcue.prompts.templates import evidence_answer_prompt, oracle_prompt, verification_prompt


def test_mock_oracle_answers_five_digit_controlled_samples() -> None:
    client = MockModelClient()
    for reasoning_type in ("single_hop", "multi_hop", "comparison", "arithmetic"):
        question, answer, _, evidence = make_controlled_task(
            reasoning_type, "00000", random.Random(11)
        )
        payload = json.loads(client.generate(oracle_prompt(question, evidence)))
        assert payload["answer"] == answer
        assert payload["evidence_ids"] == [item.evidence_id for item in evidence]


def test_mock_evidence_first_answer_routes_from_top_level_task_without_passages() -> None:
    client = MockModelClient()
    prompt = evidence_answer_prompt(
        "Who found the map?",
        "TASK: EVIDENCE_COMPRESSION\nSelected evidence:\n(none)",
        [],
    )
    payload = json.loads(client.generate(prompt))
    assert set(payload) >= {"answer", "evidence_ids", "explanation"}
    assert payload["evidence_ids"] == []


def test_mock_evidence_first_verify_supports_no_selected_passages() -> None:
    client = MockModelClient()
    prompt = verification_prompt(
        "Who found the map?",
        {"answer": "unknown", "evidence_ids": [], "explanation": ""},
        [],
    )
    payload = json.loads(client.generate(prompt))
    assert payload["is_supported"] is True
    assert payload["supporting_evidence_ids"] == []
