"""Optional spacy NER entity density reference."""

from __future__ import annotations

import hashlib
import os

from disclosure_alpha.text_metrics import tokenize_words
from disclosure_alpha.validation.artifact_cache import cache_key, read_json, write_json
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
    batch_size: int = 8,
    use_cache: bool = True,
    refresh_cache: bool = False,
) -> tuple[dict[str, float] | None, str]:
    if not ner_available():
        return None, "spacy not installed; pip install -e '.[validation]'"
    try:
        nlp = _load_nlp()
    except RuntimeError as exc:
        return None, str(exc)

    model = os.environ.get("SPACY_MODEL", "en_core_web_sm")
    out: dict[str, float] = {}
    total = len(rows)
    pending_rows: list[CorpusRow] = []
    pending_texts: list[str] = []
    pending_words: list[int] = []
    pending_keys: list[str] = []
    done = 0
    for row in rows:
        text = row.cleaned_text[:1_000_000]
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        key = cache_key("ner_density_v1", model, text_hash)
        if use_cache and not refresh_cache:
            cached = read_json(key)
            if cached and isinstance(cached.get("density"), (float, int)):
                out[row.ticker] = float(cached["density"])
                done += 1
                if progress_every and done % progress_every == 0:
                    print(f"  NER progress: {done}/{total}", flush=True)
                continue
        pending_rows.append(row)
        pending_texts.append(text)
        pending_words.append(len(tokenize_words(text)))
        pending_keys.append(key)

    for row, doc, n_words, key in zip(
        pending_rows,
        nlp.pipe(pending_texts, batch_size=batch_size),
        pending_words,
        pending_keys,
    ):
        if not n_words:
            density = 0.0
        else:
            count = sum(1 for ent in doc.ents if ent.label_ in _ENTITY_LABELS)
            density = count / n_words
        out[row.ticker] = density
        if use_cache:
            write_json(key, {"density": density})
        done += 1
        if progress_every and done % progress_every == 0:
            print(f"  NER progress: {done}/{total}", flush=True)
    if total and (done % progress_every != 0):
        print(f"  NER progress: {total}/{total}", flush=True)
    return out, ""
