from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass

from .adapter_utils import compose_context, passage_id, sample_from_parts
from .schema import BenchmarkSample, Distractor, Evidence

CONTROLLED_CONTEXT_LENGTHS = (4000, 8000, 16000, 32000)
CONTROLLED_EVIDENCE_POSITIONS = ("front", "middle", "end", "scattered")
CONTROLLED_DISTRACTOR_SIMILARITIES = ("none", "low", "high", "conflicting")
CONTROLLED_REASONING_TYPES = ("single_hop", "multi_hop", "comparison", "arithmetic")


@dataclass
class ControlledCUEGenerator:
    num_per_cell: int = 5
    seed: int = 42
    context_lengths: tuple[int, ...] = CONTROLLED_CONTEXT_LENGTHS
    evidence_positions: tuple[str, ...] = CONTROLLED_EVIDENCE_POSITIONS
    distractor_similarities: tuple[str, ...] = CONTROLLED_DISTRACTOR_SIMILARITIES
    reasoning_types: tuple[str, ...] = CONTROLLED_REASONING_TYPES

    def generate(self) -> list[BenchmarkSample]:
        if self.num_per_cell <= 0:
            raise ValueError("num_per_cell must be positive.")
        rng = random.Random(self.seed)
        samples: list[BenchmarkSample] = []
        cells = [
            (context_length, position, similarity, reasoning_type, replicate)
            for context_length in self.context_lengths
            for position in self.evidence_positions
            for similarity in self.distractor_similarities
            for reasoning_type in self.reasoning_types
            for replicate in range(self.num_per_cell)
        ]
        for index, variables in enumerate(cells):
            samples.append(self._build_sample(index, variables, rng))
        return samples

    def _build_sample(
        self,
        index: int,
        variables: tuple[int, str, str, str, int],
        rng: random.Random,
    ) -> BenchmarkSample:
        context_length, position, similarity, reasoning_type, replicate = variables
        tag = f"{index:05d}"
        question, answer, answer_type, evidence = make_controlled_task(
            reasoning_type, tag, rng
        )
        distractors = make_controlled_distractors(similarity, reasoning_type, tag, answer)
        long_context = compose_context(
            evidence=evidence,
            distractors=distractors,
            target_tokens=context_length,
            evidence_position=position,
            seed_tag=self.seed + index,
        )
        return sample_from_parts(
            sample_id=f"controlled_{index + 1:06d}",
            source="controlled",
            question=question,
            gold_answer=answer,
            oracle_evidence=evidence,
            long_context=long_context,
            distractors=distractors,
            context_length=context_length,
            evidence_position=position,
            evidence_density="low" if len(evidence) == 1 else "medium",
            distractor_similarity=similarity,
            reasoning_type=reasoning_type,
            answer_type=answer_type,
            metadata={"cell_replicate": replicate, "seed": self.seed, "cue_applicable": True},
        )


def make_controlled_task(
    reasoning_type: str, tag: str, rng: random.Random
) -> tuple[str, str, str, list[Evidence]]:
    if reasoning_type == "single_hop":
        company = f"NovaMind-{tag}"
        acquirer = f"Arcturus Systems {tag}"
        return (
            f"Which company acquired {company}?",
            acquirer,
            "entity",
            [Evidence(passage_id(1), f"In 2022, {company} was acquired by {acquirer}.")],
        )
    if reasoning_type == "multi_hop":
        company = f"NovaMind-{tag}"
        acquirer = f"Arcturus Systems {tag}"
        city = f"Zurich-{tag}"
        return (
            f"Where is the company that acquired {company} headquartered?",
            city,
            "entity",
            [
                Evidence(passage_id(1), f"{company} was acquired by {acquirer}."),
                Evidence(passage_id(2), f"{acquirer} is headquartered in {city}."),
            ],
        )
    if reasoning_type == "comparison":
        alpha = round(68.0 + rng.random() * 20, 1)
        beta = round(alpha - (1.0 + rng.random() * 8), 1)
        model_a = f"Model Alpha {tag}"
        model_b = f"Model Beta {tag}"
        return (
            f"Which model achieved higher accuracy in evaluation {tag}?",
            model_a,
            "entity",
            [
                Evidence(passage_id(1), f"{model_a} achieved {alpha} accuracy."),
                Evidence(passage_id(2), f"{model_b} achieved {beta} accuracy."),
            ],
        )
    if reasoning_type == "arithmetic":
        count_a = 220 + rng.randint(0, 260)
        count_b = 80 + rng.randint(0, 180)
        return (
            f"How many samples are there in total across Dataset A {tag} and Dataset B {tag}?",
            str(count_a + count_b),
            "number",
            [
                Evidence(passage_id(1), f"Dataset A {tag} contains {count_a} samples."),
                Evidence(passage_id(2), f"Dataset B {tag} contains {count_b} samples."),
            ],
        )
    raise ValueError(f"Unsupported controlled reasoning type: {reasoning_type}")


def make_controlled_distractors(
    similarity: str, reasoning_type: str, tag: str, gold_answer: str
) -> list[Distractor]:
    if similarity == "none":
        return []
    if similarity == "low":
        return [
            Distractor(
                passage_id(3),
                f"A lab inventory bulletin {tag} lists microscope calibration schedules.",
            )
        ]
    if reasoning_type == "single_hop":
        text = (
            f"NovaMind-{tag} discussed a partnership with Helios Labs {tag}."
            if similarity == "high"
            else f"A disputed memo says NovaMind-{tag} was acquired by Helios Labs {tag}."
        )
    elif reasoning_type == "multi_hop":
        text = (
            f"Arcturus Systems {tag} opened a Zurich recruiting office."
            if similarity == "high"
            else f"A draft claims Arcturus Systems {tag} is headquartered in Oslo-{tag}."
        )
    elif reasoning_type == "comparison":
        text = (
            f"Model Beta {tag} achieved higher accuracy on a preliminary pilot."
            if similarity == "high"
            else f"Conflicting draft: Model Beta {tag} achieved higher accuracy than {gold_answer}."
        )
    else:
        text = (
            f"Dataset A {tag} reserved additional samples for a later release."
            if similarity == "high"
            else f"Conflicting worksheet reports a different total for Dataset A {tag} and Dataset B {tag}."
        )
    return [Distractor(passage_id(3), text)]


def controlled_summary(samples: list[BenchmarkSample]) -> dict[str, object]:
    return {
        "samples": len(samples),
        "context_lengths": dict(Counter(sample.context_length for sample in samples)),
        "evidence_positions": dict(Counter(sample.evidence_position for sample in samples)),
        "distractor_similarities": dict(
            Counter(sample.distractor_similarity for sample in samples)
        ),
        "reasoning_types": dict(Counter(sample.reasoning_type for sample in samples)),
    }
