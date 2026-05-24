from __future__ import annotations

import logging
import random
from collections import Counter
from collections.abc import Iterable
from typing import Any

from .adapter_utils import compose_context, passage_id, raw_record_metadata, sample_from_parts
from .schema import BenchmarkSample, Distractor, Evidence

HOTPOT_POSITIONS = ("front", "middle", "end", "scattered")


def load_hotpotqa_cue(
    *,
    split: str,
    limit: int,
    context_lengths: list[int],
    seed: int,
    logger: logging.Logger | None = None,
) -> tuple[list[BenchmarkSample], dict[str, Any]]:
    from datasets import load_dataset

    dataset = load_dataset("hotpotqa/hotpot_qa", "fullwiki", split=split)
    return convert_hotpotqa_records(
        dataset,
        limit=limit,
        context_lengths=context_lengths,
        seed=seed,
        logger=logger,
    )


def convert_hotpotqa_records(
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
            evidence, distractors = extract_hotpot_evidence(record)
        except ValueError as exc:
            skips[str(exc)] += 1
            _log(logger, "Skipping HotpotQA record %s: %s", raw_index, exc)
            continue
        question = str(record.get("question", "")).strip()
        answer = str(record.get("answer", "")).strip()
        if not question or not answer:
            skips["missing_question_or_answer"] += 1
            continue
        length = int(context_lengths[len(samples) % len(context_lengths)])
        position = HOTPOT_POSITIONS[len(samples) % len(HOTPOT_POSITIONS)]
        fragments = [item.text for item in distractors]
        samples.append(
            sample_from_parts(
                sample_id=f"hotpotqa_{record.get('id', raw_index)}",
                source="hotpotqa",
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
                evidence_density="low" if len(evidence) <= 2 else "medium",
                distractor_similarity="unknown",
                reasoning_type=(
                    "comparison"
                    if str(record.get("type", "")).lower() == "comparison"
                    else "multi_hop"
                ),
                metadata={
                    "hotpotqa_type": record.get("type"),
                    "level": record.get("level"),
                    "cue_applicable": True,
                    "original": raw_record_metadata(record),
                },
                original_answer=record.get("answer"),
            )
        )
    stats = {"converted": len(samples), "skipped": sum(skips.values()), "skip_reasons": dict(skips)}
    return samples, stats


def extract_hotpot_evidence(record: dict[str, Any]) -> tuple[list[Evidence], list[Distractor]]:
    paragraphs = parse_hotpot_context(record.get("context"))
    supporting_facts = parse_supporting_facts(record.get("supporting_facts"))
    if not paragraphs or not supporting_facts:
        raise ValueError("missing_context_or_supporting_facts")
    paragraph_map = {title: sentences for title, sentences in paragraphs}
    support_titles = {title for title, _ in supporting_facts}
    evidence: list[Evidence] = []
    for index, (title, sentence_id) in enumerate(supporting_facts, start=1):
        sentences = paragraph_map.get(title)
        if sentences is None or sentence_id < 0 or sentence_id >= len(sentences):
            raise ValueError("unaligned_supporting_fact")
        sentence = str(sentences[sentence_id]).strip()
        if not sentence:
            raise ValueError("empty_supporting_fact")
        evidence.append(Evidence(passage_id(index), sentence, title=title))
    distractors = [
        Distractor(passage_id(len(evidence) + index), " ".join(sentences).strip(), title=title)
        for index, (title, sentences) in enumerate(paragraphs, start=1)
        if title not in support_titles and " ".join(sentences).strip()
    ]
    return evidence, distractors


def parse_hotpot_context(value: Any) -> list[tuple[str, list[str]]]:
    if isinstance(value, dict):
        titles = value.get("title") or value.get("titles") or []
        sentences = value.get("sentences") or value.get("sentence") or []
        return [
            (str(title), [str(sentence) for sentence in paragraph])
            for title, paragraph in zip(titles, sentences)
            if isinstance(paragraph, (list, tuple))
        ]
    if isinstance(value, list):
        paragraphs: list[tuple[str, list[str]]] = []
        for item in value:
            if isinstance(item, dict):
                title = item.get("title")
                sentences = item.get("sentences") or item.get("sentence")
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                title, sentences = item[0], item[1]
            else:
                continue
            if isinstance(sentences, str):
                sentences = [sentences]
            if title is not None and isinstance(sentences, (list, tuple)):
                paragraphs.append((str(title), [str(sentence) for sentence in sentences]))
        return paragraphs
    return []


def parse_supporting_facts(value: Any) -> list[tuple[str, int]]:
    if isinstance(value, dict):
        titles = value.get("title") or value.get("titles") or []
        sentence_ids = value.get("sent_id") or value.get("sent_ids") or value.get("sentence_id") or []
        return _support_pairs(titles, sentence_ids)
    if isinstance(value, list):
        pairs: list[tuple[str, int]] = []
        for item in value:
            if isinstance(item, dict):
                title = item.get("title")
                sentence_id = item.get("sent_id", item.get("sentence_id"))
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                title, sentence_id = item[0], item[1]
            else:
                continue
            try:
                pairs.append((str(title), int(sentence_id)))
            except (TypeError, ValueError):
                continue
        return pairs
    return []


def _support_pairs(titles: Any, sentence_ids: Any) -> list[tuple[str, int]]:
    pairs: list[tuple[str, int]] = []
    if not isinstance(titles, (list, tuple)) or not isinstance(sentence_ids, (list, tuple)):
        return pairs
    for title, sentence_id in zip(titles, sentence_ids):
        try:
            pairs.append((str(title), int(sentence_id)))
        except (TypeError, ValueError):
            continue
    return pairs


def _log(logger: logging.Logger | None, message: str, *args: Any) -> None:
    if logger is not None:
        logger.warning(message, *args)
