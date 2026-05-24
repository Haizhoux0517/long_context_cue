from __future__ import annotations

"""Fixed instruction templates for diagnostic conditions.

The templates in this module are intentionally static across models and datasets.
They are part of the measurement protocol, not objects of prompt optimization.
"""

import json
from collections.abc import Iterable
from typing import Any

from longcue.data.schema import Evidence, format_evidence

ANSWER_SCHEMA = """Return exactly one JSON object and nothing else. Do not wrap it in Markdown and do not add text before or after it:
{
  "answer": "<final short answer>",
  "evidence_ids": ["p0001"],
  "explanation": "<brief evidence-based explanation>"
}"""

ANSWER_RULES = """Answer rules:
- Answer the final question directly.
- Do not answer yes/no unless the expected answer type is yes_no or the final question itself asks yes/no.
- For entity questions, output the entity name only.
- For number questions, output the number only.
- For comparison questions, output the selected or winning entity, not yes/no.
- For arithmetic questions, output the final computed number only.
- Do not output passage IDs or section IDs as the answer.
- Do not output "unknown" unless the context truly lacks the required information.
- Keep the explanation brief and grounded in the cited passages."""

CITATION_RULES = """Citation rules:
- The evidence_ids field must contain zero to three supporting passage IDs.
- Every evidence ID must exactly match a visible passage ID in the supplied text.
- Do not output raw numeric IDs, section IDs, ranges, or more than three evidence IDs.
- If no visible passage supports the answer, return an empty evidence_ids list."""

MULTI_HOP_RULES = """Reasoning rules:
- For multi-hop questions, combine all necessary passages before answering.
- Do not stop after the first relevant passage.
- If one passage identifies an entity and another passage gives a property of that entity, use both passages."""


def no_evidence_prompt(question: str) -> str:
    return f"""TASK: NO_EVIDENCE
Answer without external evidence. Return an empty evidence_ids list when no passage is supplied.
{ANSWER_RULES}
{CITATION_RULES}
Final question: {question}
{ANSWER_SCHEMA}"""


def oracle_prompt(
    question: str,
    evidence: list[Evidence],
    reasoning_type: str = "unknown",
    answer_type: str = "unknown",
) -> str:
    return direct_answer_prompt(
        question,
        format_evidence(evidence),
        task="ORACLE_ANSWER",
        reasoning_type=reasoning_type,
        answer_type=answer_type,
    )


def direct_answer_prompt(
    question: str,
    context: str,
    task: str = "DIRECT_ANSWER",
    reasoning_type: str = "unknown",
    answer_type: str = "unknown",
) -> str:
    return f"""TASK: {task}
Use the supplied context to answer the final question.
{_task_hints(reasoning_type, answer_type)}
Context:
{context}
{ANSWER_RULES}
{CITATION_RULES}
{MULTI_HOP_RULES}
Final question: {question}
{ANSWER_SCHEMA}"""


def cot_prompt(
    question: str,
    context: str,
    reasoning_type: str = "unknown",
    answer_type: str = "unknown",
) -> str:
    return f"""TASK: CONCISE_REASONING_PROBE
Use the supplied context under the same answer contract as the full-context condition. This is a fixed auxiliary reasoning probe, not a tuned prompt.
{_task_hints(reasoning_type, answer_type)}
Context:
{context}
{ANSWER_RULES}
{CITATION_RULES}
{MULTI_HOP_RULES}
Final question: {question}
{ANSWER_SCHEMA}"""


def evidence_extraction_prompt(
    question: str,
    context: str,
    reasoning_type: str = "unknown",
    answer_type: str = "unknown",
) -> str:
    return f"""TASK: EVIDENCE_SELECTION_PROBE
Select up to three passages that are jointly sufficient to answer the final question.
{_task_hints(reasoning_type, answer_type)}
Extraction rules:
- Select passages that are jointly sufficient to answer the final question, not merely passages that share keywords with it.
- For multi-hop questions, first identify the intermediate entity, then select the passage that gives the requested property of that exact entity.
- For multi-hop questions, do not stop at the first related passage; include the linking passage and the property/value passage when both are needed.
- If a passage mentions the requested property but not the exact intermediate entity, treat it as a possible conflicting distractor rather than sufficient evidence.
- For comparison questions, select the passages containing the compared values for all candidates needed to decide the winner.
- For arithmetic questions, select all passages containing the numbers needed for the calculation.
- For multi-hop, comparison, or arithmetic questions, select all necessary supporting passages, not only the first related passage.
- Use exact visible passage IDs only.
- Do not output raw numeric IDs, section IDs, ranges, large passage spans, or more than three selected_evidence items.
- In the text field, copy the selected passage text exactly as shown; do not rewrite, infer, or invent passage text.
Long context:
{context}
Final question: {question}
Return exactly one JSON object and nothing else:
{{
  "selected_evidence": [
    {{"evidence_id": "p0001", "text": "<selected passage text>", "relevance_score": 0.0}}
  ]
}}"""


def evidence_compression_prompt(
    question: str,
    selected_evidence: Iterable[dict[str, Any]],
    reasoning_type: str = "unknown",
    answer_type: str = "unknown",
) -> str:
    rendered = _render_selected_evidence(selected_evidence)
    return f"""TASK: EVIDENCE_SUMMARY_PROBE
Compress the selected passages for answering the final question.
{_task_hints(reasoning_type, answer_type)}
Compression rules:
- Use only the selected passages shown below; do not add outside facts or infer missing facts.
- Preserve exact entity names, numeric suffixes, dates, locations, and IDs.
- Preserve entities and numbers exactly.
- Preserve the connection between entities across passages, especially intermediate entities in multi-hop questions.
- Do not replace concrete values with generic placeholders.
- Do not summarize away the final answer.
- If the selected passages are insufficient, state precisely what is missing instead of guessing.
Selected evidence:
{rendered}
Final question: {question}
Return exactly one JSON object and nothing else:
{{
  "evidence_summary": "<compressed evidence summary>"
}}"""


def evidence_answer_prompt(
    question: str,
    evidence_summary: str,
    selected_evidence: Iterable[dict[str, Any]],
    reasoning_type: str = "unknown",
    answer_type: str = "unknown",
) -> str:
    rendered = _render_selected_evidence(selected_evidence)
    return f"""TASK: EVIDENCE_SELECTION_ANSWER_PROBE
Answer the final question using the evidence summary and selected passages.
{_task_hints(reasoning_type, answer_type)}
Evidence summary:
{evidence_summary}
Selected evidence:
{rendered}
{ANSWER_RULES}
{CITATION_RULES}
{MULTI_HOP_RULES}
- Copy the answer exactly from the evidence summary whenever possible.
- Use only facts present in the evidence summary or selected passages; do not use outside knowledge.
- Do not replace concrete answers with common entities unless they appear in the selected evidence and directly answer the final question.
- Do not default to "unknown" when the evidence summary contains relevant evidence for the final question.
- If the evidence summary is incomplete, answer only if the selected passages still contain the missing value.
Final question: {question}
{ANSWER_SCHEMA}"""


def verification_prompt(
    question: str,
    answer_payload: dict[str, Any],
    selected_evidence: Iterable[dict[str, Any]],
    reasoning_type: str = "unknown",
    answer_type: str = "unknown",
) -> str:
    return f"""TASK: EVIDENCE_SUFFICIENCY_PROBE
Check whether the answer is supported by the selected passages. Do not use outside knowledge.
{_task_hints(reasoning_type, answer_type)}
Verification rules:
- Report zero to three supporting passage IDs.
- Every supporting evidence ID must exactly match a selected visible passage ID.
- Do not output raw numeric IDs, section IDs, ranges, or more than three supporting evidence IDs.
Answer payload: {json.dumps(answer_payload, ensure_ascii=True)}
Selected evidence:
{_render_selected_evidence(selected_evidence)}
Final question: {question}
Return exactly one JSON object and nothing else:
{{
  "is_supported": true,
  "supporting_evidence_ids": ["p0001"],
  "verification_explanation": "<brief support check>"
}}"""


def revision_prompt(
    question: str,
    evidence_summary: str,
    selected_evidence: Iterable[dict[str, Any]],
    verification: dict[str, Any],
    reasoning_type: str = "unknown",
    answer_type: str = "unknown",
) -> str:
    return f"""TASK: REVISE_ANSWER
Revise the answer once because verification did not establish support.
{_task_hints(reasoning_type, answer_type)}
Evidence summary:
{evidence_summary}
Selected evidence:
{_render_selected_evidence(selected_evidence)}
Verification: {json.dumps(verification, ensure_ascii=True)}
{ANSWER_RULES}
{CITATION_RULES}
{MULTI_HOP_RULES}
Final question: {question}
{ANSWER_SCHEMA}"""



def evidence_expansion_prompt(
    question: str,
    context: str,
    selected_evidence: Iterable[dict[str, Any]],
    evidence_summary: str,
    answer_payload: dict[str, Any],
    verification: dict[str, Any],
    reasoning_type: str = "unknown",
    answer_type: str = "unknown",
) -> str:
    already_selected = _render_selected_evidence(selected_evidence)
    selected_ids = [str(item.get("evidence_id", "")) for item in selected_evidence]
    return f"""TASK: EVIDENCE_GAP_PROBE
The current selected evidence is insufficient or unsupported. Find additional passage IDs from the full long context that supply the missing information required to answer the final question.
{_task_hints(reasoning_type, answer_type)}
Current selected evidence IDs: {json.dumps(selected_ids, ensure_ascii=True)}
Current selected evidence:
{already_selected}
Current evidence summary:
{evidence_summary}
Current answer payload: {json.dumps(answer_payload, ensure_ascii=True)}
Verification result: {json.dumps(verification, ensure_ascii=True)}
Expansion rules:
- Select zero to two additional passages only.
- Do not repeat any already selected passage.
- Use exact visible passage IDs only.
- Do not output raw numeric IDs, section IDs, ranges, or large passage spans.
- Do not choose a passage merely because it shares a keyword such as headquarters, location, accuracy, samples, or acquired.
- Prefer direct factual statements over low-trust or conflicting wording such as "draft claims", "rumor", "unconfirmed", "incorrectly", or "outdated".
- Choose passages that close the missing reasoning gap identified by the verification explanation.
- For multi-hop questions, if selected evidence identifies an intermediate entity, find a passage about that exact intermediate entity that gives the requested property.
- Example pattern to follow: if one selected passage says X was acquired by Y, and the question asks where the company that acquired X is headquartered, find a passage about Y's headquarters.
- For comparison questions, add the passage that contains the missing compared value for the candidate not yet covered.
- For arithmetic questions, add passages that contain missing numbers required for the calculation.
- In the text field, copy the selected passage text exactly as shown; do not rewrite, infer, or invent passage text.
Full long context:
{context}
Final question: {question}
Return exactly one JSON object and nothing else:
{{
  "selected_evidence": [
    {{"evidence_id": "p0002", "text": "<additional selected passage text>", "relevance_score": 0.0}}
  ]
}}"""

def _render_selected_evidence(selected_evidence: Iterable[dict[str, Any]]) -> str:
    lines = []
    for item in selected_evidence:
        evidence_id = str(item.get("evidence_id", "unknown"))
        text = str(item.get("text", ""))
        lines.append(f"[passage_id: {evidence_id}] {text}")
    return "\n".join(lines) or "(none)"


def _task_hints(reasoning_type: str, answer_type: str) -> str:
    return f"""Reasoning type: {reasoning_type}
Expected answer type: {answer_type}"""
