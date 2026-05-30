from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

CONTEXT_LENGTHS = (4000, 8000, 16000, 32000)
SOURCES = ("controlled", "hotpotqa", "2wikimultihopqa", "ruler", "longbench", "babilong")
DECILE_EVIDENCE_POSITIONS = tuple(f"pos_{index:02d}" for index in range(10))
EVIDENCE_POSITIONS = ("front", "middle", "end", "scattered", "unknown", *DECILE_EVIDENCE_POSITIONS)
EVIDENCE_DENSITIES = ("high", "medium", "low", "unknown")
DISTRACTOR_SIMILARITIES = ("none", "low", "high", "conflicting", "unknown")
REASONING_TYPES = (
    "single_hop",
    "multi_hop",
    "comparison",
    "arithmetic",
    "contradiction",
    "retrieval",
    "aggregation",
    "summarization",
    "unknown",
)
ANSWER_TYPES = ("entity", "number", "yes_no", "string", "list", "unknown")


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    text: str
    title: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Evidence":
        return cls(
            evidence_id=str(payload["evidence_id"]),
            text=str(payload["text"]),
            title=_optional_text(payload.get("title")),
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"evidence_id": self.evidence_id, "text": self.text}
        if self.title is not None:
            payload["title"] = self.title
        return payload


@dataclass(frozen=True)
class Distractor:
    distractor_id: str
    text: str
    title: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Distractor":
        return cls(
            distractor_id=str(payload["distractor_id"]),
            text=str(payload["text"]),
            title=_optional_text(payload.get("title")),
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "distractor_id": self.distractor_id,
            "text": self.text,
        }
        if self.title is not None:
            payload["title"] = self.title
        return payload


@dataclass(frozen=True)
class BenchmarkSample:
    id: str
    question: str
    gold_answer: str
    oracle_evidence: list[Evidence]
    long_context: str
    distractors: list[Distractor]
    evidence_position: str
    context_length: int
    evidence_density: str
    distractor_similarity: str
    reasoning_type: str
    source: str = "controlled"
    answer_type: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id or not self.question or not self.gold_answer:
            raise ValueError("Sample id, question, and gold_answer are required.")
        if not self.long_context:
            raise ValueError(f"Sample {self.id} has no long context.")
        if self.source not in SOURCES:
            raise ValueError(f"Unsupported source: {self.source}")
        if self.evidence_position not in EVIDENCE_POSITIONS:
            raise ValueError(f"Unsupported evidence position: {self.evidence_position}")
        if self.context_length < 0:
            raise ValueError(f"Context length must be non-negative: {self.context_length}")
        if self.evidence_density not in EVIDENCE_DENSITIES:
            raise ValueError(f"Unsupported evidence density: {self.evidence_density}")
        if self.distractor_similarity not in DISTRACTOR_SIMILARITIES:
            raise ValueError(f"Unsupported distractor similarity: {self.distractor_similarity}")
        if self.reasoning_type not in REASONING_TYPES:
            raise ValueError(f"Unsupported reasoning type: {self.reasoning_type}")
        if self.answer_type not in ANSWER_TYPES:
            raise ValueError(f"Unsupported answer type: {self.answer_type}")
        if not isinstance(self.metadata, dict):
            raise ValueError("Sample metadata must be a dictionary.")

    @property
    def gold_evidence_ids(self) -> list[str]:
        return [evidence.evidence_id for evidence in self.oracle_evidence]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "question": self.question,
            "gold_answer": self.gold_answer,
            "oracle_evidence": [item.to_dict() for item in self.oracle_evidence],
            "long_context": self.long_context,
            "distractors": [item.to_dict() for item in self.distractors],
            "context_length": self.context_length,
            "evidence_position": self.evidence_position,
            "evidence_density": self.evidence_density,
            "distractor_similarity": self.distractor_similarity,
            "reasoning_type": self.reasoning_type,
            "answer_type": self.answer_type,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BenchmarkSample":
        return cls(
            id=str(payload["id"]),
            question=str(payload["question"]),
            gold_answer=str(payload["gold_answer"]),
            oracle_evidence=[
                Evidence.from_dict(item) for item in payload.get("oracle_evidence", [])
            ],
            long_context=str(payload["long_context"]),
            distractors=[
                Distractor.from_dict(item) for item in payload.get("distractors", [])
            ],
            evidence_position=str(payload["evidence_position"]),
            context_length=int(payload["context_length"]),
            evidence_density=str(payload["evidence_density"]),
            distractor_similarity=str(payload["distractor_similarity"]),
            reasoning_type=str(payload["reasoning_type"]),
            source=str(payload.get("source", "controlled")),
            answer_type=str(payload.get("answer_type", "unknown")),
            metadata=dict(payload.get("metadata", {})),
        )


def format_evidence(evidence: list[Evidence]) -> str:
    lines = []
    for item in evidence:
        title = f" title={item.title}." if item.title else ""
        lines.append(f"[passage_id: {item.evidence_id}]{title} {item.text}")
    return "\n".join(lines)


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None
