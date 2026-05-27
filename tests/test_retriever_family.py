from __future__ import annotations

from longcue.data.schema import BenchmarkSample, Evidence
from longcue.methods.retrievers import (
    extract_passage_ids,
    reciprocal_rank_fusion,
    retrieve_chunks,
    retrieval_diagnostics,
)


def _sample() -> BenchmarkSample:
    context = "\n\n".join(
        [
            "[passage_id: p0001] Alice founded Example Labs in Paris.",
            "[passage_id: p0002] Bob later acquired Example Labs in 2012.",
            "[passage_id: p0003] A distractor passage about unrelated football.",
        ]
    )
    return BenchmarkSample(
        id="retfam_test",
        question="Who founded Example Labs and where?",
        gold_answer="Alice in Paris",
        oracle_evidence=[
            Evidence("p0001", "Alice founded Example Labs in Paris."),
            Evidence("p0002", "Bob later acquired Example Labs in 2012."),
        ],
        long_context=context,
        distractors=[],
        evidence_position="front",
        context_length=4000,
        evidence_density="low",
        distractor_similarity="low",
        reasoning_type="multi_hop",
        source="controlled",
        answer_type="entity",
    )


def test_extract_passage_ids_preserves_order_without_duplicates() -> None:
    text = "[passage_id: p0002] x [passage_id: p0001] y [passage_id: p0002] z"
    assert extract_passage_ids(text) == ("p0002", "p0001")


def test_lexical_retrieval_reports_chain_diagnostics() -> None:
    sample = _sample()
    chunks = retrieve_chunks(sample=sample, retriever="lexical", top_k=2, chunk_size=20, overlap=0)
    diag = retrieval_diagnostics(chunks, sample.gold_evidence_ids)
    assert len(chunks) == 2
    assert diag["oracle_hit_rate"] == 1.0
    assert 0.0 <= diag["full_chain_coverage"] <= 1.0
    assert 0.0 <= diag["retrieval_recall"] <= 1.0


def test_oracle_retrieval_returns_gold_passages() -> None:
    sample = _sample()
    chunks = retrieve_chunks(sample=sample, retriever="oracle", top_k=8)
    assert [pid for chunk in chunks for pid in chunk.passage_ids] == ["p0001", "p0002"]
    diag = retrieval_diagnostics(chunks, sample.gold_evidence_ids)
    assert diag["full_chain_coverage"] == 1.0
    assert diag["retrieval_recall"] == 1.0


def test_reciprocal_rank_fusion_prefers_consensus() -> None:
    fused = reciprocal_rank_fusion([[1, 2, 3], [2, 1, 4]], rrf_k=60)
    assert fused[0][0] in {1, 2}
    assert {doc for doc, _ in fused} == {1, 2, 3, 4}
