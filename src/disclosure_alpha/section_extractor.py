import hashlib
import re
from dataclasses import dataclass, field

from disclosure_alpha.dictionaries import REQUIRED_SECTIONS, sections_for_form_type
from disclosure_alpha.text_cleaner import clean_html_text, normalize_whitespace


@dataclass
class FilingDocument:
    cik: str
    accession_number: str
    form_type: str
    html: str


@dataclass
class ExtractedSection:
    section_name: str
    raw_text: str
    cleaned_text: str
    text_hash: str
    word_count: int
    sentence_count: int
    extraction_confidence: float
    extraction_method: str
    parser_version: str
    start_offset: int | None = None
    end_offset: int | None = None
    warnings: list[str] = field(default_factory=list)


def _count_sentences(text: str) -> int:
    if not text:
        return 0
    parts = re.split(r"[.!?]+\s+", text)
    return max(1, len([p for p in parts if p.strip()]))


def _count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _find_heading_positions(text: str, section_map: dict[str, str]) -> list[tuple[int, str, str]]:
    positions: list[tuple[int, str, str]] = []
    lower = text.lower()
    for section_name, pattern in section_map.items():
        for match in re.finditer(pattern, lower, flags=re.IGNORECASE):
            positions.append((match.start(), section_name, match.group(0)))
    positions.sort(key=lambda x: x[0])
    return positions


def _is_toc_like(text: str, start: int, heading: str) -> bool:
    window = text[start : start + 200]
    if re.search(r"\.\.\.|\.{3,}|\t\d+\s*$", window):
        return True
    if len(heading) < 10 and re.search(r"\d+\s*$", window):
        return True
    return False


def _pick_section_start(
    text: str, positions: list[tuple[int, str, str]], section_name: str
) -> tuple[int, float] | None:
    candidates = [(pos, name, heading) for pos, name, heading in positions if name == section_name]
    if not candidates:
        return None
    best_pos: int | None = None
    for pos, _, heading in candidates:
        if _is_toc_like(text, pos, heading):
            continue
        best_pos = pos
    if best_pos is None:
        best_pos = candidates[-1][0]
    confidence = 0.9 if len(candidates) == 1 else 0.75
    if _is_toc_like(text, best_pos, candidates[0][2]):
        confidence = 0.4
    return best_pos, confidence


def required_sections_present(form_type: str, extracted: list[ExtractedSection]) -> bool:
    base = form_type.replace("/A", "").replace("-A", "").upper()
    required = REQUIRED_SECTIONS.get(base, REQUIRED_SECTIONS.get("10-K", []))
    found = {s.section_name for s in extracted}
    return all(r in found for r in required)


def extract_sections(document: FilingDocument) -> list[ExtractedSection]:
    from disclosure_alpha.version import PARSER_VERSION

    parser_version = PARSER_VERSION
    cleaned_full = clean_html_text(document.html)
    section_map = sections_for_form_type(document.form_type)
    positions = _find_heading_positions(cleaned_full, section_map)
    section_starts: dict[str, tuple[int, float]] = {}
    for section_name in section_map:
        picked = _pick_section_start(cleaned_full, positions, section_name)
        if picked:
            section_starts[section_name] = picked

    ordered = sorted(section_starts.items(), key=lambda x: x[1][0])
    results: list[ExtractedSection] = []
    for idx, (section_name, (start, base_conf)) in enumerate(ordered):
        end = len(cleaned_full)
        if idx + 1 < len(ordered):
            end = ordered[idx + 1][1][0]
        raw_slice = cleaned_full[start:end].strip()
        cleaned = normalize_whitespace(raw_slice)
        word_count = _count_words(cleaned)
        sentence_count = _count_sentences(cleaned)
        confidence = base_conf
        warnings: list[str] = []
        if word_count < 50:
            confidence = min(confidence, 0.35)
            warnings.append("short_section")
        if end == len(cleaned_full):
            confidence = min(confidence, 0.6)
            warnings.append("open_ended_boundary")
        results.append(
            ExtractedSection(
                section_name=section_name,
                raw_text=raw_slice,
                cleaned_text=cleaned,
                text_hash=_text_hash(cleaned),
                word_count=word_count,
                sentence_count=sentence_count,
                extraction_confidence=round(confidence, 2),
                extraction_method="heading_boundary_v1",
                parser_version=parser_version,
                start_offset=start,
                end_offset=end,
                warnings=warnings,
            )
        )
    return results
