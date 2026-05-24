from __future__ import annotations

import random
from dataclasses import dataclass

from longcue.utils.token_utils import estimate_tokens

from .adapter_utils import passage_id
from .schema import (
    CONTEXT_LENGTHS,
    BenchmarkSample,
    Distractor,
    Evidence,
)

FILLER_VOCABULARY = (
    "archive",
    "briefing",
    "committee",
    "dataset",
    "editorial",
    "finding",
    "governance",
    "handoff",
    "index",
    "journal",
    "ledger",
    "memo",
    "notebook",
    "observation",
    "protocol",
    "query",
    "record",
    "summary",
    "timeline",
    "update",
)
DEMO_REASONING_TYPES = (
    "single_hop",
    "multi_hop",
    "comparison",
    "arithmetic",
    "contradiction",
)
DEMO_EVIDENCE_POSITIONS = ("front", "middle", "end", "scattered")
DEMO_EVIDENCE_DENSITIES = ("high", "medium", "low")
DEMO_DISTRACTOR_SIMILARITIES = ("none", "low", "high", "conflicting")


@dataclass
class ControlledBenchmarkGenerator:
    sample_count: int = 100
    seed: int = 13
    context_lengths: tuple[int, ...] = CONTEXT_LENGTHS

    def generate(self) -> list[BenchmarkSample]:
        rng = random.Random(self.seed)
        samples: list[BenchmarkSample] = []
        base_grid = [
            (context_length, evidence_position, evidence_density, reasoning_type)
            for context_length in self.context_lengths
            for evidence_position in DEMO_EVIDENCE_POSITIONS
            for evidence_density in DEMO_EVIDENCE_DENSITIES
            for reasoning_type in DEMO_REASONING_TYPES
        ]
        rng.shuffle(base_grid)
        variable_grid = [
            (
                context_length,
                evidence_position,
                evidence_density,
                distractor_similarity,
                reasoning_type,
            )
            for context_length, evidence_position, evidence_density, reasoning_type in base_grid
            for distractor_similarity in DEMO_DISTRACTOR_SIMILARITIES
        ]
        for index in range(self.sample_count):
            variables = variable_grid[index % len(variable_grid)]
            samples.append(self._sample(index=index, rng=rng, variables=variables))
        return samples

    def _sample(
        self,
        index: int,
        rng: random.Random,
        variables: tuple[int, str, str, str, str],
    ) -> BenchmarkSample:
        context_length, position, density, similarity, reasoning_type = variables
        sample_tag = f"{index:04d}"
        question, gold_answer, evidence = _task_template(reasoning_type, sample_tag)
        distractors = _make_distractors(similarity, reasoning_type, sample_tag)
        long_context = _assemble_context(
            evidence=evidence,
            distractors=distractors,
            target_tokens=context_length,
            evidence_position=position,
            evidence_density=density,
            sample_index=index,
            rng=rng,
        )
        return BenchmarkSample(
            id=f"sample_{index + 1:04d}",
            question=question,
            gold_answer=gold_answer,
            oracle_evidence=evidence,
            long_context=long_context,
            distractors=distractors,
            evidence_position=position,
            context_length=context_length,
            evidence_density=density,
            distractor_similarity=similarity,
            reasoning_type=reasoning_type,
            metadata={"cue_applicable": True},
        )


def _task_template(reasoning_type: str, tag: str) -> tuple[str, str, list[Evidence]]:
    if reasoning_type == "single_hop":
        target = f"NovaMind-{tag}"
        answer = f"Arcturus Systems {tag}"
        return (
            f"Which company acquired {target}?",
            answer,
            [
                Evidence(
                    passage_id(1),
                    f"In 2022, {target} was acquired by {answer} after two years of independent operation.",
                )
            ],
        )
    if reasoning_type == "multi_hop":
        target = f"NovaMind-{tag}"
        acquirer = f"Arcturus Systems {tag}"
        answer = f"Meridian City {tag}"
        return (
            f"In which city is the company that acquired {target} headquartered?",
            answer,
            [
                Evidence(passage_id(1), f"{target} was acquired by {acquirer} in 2022."),
                Evidence(passage_id(2), f"{acquirer} is headquartered in {answer}."),
            ],
        )
    if reasoning_type == "comparison":
        project_a = f"Project Aurora {tag}"
        project_b = f"Project Boreal {tag}"
        return (
            f"Which project achieved the higher benchmark score in trial {tag}?",
            project_b,
            [
                Evidence(passage_id(1), f"{project_a} scored 71 in trial {tag}."),
                Evidence(passage_id(2), f"{project_b} scored 84 in trial {tag}."),
            ],
        )
    if reasoning_type == "arithmetic":
        atlas_count = 38 + int(tag) % 7
        borealis_count = 11 + int(tag) % 5
        difference = str(atlas_count - borealis_count)
        return (
            f"How many more records did Atlas unit process than Borealis unit in run {tag}?",
            difference,
            [
                Evidence(passage_id(1), f"Atlas unit processed {atlas_count} records in run {tag}."),
                Evidence(passage_id(2), f"Borealis unit processed {borealis_count} records in run {tag}."),
            ],
        )
    if reasoning_type == "contradiction":
        target = f"NovaMind-{tag}"
        answer = f"Arcturus Systems {tag}"
        return (
            f"After resolving the correction, which company acquired {target}?",
            answer,
            [
                Evidence(
                    passage_id(1),
                    f"The registry correction says the Helios claim for {target} is incorrect.",
                ),
                Evidence(passage_id(2), f"The correction confirms {target} was acquired by {answer}."),
            ],
        )
    raise ValueError(f"Unsupported reasoning type: {reasoning_type}")


def _make_distractors(
    similarity: str, reasoning_type: str, tag: str
) -> list[Distractor]:
    if similarity == "none":
        return []
    if similarity == "low":
        return [
            Distractor(
                passage_id(3),
                f"A coastal weather bulletin for district {tag} recorded a routine sensor audit.",
            )
        ]
    if reasoning_type == "comparison":
        distractor_text = (
            f"Project Aurora {tag} scored 96 in an unrelated pilot, not trial {tag}."
        )
    elif reasoning_type == "arithmetic":
        distractor_text = (
            f"Atlas unit forecast {90 + int(tag) % 9} records for a later run outside run {tag}."
        )
    elif similarity == "conflicting":
        distractor_text = (
            f"An unverified note claims NovaMind-{tag} was acquired by Helios Labs {tag}."
        )
    else:
        distractor_text = (
            f"NovaMind-{tag} explored a partnership with Helios Labs {tag} before acquisition."
        )
    if similarity == "conflicting" and reasoning_type in {"comparison", "arithmetic"}:
        distractor_text = f"Conflicting draft: {distractor_text}"
    return [Distractor(passage_id(3), distractor_text)]


def _assemble_context(
    evidence: list[Evidence],
    distractors: list[Distractor],
    target_tokens: int,
    evidence_position: str,
    evidence_density: str,
    sample_index: int,
    rng: random.Random,
) -> str:
    repeat_count = {"low": 1, "medium": 2, "high": 3}[evidence_density]
    evidence_blocks = [
        f"[passage_id: {item.evidence_id}] {item.text}"
        for _ in range(repeat_count)
        for item in evidence
    ]
    distractor_blocks = [
        f"[passage_id: {item.distractor_id}] {item.text}" for item in distractors
    ]
    base_token_count = estimate_tokens("\n".join(evidence_blocks + distractor_blocks))
    filler = _filler_paragraphs(
        max(target_tokens - base_token_count, 0), sample_index=sample_index, rng=rng
    )
    paragraphs = _place_blocks(
        filler=filler,
        evidence_blocks=evidence_blocks,
        distractor_blocks=distractor_blocks,
        evidence_position=evidence_position,
    )
    return "\n\n".join(paragraphs)


def _filler_paragraphs(
    token_count: int, sample_index: int, rng: random.Random, paragraph_size: int = 72
) -> list[str]:
    paragraphs: list[str] = []
    vocabulary = list(FILLER_VOCABULARY)
    rng.shuffle(vocabulary)
    for start in range(0, token_count, paragraph_size):
        width = min(paragraph_size, token_count - start)
        words = [
            f"{vocabulary[(start + offset) % len(vocabulary)]}_{(sample_index + offset) % 97}"
            for offset in range(width)
        ]
        paragraphs.append(" ".join(words))
    return paragraphs


def _place_blocks(
    filler: list[str],
    evidence_blocks: list[str],
    distractor_blocks: list[str],
    evidence_position: str,
) -> list[str]:
    if evidence_position == "front":
        return evidence_blocks + distractor_blocks + filler
    if evidence_position == "end":
        return filler + distractor_blocks + evidence_blocks

    midpoint = len(filler) // 2
    if evidence_position == "middle":
        return filler[:midpoint] + distractor_blocks + evidence_blocks + filler[midpoint:]

    paragraphs = list(filler)
    if distractor_blocks:
        paragraphs[midpoint:midpoint] = distractor_blocks
    if not paragraphs:
        return evidence_blocks + distractor_blocks
    scattered = list(paragraphs)
    for offset, block in enumerate(evidence_blocks, start=1):
        index = min(len(scattered), (len(paragraphs) * offset) // (len(evidence_blocks) + 1))
        scattered.insert(index, block)
    return scattered
