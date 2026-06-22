import re
from dataclasses import dataclass, field
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from disclosure_alpha.dictionaries import SEVERITY_WORDS, TOPIC_KEYWORDS
from disclosure_alpha.embedding_service import semantic_similarity
from disclosure_alpha.text_matching import (
    align_sentences,
    extract_numeric_tokens,
    split_sentences,
    topic_intensity,
    topic_phrase_matches,
    tokenize_words,
)
from disclosure_alpha.text_metrics import SectionTextInput, compute_text_metrics


@dataclass
class SectionDiffResult:
    current_section_id: str | None = None
    prior_section_id: str | None = None
    lexical_similarity: float | None = None
    semantic_similarity: float | None = None
    length_change_pct: float | None = None
    new_topics: list[str] = field(default_factory=list)
    removed_topics: list[str] = field(default_factory=list)
    intensified_topics: list[str] = field(default_factory=list)
    disclosure_change_score: float | None = None
    disclosure_change_score_v2: float | None = None
    diff_summary: str = ""
    confidence_score: float = 0.0
    language_deltas: dict[str, float] = field(default_factory=dict)
    added_sentence_count: int = 0
    removed_sentence_count: int = 0
    changed_numeric_count: int = 0
    added_risk_language_score: float | None = None
    diff_evidence: dict[str, Any] = field(default_factory=dict)


def lexical_similarity(text_a: str, text_b: str) -> float:
    if not text_a.strip() or not text_b.strip():
        return 0.0
    vec = TfidfVectorizer(max_features=2000)
    matrix = vec.fit_transform([text_a, text_b])
    return float(max(0.0, min(1.0, cosine_similarity(matrix[0:1], matrix[1:2])[0][0])))


def extract_topics(text: str) -> set[str]:
    found: set[str] = set()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if topic_phrase_matches(text, keywords):
            found.add(topic)
    return found


def _topic_intensity(text: str, topic: str) -> float:
    return topic_intensity(text, topic, TOPIC_KEYWORDS, SEVERITY_WORDS)


def _v1_change_score(
    *,
    sem: float,
    lex: float,
    length_change: float,
    new_topics: list[str],
    intensified: list[str],
) -> float:
    new_topic_score = min(1.0, len(new_topics) / 3.0)
    intensified_score = min(1.0, len(intensified) / 3.0)
    length_component = max(0.0, min(1.0, length_change))
    combined_sim = 0.6 * sem + 0.4 * lex
    change_score = (
        40 * (1 - combined_sim)
        + 20 * length_component
        + 20 * new_topic_score
        + 20 * intensified_score
    )
    return max(0.0, min(100.0, change_score))


def _severity_density(text: str) -> float:
    words = tokenize_words(text)
    if not words:
        return 0.0
    return sum(1 for w in words if w in SEVERITY_WORDS) / len(words)


def _added_risk_language_score(added_text: str) -> float | None:
    if not added_text.strip():
        return None
    metrics = compute_text_metrics(SectionTextInput("x", added_text))
    tone = (
        (metrics.negative_word_ratio or 0)
        + (metrics.uncertainty_word_ratio or 0)
        + (metrics.litigious_word_ratio or 0)
        + (metrics.constraining_word_ratio or 0)
    ) * 100
    severity = _severity_density(added_text) * 100
    topic_hits = len(extract_topics(added_text))
    topic_component = min(100.0, topic_hits * 25.0)
    return min(100.0, 0.45 * tone + 0.35 * severity + 0.20 * topic_component)


def _numeric_change_evidence(
    current_sentences: list[str],
    prior_sentences: list[str],
    added: list[str],
    removed: list[str],
    matched: list[tuple[int, int, float]],
) -> tuple[int, dict[str, Any]]:
    prior_nums = set(extract_numeric_tokens(" ".join(prior_sentences)))
    cur_nums = set(extract_numeric_tokens(" ".join(current_sentences)))
    added_nums = sorted(cur_nums - prior_nums)
    removed_nums = sorted(prior_nums - cur_nums)

    changed = 0
    for ci, pi, sim in matched:
        if sim >= 0.92:
            continue
        c_nums = set(extract_numeric_tokens(current_sentences[ci]))
        p_nums = set(extract_numeric_tokens(prior_sentences[pi]))
        changed += len(c_nums.symmetric_difference(p_nums))

    changed += len(added_nums) + len(removed_nums)
    evidence = {
        "added_numeric_tokens": added_nums[:20],
        "removed_numeric_tokens": removed_nums[:20],
        "matched_sentence_pairs": len(matched),
        "added_sentence_samples": added[:3],
        "removed_sentence_samples": removed[:3],
    }
    return changed, evidence


def _v2_change_score(
    *,
    v1_score: float,
    added_sentences: list[str],
    prior_sentences: list[str],
    added_risk: float | None,
    changed_numeric: int,
    new_topics: list[str],
    intensified: list[str],
) -> float:
    n_prior = max(1, len(prior_sentences))
    added_ratio = min(1.0, len(added_sentences) / n_prior)
    numeric_component = min(1.0, changed_numeric / 5.0)
    risk_component = (added_risk or 0.0) / 100.0
    topic_component = min(1.0, (len(new_topics) + len(intensified)) / 3.0)
    alignment_score = (
        30 * added_ratio
        + 35 * risk_component
        + 20 * numeric_component
        + 15 * topic_component
    )
    # ponytail: blend with v1 so high-similarity docs with severe additions still rise
    return max(0.0, min(100.0, 0.55 * alignment_score + 0.45 * v1_score))


def compute_section_diff(
    *,
    current_text: str,
    prior_text: str | None,
    current_section_id: str | None = None,
    prior_section_id: str | None = None,
) -> SectionDiffResult:
    if not prior_text:
        return SectionDiffResult(
            current_section_id=current_section_id,
            prior_section_id=prior_section_id,
            disclosure_change_score=None,
            disclosure_change_score_v2=None,
            diff_summary="No prior comparable filing section available.",
            confidence_score=0.2,
        )

    lex = lexical_similarity(current_text, prior_text)
    sem = semantic_similarity(current_text, prior_text)
    cur_words = len(re.findall(r"\b\w+\b", current_text))
    prior_words = max(1, len(re.findall(r"\b\w+\b", prior_text)))
    length_change = (cur_words - prior_words) / prior_words

    cur_topics = extract_topics(current_text)
    prior_topics = extract_topics(prior_text)
    new_topics = sorted(cur_topics - prior_topics)
    removed_topics = sorted(prior_topics - cur_topics)
    intensified: list[str] = []
    for topic in cur_topics & prior_topics:
        if _topic_intensity(current_text, topic) > _topic_intensity(prior_text, topic) * 1.2:
            intensified.append(topic)

    change_score = _v1_change_score(
        sem=sem,
        lex=lex,
        length_change=length_change,
        new_topics=new_topics,
        intensified=intensified,
    )

    cur_metrics = compute_text_metrics(SectionTextInput("x", current_text))
    prior_metrics = compute_text_metrics(SectionTextInput("x", prior_text))
    language_deltas = {
        "negative_language_delta": round(
            (cur_metrics.negative_word_ratio - prior_metrics.negative_word_ratio) * 100, 4
        ),
        "uncertainty_language_delta": round(
            (cur_metrics.uncertainty_word_ratio - prior_metrics.uncertainty_word_ratio) * 100, 4
        ),
        "legal_language_delta": round(
            (cur_metrics.litigious_word_ratio - prior_metrics.litigious_word_ratio) * 100, 4
        ),
        "constraining_language_delta": round(
            (cur_metrics.constraining_word_ratio - prior_metrics.constraining_word_ratio) * 100, 4
        ),
    }
    metric_shift = abs(cur_metrics.uncertainty_word_ratio - prior_metrics.uncertainty_word_ratio)
    confidence = max(0.4, min(0.95, 0.7 + sem * 0.2 - metric_shift))

    current_sentences = split_sentences(current_text)
    prior_sentences = split_sentences(prior_text)
    added, removed, matched = align_sentences(current_sentences, prior_sentences)
    added_text = " ".join(added)
    added_risk = _added_risk_language_score(added_text)
    changed_numeric, numeric_evidence = _numeric_change_evidence(
        current_sentences, prior_sentences, added, removed, matched
    )
    change_score_v2 = _v2_change_score(
        v1_score=change_score,
        added_sentences=added,
        prior_sentences=prior_sentences,
        added_risk=added_risk,
        changed_numeric=changed_numeric,
        new_topics=new_topics,
        intensified=intensified,
    )

    diff_evidence: dict[str, Any] = {
        "sentence_alignment": {
            "added_count": len(added),
            "removed_count": len(removed),
            "matched_count": len(matched),
        },
        "added_language": {
            "negative_word_ratio": compute_text_metrics(SectionTextInput("x", added_text)).negative_word_ratio
            if added_text.strip()
            else None,
            "added_risk_language_score": added_risk,
        },
        "numeric_changes": numeric_evidence,
        "new_topics": new_topics,
        "intensified_topics": intensified,
    }

    summary_parts = []
    if new_topics:
        summary_parts.append(f"New topics: {', '.join(new_topics)}.")
    if removed_topics:
        summary_parts.append(f"Removed topics: {', '.join(removed_topics)}.")
    if intensified:
        summary_parts.append(f"Intensified topics: {', '.join(intensified)}.")
    if added:
        summary_parts.append(f"Added {len(added)} sentence(s).")
    if changed_numeric:
        summary_parts.append(f"Numeric disclosure changes: {changed_numeric}.")
    if not summary_parts:
        summary_parts.append("Minor wording changes detected.")

    return SectionDiffResult(
        current_section_id=current_section_id,
        prior_section_id=prior_section_id,
        lexical_similarity=round(lex, 4),
        semantic_similarity=round(sem, 4),
        length_change_pct=round(length_change, 4),
        new_topics=new_topics,
        removed_topics=removed_topics,
        intensified_topics=intensified,
        disclosure_change_score=round(change_score, 2),
        disclosure_change_score_v2=round(change_score_v2, 2),
        diff_summary=" ".join(summary_parts),
        confidence_score=round(confidence, 4),
        language_deltas=language_deltas,
        added_sentence_count=len(added),
        removed_sentence_count=len(removed),
        changed_numeric_count=changed_numeric,
        added_risk_language_score=round(added_risk, 2) if added_risk is not None else None,
        diff_evidence=diff_evidence,
    )
