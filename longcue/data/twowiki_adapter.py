from __future__ import annotations

import logging
import random
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .adapter_utils import compose_context, iter_json_records, passage_id, raw_record_metadata, sample_from_parts
from .hotpotqa_adapter import parse_hotpot_context, parse_supporting_facts
from .schema import BenchmarkSample, Distractor, Evidence

TWOWIKI_POSITIONS = ("front", "middle", "end", "scattered")
DEFAULT_TWOWIKI_DATASET = "xanhho/2WikiMultihopQA"
FALLBACK_TWOWIKI_DATASETS = ("framolfese/2WikiMultihopQA",)


def load_2wikimultihopqa_cue(
    *,
    split: str,
    limit: int,
    context_lengths: list[int],
    seed: int,
    dataset_name: str = DEFAULT_TWOWIKI_DATASET,
    logger: logging.Logger | None = None,
) -> tuple[list[BenchmarkSample], dict[str, Any]]:
    """Load 2WikiMultiHopQA from Hugging Face and convert it to ONCU samples.

    The default dataset is the official Hugging Face mirror. A HotpotQA-compatible
    mirror is tried as a fallback because it exposes `context` and
    `supporting_facts` in a schema that is easier to align with existing ONCU
    adapters.
    """
    from datasets import load_dataset

    attempted: list[str] = []
    last_exc: Exception | None = None
    for candidate in (dataset_name, *FALLBACK_TWOWIKI_DATASETS):
        if candidate in attempted:
            continue
        attempted.append(candidate)
        try:
            dataset = load_dataset(candidate, split=split)
            return convert_2wikimultihopqa_records(
                dataset,
                limit=limit,
                context_lengths=context_lengths,
                seed=seed,
                logger=logger,
            )
        except Exception as exc:  # pragma: no cover - network/dataset dependent.
            last_exc = exc
            _log(logger, "Could not load 2WikiMultiHopQA dataset %s: %s", candidate, exc)
    raise RuntimeError(
        "Could not load any configured 2WikiMultiHopQA dataset. "
        f"Attempted: {attempted}. Last error: {last_exc}"
    )


def load_2wikimultihopqa_cue_from_path(
    path: str | Path,
    *,
    limit: int | None = None,
    context_lengths: list[int] | tuple[int, ...] = (4000, 8000, 16000),
    seed: int = 42,
    logger: logging.Logger | None = None,
) -> tuple[list[BenchmarkSample], dict[str, Any]]:
    """Load 2WikiMultiHopQA records from local JSON/JSONL files."""
    records = (record for _, record in iter_json_records(path))
    return convert_2wikimultihopqa_records(
        records,
        limit=limit,
        context_lengths=context_lengths,
        seed=seed,
        logger=logger,
    )


def convert_2wikimultihopqa_records(
    records: Iterable[dict[str, Any]],
    *,
    limit: int | None = None,
    context_lengths: list[int] | tuple[int, ...] = (4000, 8000, 16000),
    seed: int = 42,
    logger: logging.Logger | None = None,
) -> tuple[list[BenchmarkSample], dict[str, Any]]:
    if not context_lengths:
        raise ValueError("At least one context length is required.")
    rng = random.Random(seed)
    samples: list[BenchmarkSample] = []
    skips: Counter[str] = Counter()
    for raw_index, record in enumerate(records):
        if limit is not None and len(samples) >= limit:
            break
        if not isinstance(record, dict):
            skips["non_mapping_record"] += 1
            continue
        try:
            evidence, distractors = extract_2wiki_evidence(record)
        except ValueError as exc:
            skips[str(exc)] += 1
            _log(logger, "Skipping 2WikiMultiHopQA record %s: %s", raw_index, exc)
            continue
        question = str(record.get("question", "")).strip()
        answer = str(record.get("answer", "")).strip()
        if not question or not answer:
            skips["missing_question_or_answer"] += 1
            continue
        length = int(context_lengths[len(samples) % len(context_lengths)])
        position = TWOWIKI_POSITIONS[len(samples) % len(TWOWIKI_POSITIONS)]
        fragments = [item.text for item in distractors]
        record_id = record.get("id", record.get("_id", raw_index))
        samples.append(
            sample_from_parts(
                sample_id=f"2wikimultihopqa_{record_id}",
                source="2wikimultihopqa",
                question=question,
                gold_answer=answer,
                oracle_evidence=evidence,
                long_context=compose_context(
                    evidence,
                    distractors,
                    target_tokens=length,
                    evidence_position=position,
                    seed_tag=seed + raw_index + rng.randint(0, 9999),
                    filler_fragments=fragments,
                ),
                distractors=distractors,
                context_length=length,
                evidence_position=position,
                evidence_density=_evidence_density(len(evidence)),
                distractor_similarity="unknown",
                reasoning_type=_reasoning_type(record.get("type"), evidence),
                metadata={
                    "2wiki_type": record.get("type"),
                    "hop_count": _hop_count(record, evidence),
                    "cue_applicable": True,
                    "original": raw_record_metadata(record),
                },
                original_answer=record.get("answer"),
            )
        )
    stats = {"converted": len(samples), "skipped": sum(skips.values()), "skip_reasons": dict(skips)}
    return samples, stats


def extract_2wiki_evidence(record: dict[str, Any]) -> tuple[list[Evidence], list[Distractor]]:
    paragraphs = parse_hotpot_context(record.get("context"))
    supporting_facts = parse_supporting_facts(record.get("supporting_facts"))
    if paragraphs and supporting_facts:
        return _extract_from_supporting_facts(paragraphs, supporting_facts)

    evidence = _extract_textual_evidences(record.get("evidences"))
    if not evidence:
        raise ValueError("missing_context_or_supporting_facts")
    distractors = _distractors_from_context(paragraphs, {item.title for item in evidence if item.title})
    return evidence, distractors


def _extract_from_supporting_facts(
    paragraphs: list[tuple[str, list[str]]],
    supporting_facts: list[tuple[str, int]],
) -> tuple[list[Evidence], list[Distractor]]:
    paragraph_map = {title: sentences for title, sentences in paragraphs}
    support_titles = {title for title, _ in supporting_facts}
    evidence: list[Evidence] = []
    seen: set[tuple[str, int]] = set()
    for title, sentence_id in supporting_facts:
        key = (title, sentence_id)
        if key in seen:
            continue
        seen.add(key)
        sentences = paragraph_map.get(title)
        if sentences is None or sentence_id < 0 or sentence_id >= len(sentences):
            raise ValueError("unaligned_supporting_fact")
        sentence = str(sentences[sentence_id]).strip()
        if not sentence:
            raise ValueError("empty_supporting_fact")
        evidence.append(Evidence(passage_id(len(evidence) + 1), sentence, title=title))
    if not evidence:
        raise ValueError("missing_oracle_evidence")
    distractors = _distractors_from_context(paragraphs, support_titles, offset=len(evidence))
    return evidence, distractors


def _extract_textual_evidences(value: Any) -> list[Evidence]:
    """Best-effort extraction for 2Wiki fields named `evidences`.

    Some public mirrors expose sentence-level `supporting_facts`; others expose a
    reasoning-path style `evidences` field. This parser only creates oracle
    evidence when a readable text field is present. Structured triples without a
    surface text are kept in metadata by the caller but are not exposed as oracle
    passages.
    """
    if not isinstance(value, list):
        return []
    evidence: list[Evidence] = []
    for item in value:
        title: str | None = None
        text = ""
        if isinstance(item, dict):
            title = _optional_str(item.get("title") or item.get("entity") or item.get("page"))
            text = _first_text_field(item, ("text", "sentence", "evidence", "passage", "paragraph"))
        elif isinstance(item, (list, tuple)):
            # Prefer list entries that already contain a natural-language sentence.
            string_items = [str(part).strip() for part in item if isinstance(part, str) and str(part).strip()]
            sentence_like = [part for part in string_items if len(part.split()) >= 4]
            if sentence_like:
                text = sentence_like[-1]
                title = string_items[0] if string_items else None
        if text:
            evidence.append(Evidence(passage_id(len(evidence) + 1), text, title=title))
    return evidence


def _distractors_from_context(
    paragraphs: list[tuple[str, list[str]]],
    support_titles: set[str],
    *,
    offset: int = 0,
) -> list[Distractor]:
    distractors: list[Distractor] = []
    for title, sentences in paragraphs:
        text = " ".join(str(sentence).strip() for sentence in sentences if str(sentence).strip())
        if title in support_titles or not text:
            continue
        distractors.append(Distractor(passage_id(offset + len(distractors) + 1), text, title=title))
    return distractors


def _first_text_field(record: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, (list, tuple)):
            joined = " ".join(str(part).strip() for part in value if str(part).strip())
            if joined:
                return joined
    return ""


def _reasoning_type(raw_type: Any, evidence: list[Evidence]) -> str:
    text = str(raw_type or "").lower()
    if "comparison" in text or "comparative" in text:
        return "comparison"
    return "multi_hop" if len(evidence) >= 2 else "single_hop"


def _hop_count(record: dict[str, Any], evidence: list[Evidence]) -> int:
    for key in ("hop_count", "num_hops", "hops"):
        try:
            return int(record[key])
        except (KeyError, TypeError, ValueError):
            continue
    return max(1, len(evidence))


def _evidence_density(count: int) -> str:
    if count <= 2:
        return "low"
    if count <= 4:
        return "medium"
    return "high"


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _log(logger: logging.Logger | None, message: str, *args: Any) -> None:
    if logger is not None:
        logger.warning(message, *args)
