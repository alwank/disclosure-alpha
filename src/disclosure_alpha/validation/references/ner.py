"""Optional spacy NER entity density reference."""

from __future__ import annotations

import os

from disclosure_alpha.text_metrics import tokenize_words
from disclosure_alpha.validation.types import CorpusRow

_ENTITY_LABELS = frozenset({"ORG", "GPE", "PER", "MONEY", "DATE"})


def ner_available() -> bool:
    try:
        import spacy  # noqa: F401
    except ImportError:
        return False
    return True


def _load_nlp():
    import spacy

    model = os.environ.get("SPACY_MODEL", "en_core_web_sm")
    try:
        return spacy.load(model)
    except OSError as exc:
        raise RuntimeError(
            f"spacy model {model!r} not found; run: python -m spacy download {model}"
        ) from exc


def compute_ner_entity_density(text: str, *, nlp=None) -> float:
    words = tokenize_words(text)
    if not words:
        return 0.0
    if nlp is None:
        nlp = _load_nlp()
    doc = nlp(text[:1_000_000])
    count = sum(1 for ent in doc.ents if ent.label_ in _ENTITY_LABELS)
    return count / len(words)


def compute_ner_densities(
    rows: list[CorpusRow],
    *,
    progress_every: int = 25,
) -> tuple[dict[str, float] | None, str]:
    if not ner_available():
        return None, "spacy not installed; pip install -e '.[validation]'"
    try:
        nlp = _load_nlp()
    except RuntimeError as exc:
        return None, str(exc)

    out: dict[str, float] = {}
    total = len(rows)
    for i, row in enumerate(rows, start=1):
        out[row.ticker] = compute_ner_entity_density(row.cleaned_text, nlp=nlp)
        if progress_every and i % progress_every == 0:
            print(f"  NER progress: {i}/{total}", flush=True)
    if total and (total % progress_every != 0):
        print(f"  NER progress: {total}/{total}", flush=True)
    return out, ""
