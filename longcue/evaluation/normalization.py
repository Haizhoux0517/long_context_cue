from __future__ import annotations

import re
import string
import unicodedata

ARTICLES = re.compile(r"\b(a|an|the)\b", re.IGNORECASE)
SYNTHETIC_SUFFIX = re.compile(r"^0\d{2,}$")


def normalize_answer(text: str) -> str:
    lowered = text.lower()
    without_punctuation = "".join(
        character for character in lowered if character not in string.punctuation
    )
    without_articles = ARTICLES.sub(" ", without_punctuation)
    return " ".join(without_articles.split())


def answer_tokens(text: str) -> list[str]:
    normalized = normalize_answer(text)
    return normalized.split() if normalized else []


def normalize_answer_relaxed(
    text: str, *, answer_type: str = "unknown", reasoning_type: str = "unknown"
) -> str:
    """Normalize answer variants used by controlled synthetic entities."""
    ascii_folded = "".join(
        character
        for character in unicodedata.normalize("NFKD", text.lower())
        if not unicodedata.combining(character)
    )
    separated = ascii_folded.replace("-", " ").replace("_", " ")
    without_punctuation = "".join(
        " " if unicodedata.category(character).startswith("P") else character
        for character in separated
    )
    without_articles = ARTICLES.sub(" ", without_punctuation)
    tokens = without_articles.split()
    if answer_type != "number" and reasoning_type != "arithmetic":
        while tokens and SYNTHETIC_SUFFIX.fullmatch(tokens[-1]):
            tokens.pop()
    return " ".join(tokens)


def answer_tokens_relaxed(
    text: str, *, answer_type: str = "unknown", reasoning_type: str = "unknown"
) -> list[str]:
    normalized = normalize_answer_relaxed(
        text, answer_type=answer_type, reasoning_type=reasoning_type
    )
    return normalized.split() if normalized else []
