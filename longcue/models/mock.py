from __future__ import annotations

import json
import re

from .base import BaseModelClient

PASSAGE_PATTERN = re.compile(r"\[passage_id:\s*([^\]]+)\]\s*([^\n]+)")


class MockModelClient(BaseModelClient):
    """Deterministic offline client for tests and reproducible smoke runs."""

    def __init__(self, model_name: str = "mock") -> None:
        self.model_name = model_name

    def generate(
        self, prompt: str, max_tokens: int = 512, temperature: float = 0.0
    ) -> str:
        del max_tokens, temperature
        task = _top_level_task(prompt)
        if task in {"EVIDENCE_EXTRACTION", "EVIDENCE_SELECTION_PROBE"}:
            return self._extract_evidence(prompt)
        if task in {"EVIDENCE_COMPRESSION", "EVIDENCE_SUMMARY_PROBE"}:
            return self._compress_evidence(prompt)
        if task in {"EVIDENCE_FIRST_VERIFY", "VERIFY_ANSWER", "EVIDENCE_SUFFICIENCY_PROBE"}:
            evidence_ids = _evidence_ids(prompt)
            return json.dumps(
                {
                    "is_supported": True,
                    "supporting_evidence_ids": evidence_ids,
                    "verification_explanation": (
                        "Selected evidence supports the synthetic answer."
                        if evidence_ids
                        else "No passage IDs were available in the selected evidence."
                    ),
                }
            )
        if task == "NO_EVIDENCE":
            return json.dumps(
                {
                    "answer": "unknown",
                    "evidence_ids": [],
                    "explanation": "No supporting evidence was provided.",
                }
            )
        if task in {"EVIDENCE_FIRST_ANSWER", "EVIDENCE_SELECTION_ANSWER_PROBE"}:
            return _answer_response(prompt)
        return _answer_response(prompt)

    def _extract_evidence(self, prompt: str) -> str:
        selected = [
            {
                "evidence_id": evidence_id,
                "text": text.strip(),
                "relevance_score": 1.0,
            }
            for evidence_id, text in PASSAGE_PATTERN.findall(prompt)
        ]
        unique: dict[str, dict[str, object]] = {}
        for item in selected:
            unique.setdefault(str(item["evidence_id"]), item)
        return json.dumps({"selected_evidence": list(unique.values())})

    def _compress_evidence(self, prompt: str) -> str:
        evidence_text = " ".join(text for _, text in PASSAGE_PATTERN.findall(prompt))
        if not evidence_text:
            evidence_text = prompt[-700:]
        return json.dumps({"evidence_summary": evidence_text[:1200]})


def _top_level_task(prompt: str) -> str:
    for line in prompt.lstrip().splitlines()[:8]:
        stripped = line.strip()
        if stripped.startswith("TASK:"):
            return stripped.removeprefix("TASK:").strip()
    return ""


def _answer_response(prompt: str) -> str:
    evidence_ids = _evidence_ids(prompt)
    answer = _infer_answer(prompt)
    return json.dumps(
        {
            "answer": answer,
            "evidence_ids": evidence_ids,
            "explanation": (
                "The cited synthetic evidence contains the answer."
                if answer != "unknown"
                else "The answer was not found in the supplied evidence."
            ),
        }
    )


def _evidence_ids(prompt: str) -> list[str]:
    return list(dict.fromkeys(identifier.strip() for identifier, _ in PASSAGE_PATTERN.findall(prompt)))


def _infer_answer(prompt: str) -> str:
    if "higher benchmark score" in prompt:
        scores = [
            (project.strip(), int(score))
            for project, score in re.findall(
                r"(Project [A-Za-z]+ \d+) scored (\d+)", prompt
            )
        ]
        if scores:
            return max(scores, key=lambda item: item[1])[0]
    if "achieved higher accuracy" in prompt:
        accuracies = [
            (model.strip(), float(score))
            for model, score in re.findall(
                r"(Model [A-Za-z]+ \d+) achieved ([\d.]+) accuracy", prompt
            )
        ]
        if accuracies:
            return max(accuracies, key=lambda item: item[1])[0]
    if "How many more records" in prompt:
        atlas = re.search(r"Atlas unit processed (\d+) records", prompt)
        borealis = re.search(r"Borealis unit processed (\d+) records", prompt)
        if atlas and borealis:
            return str(int(atlas.group(1)) - int(borealis.group(1)))
    if "How many samples are there in total" in prompt:
        counts = [
            int(count)
            for count in re.findall(r"Dataset [AB] \d+ contains (\d+) samples", prompt)
        ]
        if len(counts) >= 2:
            return str(sum(counts[:2]))
    if "headquartered" in prompt:
        city = re.search(r"headquartered in ([A-Za-z -]+\d+)", prompt)
        if city:
            return city.group(1).strip()
    acquirer = re.search(r"acquired by ([A-Za-z ]+\d+)", prompt)
    if acquirer:
        return acquirer.group(1).strip()
    return "unknown"
