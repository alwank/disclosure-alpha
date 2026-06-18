import re
from dataclasses import dataclass, field

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from disclosure_alpha.dictionaries import SEVERITY_WORDS, TOPIC_KEYWORDS
from disclosure_alpha.embedding_service import semantic_similarity
from disclosure_alpha.text_metrics import SectionTextInput, TextMetricResult, compute_text_metrics


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
    diff_summary: str = ""
    confidence_score: float = 0.0
    language_deltas: dict[str, float] = field(default_factory=dict)


def lexical_similarity(text_a: str, text_b: str) -> float:
    if not text_a.strip() or not text_b.strip():
        return 0.0
    vec = TfidfVectorizer(max_features=2000)
    matrix = vec.fit_transform([text_a, text_b])
    return float(max(0.0, min(1.0, cosine_similarity(matrix[0:1], matrix[1:2])[0][0])))


def extract_topics(text: str) -> set[str]:
    lower = text.lower()
    found: set[str] = set()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            found.add(topic)
    return found


def _topic_intensity(text: str, topic: str) -> float:
    keywords = TOPIC_KEYWORDS.get(topic, [])
    lower = text.lower()
    hits = sum(lower.count(kw) for kw in keywords)
    severity_hits = sum(1 for w in SEVERITY_WORDS if w in lower)
    return hits + severity_hits * 0.5


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
    change_score = max(0.0, min(100.0, change_score))

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

    summary_parts = []
    if new_topics:
        summary_parts.append(f"New topics: {', '.join(new_topics)}.")
    if removed_topics:
        summary_parts.append(f"Removed topics: {', '.join(removed_topics)}.")
    if intensified:
        summary_parts.append(f"Intensified topics: {', '.join(intensified)}.")
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
        diff_summary=" ".join(summary_parts),
        confidence_score=round(confidence, 4),
        language_deltas=language_deltas,
    )
