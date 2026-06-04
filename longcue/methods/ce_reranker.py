from __future__ import annotations

from functools import lru_cache
from typing import Any, Iterable


def cross_encoder_ranking(
    query: str,
    chunks: list[str],
    candidate_indices: Iterable[int],
    *,
    model_name: str = "cross-encoder/ms-marco-MiniLM-L6-v2",
    batch_size: int = 32,
    device: str | None = None,
) -> list[tuple[int, float]]:
    """Rerank first-stage candidate chunks with a SentenceTransformers CrossEncoder."""
    indices = [int(i) for i in candidate_indices]
    if not chunks or not indices:
        return []

    model = _get_cross_encoder(model_name, _normalize_device(device))
    pairs = [(query, chunks[i]) for i in indices]

    try:
        scores = model.predict(pairs, batch_size=batch_size, show_progress_bar=False)
    except TypeError:
        scores = model.predict(pairs, batch_size=batch_size)

    ranked = [(idx, float(score)) for idx, score in zip(indices, scores)]
    return sorted(ranked, key=lambda item: (-item[1], item[0]))


def _normalize_device(device: str | None) -> str | None:
    if device is None:
        return _default_device()
    value = str(device).strip().lower()
    if value in {"", "auto", "none"}:
        return _default_device()
    return value


def _default_device() -> str:
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


@lru_cache(maxsize=4)
def _get_cross_encoder(model_name: str, device: str | None) -> Any:
    from sentence_transformers import CrossEncoder

    return CrossEncoder(model_name, device=device)
