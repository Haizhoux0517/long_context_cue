from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from longcue.utils.token_utils import chunk_words, estimate_tokens

from .schema import BenchmarkSample, Distractor, Evidence

NUMBER_PATTERN = re.compile(r"^-?\d+(?:[.,]\d+)?$")
PASSAGE_ID_PATTERN = re.compile(r"\[passage_id:\s*[^\]]+\]", re.IGNORECASE)
YES_NO = {"yes", "no", "true", "false"}


def first_present(record: dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        value = record.get(key)
        if value is not None and value != "":
            return value
    return None


def answer_text(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return answer_text(value[0]) if value else ""
    if isinstance(value, dict):
        nested = first_present(value, ("text", "answer", "target", "output", "value"))
        return answer_text(nested)
    if value is None:
        return ""
    return str(value)


def text_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        parts = [text_value(item) for item in value]
        return "\n".join(part for part in parts if part)
    if isinstance(value, dict):
        parts = [(key, text_value(item)) for key, item in value.items()]
        return "\n".join(f"{key}: {part}" for key, part in parts if part)
    if value is None:
        return ""
    return str(value)


def infer_answer_type(answer: str, original_answer: Any = None) -> str:
    if isinstance(original_answer, (list, tuple)) and len(original_answer) > 1:
        return "list"
    normalized = answer.strip().lower()
    if normalized in YES_NO:
        return "yes_no"
    if NUMBER_PATTERN.fullmatch(normalized.replace(",", "")):
        return "number"
    if answer and len(answer.split()) <= 5 and any(character.isupper() for character in answer):
        return "entity"
    return "string" if answer else "unknown"


def render_evidence(evidence: list[Evidence]) -> list[str]:
    return [f"[passage_id: {item.evidence_id}] {item.text}" for item in evidence]


def render_distractors(distractors: list[Distractor]) -> list[str]:
    return [f"[passage_id: {item.distractor_id}] {item.text}" for item in distractors]


def passage_id(index: int) -> str:
    return f"p{index:04d}"


def add_passage_ids_to_context(text: str, chunk_size_words: int = 180) -> str:
    """Prefix unmarked context chunks with neutral passage IDs."""
    stripped = text.strip()
    if not stripped or PASSAGE_ID_PATTERN.search(stripped):
        return stripped
    chunks = chunk_words(stripped, chunk_size=chunk_size_words)
    return "\n\n".join(
        f"[passage_id: {passage_id(index)}] {chunk}"
        for index, chunk in enumerate(chunks, start=1)
    )


def compose_context(
    evidence: list[Evidence],
    distractors: list[Distractor],
    target_tokens: int,
    evidence_position: str,
    seed_tag: int,
    filler_fragments: list[str] | None = None,
) -> str:
    evidence_blocks = render_evidence(evidence)
    if evidence_position == "scattered" and len(evidence_blocks) == 1:
        evidence_blocks = evidence_blocks * 2
    distractor_blocks = render_distractors(distractors)
    fixed_tokens = estimate_tokens("\n\n".join(evidence_blocks + distractor_blocks))
    filler_words = _filler_words(
        max(target_tokens - fixed_tokens, 0),
        seed_tag=seed_tag,
        fragments=filler_fragments or [],
    )
    filler_blocks = _paragraphize(filler_words)
    blocks = _insert_blocks(
        filler_blocks,
        evidence_blocks,
        distractor_blocks,
        target_tokens=target_tokens,
        evidence_position=evidence_position,
    )
    return "\n\n".join(blocks)


def raw_record_metadata(record: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(record, ensure_ascii=True, default=str))


def source_sample_id(source: str, raw_id: Any, index: int) -> str:
    clean = str(raw_id).strip() if raw_id is not None else ""
    return clean or f"{source}_{index:06d}"


def sample_from_parts(
    *,
    sample_id: str,
    source: str,
    question: str,
    gold_answer: str,
    long_context: str,
    oracle_evidence: list[Evidence] | None = None,
    distractors: list[Distractor] | None = None,
    context_length: int | None = None,
    evidence_position: str = "unknown",
    evidence_density: str = "unknown",
    distractor_similarity: str = "unknown",
    reasoning_type: str = "unknown",
    answer_type: str | None = None,
    metadata: dict[str, Any] | None = None,
    original_answer: Any = None,
) -> BenchmarkSample:
    sample_metadata = dict(metadata or {})
    sample_metadata.setdefault("cue_applicable", bool(oracle_evidence))
    return BenchmarkSample(
        id=sample_id,
        source=source,
        question=question.strip(),
        gold_answer=gold_answer.strip(),
        oracle_evidence=oracle_evidence or [],
        long_context=long_context.strip(),
        distractors=distractors or [],
        context_length=context_length if context_length is not None else estimate_tokens(long_context),
        evidence_position=evidence_position,
        evidence_density=evidence_density,
        distractor_similarity=distractor_similarity,
        reasoning_type=reasoning_type,
        answer_type=answer_type or infer_answer_type(gold_answer, original_answer),
        metadata=sample_metadata,
    )


def iter_json_records(path: str | Path) -> Iterable[tuple[Path, dict[str, Any]]]:
    root = Path(path)
    files = [root] if root.is_file() else sorted(root.rglob("*.json")) + sorted(root.rglob("*.jsonl"))
    for file_path in files:
        if file_path.suffix == ".jsonl":
            try:
                with file_path.open("r", encoding="utf-8") as handle:
                    for line in handle:
                        stripped = line.strip()
                        if not stripped:
                            continue
                        try:
                            payload = json.loads(stripped)
                        except json.JSONDecodeError:
                            continue
                        if isinstance(payload, dict):
                            yield file_path, payload
            except OSError:
                continue
            continue
        try:
            with file_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError):
            continue
        records = payload if isinstance(payload, list) else payload.get("data", payload) if isinstance(payload, dict) else []
        if isinstance(records, dict):
            yield file_path, records
        elif isinstance(records, list):
            for record in records:
                if isinstance(record, dict):
                    yield file_path, record


def _filler_words(token_count: int, seed_tag: int, fragments: list[str]) -> list[str]:
    fragment_words = " ".join(fragments).split()
    words: list[str] = []
    while fragment_words and len(words) < token_count:
        take = min(token_count - len(words), len(fragment_words))
        words.extend(fragment_words[:take])
    vocabulary = (
        "archive",
        "benchmark",
        "citation",
        "document",
        "evidence",
        "filler",
        "index",
        "journal",
        "ledger",
        "memo",
        "note",
        "paragraph",
        "protocol",
        "record",
        "report",
        "section",
    )
    while len(words) < token_count:
        offset = len(words)
        words.append(f"{vocabulary[offset % len(vocabulary)]}_{(seed_tag + offset) % 997}")
    return words


def _paragraphize(words: list[str], paragraph_size: int = 80) -> list[str]:
    return [
        " ".join(words[index : index + paragraph_size])
        for index in range(0, len(words), paragraph_size)
    ]


def _insert_blocks(
    filler_blocks: list[str],
    evidence_blocks: list[str],
    distractor_blocks: list[str],
    *,
    target_tokens: int,
    evidence_position: str,
) -> list[str]:
    paragraphs = list(filler_blocks)
    if not paragraphs:
        paragraphs = [""]
    distractor_index = len(paragraphs) // 3
    paragraphs[distractor_index:distractor_index] = distractor_blocks
    if not evidence_blocks:
        return [paragraph for paragraph in paragraphs if paragraph]
    if evidence_position == "front":
        return _insert_at_token_fraction(paragraphs, evidence_blocks, 0.05, target_tokens)
    if evidence_position == "middle":
        return _insert_at_token_fraction(paragraphs, evidence_blocks, 0.50, target_tokens)
    if evidence_position == "end":
        return _insert_at_token_fraction(paragraphs, evidence_blocks, 0.88, target_tokens)
    if evidence_position == "scattered":
        fractions = (0.10, 0.50, 0.88)
        result = paragraphs
        for index, block in enumerate(evidence_blocks):
            result = _insert_at_token_fraction(
                result, [block], fractions[index % len(fractions)], target_tokens
            )
        return result
    return paragraphs + evidence_blocks


def _insert_at_token_fraction(
    paragraphs: list[str], blocks: list[str], fraction: float, target_tokens: int
) -> list[str]:
    boundary = max(0, int(target_tokens * fraction))
    consumed = 0
    index = len(paragraphs)
    for index, paragraph in enumerate(paragraphs):
        consumed += estimate_tokens(paragraph)
        if consumed >= boundary:
            break
    else:
        index = len(paragraphs)
    return paragraphs[:index] + blocks + paragraphs[index:]
