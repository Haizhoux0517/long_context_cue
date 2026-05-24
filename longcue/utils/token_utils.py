from __future__ import annotations

import re

TOKEN_PATTERN = re.compile(r"\S+")


def estimate_tokens(text: str) -> int:
    """Dependency-free length proxy used by deterministic synthetic generation."""
    return len(TOKEN_PATTERN.findall(text))


def chunk_words(text: str, chunk_size: int, overlap: int = 0) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive.")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size.")

    words = TOKEN_PATTERN.findall(text)
    chunks: list[str] = []
    step = chunk_size - overlap
    for start in range(0, len(words), step):
        chunk = words[start : start + chunk_size]
        if not chunk:
            break
        chunks.append(" ".join(chunk))
        if start + chunk_size >= len(words):
            break
    return chunks
