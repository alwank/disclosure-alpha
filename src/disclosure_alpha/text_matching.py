"""Shared phrase and token matching helpers for text metrics and diff engine."""

import re

_SEVERITY_WINDOW = 10


def tokenize_words(text: str) -> list[str]:
    return re.findall(r"\b[a-zA-Z]+\b", text.lower())


def phrase_pattern(phrase: str) -> str:
    parts = [re.escape(part) for part in re.split(r"[\s-]+", phrase.lower()) if part]
    body = r"[\s-]+".join(parts)
    return rf"(?<![a-z0-9]){body}(?![a-z0-9])"


def phrase_count(lower: str, phrase: str) -> int:
    return len(re.findall(phrase_pattern(phrase), lower))


def phrase_matches(lower: str, phrase: str) -> bool:
    return bool(re.search(phrase_pattern(phrase), lower))


def split_sentences(text: str) -> list[str]:
    if not text.strip():
        return []
    parts = re.split(r"[.!?]+\s+", text.strip())
    return [p for p in parts if p.strip()]


def boilerplate_hits(text: str, phrases: tuple[str, ...] | list[str]) -> int:
    """Count each phrase at most once per sentence."""
    total = 0
    for sent in split_sentences(text):
        lower = sent.lower()
        for phrase in phrases:
            if phrase_matches(lower, phrase):
                total += 1
    return total


def _keyword_token_indices(text: str, keyword: str) -> list[int]:
    words = tokenize_words(text)
    kw = keyword.lower()
    if " " not in kw and "-" not in kw:
        return [i for i, w in enumerate(words) if w == kw]
    lower = text.lower()
    indices: list[int] = []
    for match in re.finditer(phrase_pattern(kw), lower):
        prefix = text[: match.start()]
        indices.append(len(tokenize_words(prefix)))
    return indices


def topic_phrase_matches(text: str, keywords: list[str]) -> bool:
    lower = (text or "").lower()
    return any(phrase_matches(lower, kw) for kw in keywords)


def topic_intensity(text: str, topic: str, topic_keywords: dict[str, list[str]], severity_words: frozenset[str]) -> float:
    keywords = topic_keywords.get(topic, [])
    if not keywords:
        return 0.0
    words = tokenize_words(text)
    hit_indices: list[int] = []
    hits = 0
    for kw in keywords:
        for idx in _keyword_token_indices(text, kw):
            hit_indices.append(idx)
            hits += 1
    severity_hits = 0
    for idx in hit_indices:
        start = max(0, idx - _SEVERITY_WINDOW)
        end = min(len(words), idx + _SEVERITY_WINDOW + 1)
        if any(w in severity_words for w in words[start:end]):
            severity_hits += 1
    return hits + severity_hits * 0.5
