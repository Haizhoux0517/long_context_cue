from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import math
import re
from typing import Any, Iterable

from longcue.data.schema import BenchmarkSample
from longcue.utils.token_utils import chunk_words

from .ce_reranker import cross_encoder_ranking

PASSAGE_ID_RE = re.compile(r"\[passage_id:\s*([^\]\s]+)\]", re.IGNORECASE)
WORD_RE = re.compile(r"\w+")


@dataclass(frozen=True)
class RetrievedChunk:
    index: int
    text: str
    score: float
    passage_ids: tuple[str, ...]
    retriever: str


def extract_passage_ids(text: str) -> tuple[str, ...]:
    """Extract neutral passage identifiers from a passage-annotated chunk."""
    ids = []
    seen = set()
    for match in PASSAGE_ID_RE.finditer(text):
        pid = match.group(1).strip()
        if pid and pid not in seen:
            ids.append(pid)
            seen.add(pid)
    return tuple(ids)


def make_chunks(context: str, *, chunk_size: int = 220, overlap: int = 40) -> list[str]:
    return chunk_words(context, chunk_size=chunk_size, overlap=overlap)


def retrieve_chunks(
    *,
    sample: BenchmarkSample,
    retriever: str,
    top_k: int,
    chunk_size: int = 220,
    overlap: int = 40,
    dense_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    rrf_k: int = 60,
    iterative_seed_k: int = 2,
    iterative_expansion_words: int = 96,
    ce_rerank_model_name: str = "cross-encoder/ms-marco-MiniLM-L6-v2",
    ce_rerank_batch_size: int = 32,
    ce_rerank_first_stage_k: int = 64,
    ce_rerank_device: str | None = None,
) -> list[RetrievedChunk]:
    """Retrieve chunks under a named retriever family.

    The function is deterministic for lexical, hybrid fusion, iterative expansion, and
    oracle retrieval. Dense retrieval is deterministic for a fixed sentence-transformer
    checkpoint and device, but requires the optional ``sentence-transformers`` package.
    """
    retriever = retriever.lower().strip()
    if top_k <= 0:
        return []
    if retriever == "oracle":
        return _oracle_chunks(sample, top_k=top_k)

    chunks = make_chunks(sample.long_context, chunk_size=chunk_size, overlap=overlap)
    if not chunks:
        return []

    if retriever == "lexical":
        ranking = lexical_ranking(sample.question, chunks)
        return _materialize("lexical", chunks, ranking[:top_k])

    if retriever == "dense":
        ranking = dense_ranking(sample.question, chunks, model_name=dense_model_name)
        return _materialize("dense", chunks, ranking[:top_k])

    if retriever == "hybrid":
        lexical = [idx for idx, _ in lexical_ranking(sample.question, chunks)]
        dense = [idx for idx, _ in dense_ranking(sample.question, chunks, model_name=dense_model_name)]
        fused = reciprocal_rank_fusion([lexical, dense], rrf_k=rrf_k)
        return _materialize("hybrid", chunks, fused[:top_k])

    if retriever.startswith("hybrid_ce"):
        lexical = [idx for idx, _ in lexical_ranking(sample.question, chunks)]
        dense = [idx for idx, _ in dense_ranking(sample.question, chunks, model_name=dense_model_name)]
        fused = reciprocal_rank_fusion([lexical, dense], rrf_k=rrf_k)
        candidate_k = _candidate_k_from_ce_label(retriever, default=ce_rerank_first_stage_k)
        candidate_indices = [idx for idx, _ in fused[:candidate_k]]
        reranked = cross_encoder_ranking(
            sample.question,
            chunks,
            candidate_indices,
            model_name=ce_rerank_model_name,
            batch_size=ce_rerank_batch_size,
            device=ce_rerank_device,
        )
        return _materialize(retriever, chunks, reranked[:top_k])

    if retriever in {"iterative", "multi_hop_iterative", "multihop_iterative"}:
        first_pass = lexical_ranking(sample.question, chunks)
        seed_chunks = [chunks[idx] for idx, _ in first_pass[: max(1, iterative_seed_k)]]
        expansion = _query_expansion_text(seed_chunks, max_words=iterative_expansion_words)
        expanded_query = f"{sample.question}\n{expansion}".strip()
        second_pass = lexical_ranking(expanded_query, chunks)
        fused = reciprocal_rank_fusion(
            [[idx for idx, _ in first_pass], [idx for idx, _ in second_pass]],
            rrf_k=rrf_k,
        )
        return _materialize("iterative", chunks, fused[:top_k])

    raise ValueError(
        f"Unsupported retriever '{retriever}'. "
        "Use lexical, dense, hybrid, iterative, or oracle."
    )



def _candidate_k_from_ce_label(label: str, *, default: int) -> int:
    """Parse labels such as hybrid_ce32, hybrid_ce64, or hybrid_ce128."""
    import re

    match = re.search(r"hybrid_ce(\d+)", str(label).lower().strip())
    if match:
        return max(1, int(match.group(1)))
    return max(1, int(default))


def lexical_ranking(query: str, chunks: list[str]) -> list[tuple[int, float]]:
    if not chunks:
        return []
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer

        matrix = TfidfVectorizer().fit_transform(chunks + [query])
        scores = (matrix[:-1] @ matrix[-1].T).toarray().ravel()
        values = [float(score) for score in scores]
    except ImportError:
        query_terms = set(WORD_RE.findall(query.lower()))
        values = [
            float(len(query_terms.intersection(WORD_RE.findall(chunk.lower()))))
            for chunk in chunks
        ]
    return sorted(enumerate(values), key=lambda item: (-item[1], item[0]))


def dense_ranking(
    query: str,
    chunks: list[str],
    *,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> list[tuple[int, float]]:
    if not chunks:
        return []
    try:
        from sentence_transformers import SentenceTransformer
        from sentence_transformers.util import cos_sim
    except ImportError as exc:  # pragma: no cover - depends on optional package.
        raise ImportError(
            "Dense and hybrid retriever-family ablations require the optional "
            "'sentence-transformers' package. Install it with "
            "'pip install sentence-transformers'."
        ) from exc

    model = _get_sentence_transformer(model_name)
    query_embedding = model.encode([query], normalize_embeddings=True, show_progress_bar=False)
    chunk_embeddings = model.encode(chunks, normalize_embeddings=True, show_progress_bar=False)
    scores = cos_sim(query_embedding, chunk_embeddings)[0].cpu().tolist()
    return sorted(
        ((idx, float(score)) for idx, score in enumerate(scores)),
        key=lambda item: (-item[1], item[0]),
    )



@lru_cache(maxsize=2)
def _get_sentence_transformer(model_name: str) -> Any:
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def reciprocal_rank_fusion(
    rankings: Iterable[Iterable[int]],
    *,
    rrf_k: int = 60,
) -> list[tuple[int, float]]:
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[int(doc_id)] = scores.get(int(doc_id), 0.0) + 1.0 / (rrf_k + rank)
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))


def retrieval_diagnostics(
    retrieved: list[RetrievedChunk],
    gold_evidence_ids: Iterable[str],
) -> dict[str, float]:
    gold = {str(pid) for pid in gold_evidence_ids if str(pid)}
    predicted: set[str] = set()
    for chunk in retrieved:
        predicted.update(chunk.passage_ids)
    overlap = predicted.intersection(gold)

    precision = len(overlap) / len(predicted) if predicted else 0.0
    recall = len(overlap) / len(gold) if gold else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0.0
    distractor_rate = (
        len(predicted.difference(gold)) / len(predicted)
        if predicted else 0.0
    )
    return {
        "retrieved_passage_count": float(len(predicted)),
        "gold_passage_count": float(len(gold)),
        "oracle_hit_rate": float(bool(overlap)),
        "full_chain_coverage": float(bool(gold) and gold.issubset(predicted)),
        "retrieval_precision": precision,
        "retrieval_recall": recall,
        "retrieval_f1": f1,
        "distractor_id_rate": distractor_rate,
    }


def _materialize(
    retriever: str,
    chunks: list[str],
    ranked_items: list[tuple[int, float]],
) -> list[RetrievedChunk]:
    return [
        RetrievedChunk(
            index=int(index),
            text=chunks[int(index)],
            score=float(score),
            passage_ids=extract_passage_ids(chunks[int(index)]),
            retriever=retriever,
        )
        for index, score in ranked_items
    ]


def _oracle_chunks(sample: BenchmarkSample, *, top_k: int) -> list[RetrievedChunk]:
    chunks = []
    for rank, evidence in enumerate(sample.oracle_evidence[:top_k]):
        text = f"[passage_id: {evidence.evidence_id}] {evidence.text}"
        chunks.append(
            RetrievedChunk(
                index=rank,
                text=text,
                score=1.0,
                passage_ids=(evidence.evidence_id,),
                retriever="oracle",
            )
        )
    return chunks


def _query_expansion_text(chunks: list[str], *, max_words: int) -> str:
    words: list[str] = []
    for chunk in chunks:
        words.extend(WORD_RE.findall(chunk))
        if len(words) >= max_words:
            break
    return " ".join(words[:max_words])
