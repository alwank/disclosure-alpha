"""Shared phrase and token matching helpers for text metrics and diff engine."""

from __future__ import annotations

import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_SEVERITY_WINDOW = 10
_NUMERIC_TOKEN = re.compile(
    r"(?:\$)?\d[\d,]*(?:\.\d+)?%?|\b(?:january|february|march|april|may|june|july|august|"
    r"september|october|november|december)\s+\d{1,2},?\s+\d{4}\b|\b\d{4}\b",
    re.IGNORECASE,
)


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


def extract_numeric_tokens(text: str) -> list[str]:
    """Normalize percentages, dollar amounts, dates, and counts for diff comparison."""
    tokens: list[str] = []
    for match in _NUMERIC_TOKEN.finditer(text or ""):
        raw = match.group(0).lower().replace(",", "").strip()
        if raw.startswith("$"):
            raw = raw[1:]
        if raw.endswith("%"):
            raw = f"pct:{raw[:-1]}"
        tokens.append(raw)
    return tokens


def align_sentences(
    current_sentences: list[str],
    prior_sentences: list[str],
    *,
    match_threshold: float = 0.55,
) -> tuple[list[str], list[str], list[tuple[int, int, float]]]:
    """Match sentences via TF-IDF cosine similarity; return added, removed, matched triples."""
    if not current_sentences and not prior_sentences:
        return [], [], []
    if not current_sentences:
        return [], list(prior_sentences), []
    if not prior_sentences:
        return list(current_sentences), [], []

    all_sents = current_sentences + prior_sentences
    vec = TfidfVectorizer(max_features=2000)
    matrix = vec.fit_transform(all_sents)
    n_cur = len(current_sentences)
    cur_mat = matrix[:n_cur]
    prior_mat = matrix[n_cur:]

    sims = cosine_similarity(cur_mat, prior_mat)
    matched_prior: set[int] = set()
    matched_cur: set[int] = set()
    pairs: list[tuple[int, int, float]] = []

    for ci in range(n_cur):
        best_pi = int(sims[ci].argmax())
        best_sim = float(sims[ci, best_pi])
        if best_sim >= match_threshold and best_pi not in matched_prior:
            matched_prior.add(best_pi)
            matched_cur.add(ci)
            pairs.append((ci, best_pi, best_sim))

    added = [current_sentences[i] for i in range(n_cur) if i not in matched_cur]
    removed = [prior_sentences[i] for i in range(len(prior_sentences)) if i not in matched_prior]
    return added, removed, pairs


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
