import hashlib
import re
import warnings
from dataclasses import dataclass, field

from disclosure_alpha.dictionaries import REQUIRED_SECTIONS, sections_for_form_type
from disclosure_alpha.text_cleaner import normalize_whitespace


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


@dataclass
class ParserBlock:
    index: int
    text: str
    normalized_text: str
    element_type: str
    start_offset: int
    end_offset: int
    is_toc: bool
    is_table: bool
    is_title: bool


@dataclass
class HeadingCandidate:
    section_name: str
    block_index: int
    start_offset: int
    end_offset: int
    score: float
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


SECTION_HEADING_SPECS = {
    "item_1a_risk_factors": ("1A", "risk factors"),
    "item_1c_cybersecurity": ("1C", "cybersecurity"),
    "item_3_legal_proceedings": ("3", "legal proceedings"),
    "item_7_mdna": ("7", "management"),
    "item_7a_market_risk": ("7A", "quantitative"),
    "item_9a_controls": ("9A", "controls"),
    "item_1_legal_proceedings": ("1", "legal proceedings"),
    "item_2_mdna": ("2", "management"),
    "item_4_controls": ("4", "controls"),
    "item_1_01": ("1.01", ""),
    "item_1_05": ("1.05", ""),
    "item_2_02": ("2.02", ""),
    "item_5_02": ("5.02", ""),
    "item_8_01": ("8.01", ""),
}


def _count_sentences(text: str) -> int:
    if not text:
        return 0
    parts = re.split(r"[.!?]+\s+", text)
    return max(1, len([p for p in parts if p.strip()]))


def _count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_block_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").replace("\xa0", " ")).strip()


def _block_flags(element_type: str, text: str) -> tuple[bool, bool, bool]:
    lower_type = element_type.lower()
    normalized = _normalize_block_text(text).lower()
    item_mentions = len(re.findall(r"\bitem\s+\d+[a-z]?(?:\.\d+)?\.?", normalized))
    is_table = "table" in lower_type
    is_title = "title" in lower_type
    is_toc = (
        "introductory" in lower_type and item_mentions >= 3
    ) or "table of contents" in normalized[:80]
    return is_toc, is_table, is_title


def _parse_blocks(html: str) -> list[ParserBlock]:
    import sec_parser as sp

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        elements = sp.Edgar10QParser().parse(html or "")

    blocks: list[ParserBlock] = []
    cursor = 0
    for element in elements:
        text = getattr(element, "text", "") or ""
        normalized = _normalize_block_text(text)
        if not normalized:
            continue
        if blocks:
            cursor += 2
        start = cursor
        end = start + len(normalized)
        element_type = type(element).__name__
        is_toc, is_table, is_title = _block_flags(element_type, normalized)
        blocks.append(
            ParserBlock(
                index=len(blocks),
                text=text,
                normalized_text=normalized,
                element_type=element_type,
                start_offset=start,
                end_offset=end,
                is_toc=is_toc,
                is_table=is_table,
                is_title=is_title,
            )
        )
        cursor = end
    return blocks


def _section_pattern(section_name: str) -> re.Pattern[str]:
    item, title = SECTION_HEADING_SPECS.get(section_name, ("", ""))
    item_re = re.escape(item).replace(r"\.", r"\.")
    title_re = re.escape(title).replace(r"\ ", r"\s+")
    if title:
        pattern = rf"(?<![a-z])item\s*{item_re}\.?(?![a-z0-9])[\s\W]{{0,80}}{title_re}"
    elif "." in item:
        pattern = rf"(?<![a-z])item\s*{item_re}(?!\d)"
    else:
        pattern = rf"(?<![a-z])item\s*{item_re}(?![a-z0-9])"
    return re.compile(pattern, re.IGNORECASE)


def _is_toc_like(block: ParserBlock, match_start: int, match_end: int) -> bool:
    text = block.normalized_text
    window = text[match_start : min(len(text), match_end + 180)]
    if block.is_toc:
        return True
    if block.is_table:
        return True
    if re.search(r"\.{3,}", window):
        return True
    if re.search(r"\b\d+\s*(?:item\s+\d|part\s+[ivx])", window, re.I):
        return True
    return False


def _body_word_count(blocks: list[ParserBlock], candidate: HeadingCandidate) -> int:
    words = 0
    for block in blocks[candidate.block_index : candidate.block_index + 5]:
        if block.index == candidate.block_index:
            text = block.normalized_text[
                max(0, candidate.end_offset - block.start_offset) :
            ]
        else:
            text = block.normalized_text
        words += _count_words(text)
        if words >= 50:
            break
    return words


def _score_candidate(
    blocks: list[ParserBlock],
    block: ParserBlock,
    section_name: str,
    match: re.Match[str],
) -> HeadingCandidate:
    score = 0.0
    reasons: list[str] = []
    warnings_out: list[str] = []
    item, title = SECTION_HEADING_SPECS.get(section_name, ("", ""))
    matched = match.group(0).lower()
    start = block.start_offset + match.start()
    end = block.start_offset + match.end()

    if item and re.search(rf"\bitem\s*{re.escape(item)}\.?", matched, re.I):
        score += 40
        reasons.append("item_match")
    if title and title in matched:
        score += 25
        reasons.append("title_match")
    if block.is_title:
        score += 15
        reasons.append("semantic_title")
    prior_context = block.normalized_text[
        max(0, match.start() - 400) : match.start()
    ]
    if block.index > 0:
        prior_context = blocks[block.index - 1].normalized_text[-200:] + " " + prior_context
    section_transition = bool(
        re.search(r"item\s+\d+[a-z]?(?:\.\d+)?\.?", prior_context, re.I)
    )
    if match.start() <= 5:
        score += 15
        reasons.append("block_start")
    elif section_transition:
        score += 25
        reasons.append("section_transition")
    elif not block.is_title:
        score -= 25
        warnings_out.append("inline_reference")

    body_words = _body_word_count(
        blocks,
        HeadingCandidate(
            section_name=section_name,
            block_index=block.index,
            start_offset=start,
            end_offset=end,
            score=0.0,
        ),
    )
    if body_words >= 50:
        score += 10
        reasons.append("substantive_body")

    if _is_toc_like(block, match.start(), match.end()):
        score -= 50
        warnings_out.append("toc_suppressed")
    if block.start_offset < 500 and not block.is_title:
        score -= 15
        warnings_out.append("early_candidate")
    if score < 50:
        warnings_out.append("low_candidate_score")

    return HeadingCandidate(
        section_name=section_name,
        block_index=block.index,
        start_offset=start,
        end_offset=end,
        score=score,
        reasons=reasons,
        warnings=warnings_out,
    )


def _find_candidates(
    blocks: list[ParserBlock],
    section_names: list[str],
) -> list[HeadingCandidate]:
    candidates: list[HeadingCandidate] = []
    for block in blocks:
        for section_name in section_names:
            pattern = _section_pattern(section_name)
            for match in pattern.finditer(block.normalized_text):
                candidates.append(_score_candidate(blocks, block, section_name, match))
    return sorted(candidates, key=lambda c: (c.start_offset, -c.score))


def _select_candidates(candidates: list[HeadingCandidate]) -> list[HeadingCandidate]:
    selected_by_section: dict[str, HeadingCandidate] = {}
    for candidate in candidates:
        if candidate.score < 50:
            continue
        current = selected_by_section.get(candidate.section_name)
        if (
            current is None
            or candidate.score > current.score
            or (
                candidate.score == current.score
                and candidate.start_offset < current.start_offset
            )
        ):
            selected_by_section[candidate.section_name] = candidate
    return sorted(selected_by_section.values(), key=lambda c: c.start_offset)


def _full_text(blocks: list[ParserBlock]) -> str:
    return "\n\n".join(block.normalized_text for block in blocks)


def required_sections_present(form_type: str, extracted: list[ExtractedSection]) -> bool:
    base = form_type.replace("/A", "").replace("-A", "").upper()
    required = REQUIRED_SECTIONS.get(base, REQUIRED_SECTIONS.get("10-K", []))
    found = {s.section_name for s in extracted}
    return all(r in found for r in required)


def extract_sections(document: FilingDocument) -> list[ExtractedSection]:
    from disclosure_alpha.version import PARSER_VERSION

    parser_version = PARSER_VERSION
    section_map = sections_for_form_type(document.form_type)
    try:
        blocks = _parse_blocks(document.html)
    except Exception:
        return []
    if not blocks:
        return []

    candidates = _find_candidates(blocks, list(section_map))
    ordered = _select_candidates(candidates)
    cleaned_full = _full_text(blocks)

    found = {candidate.section_name for candidate in ordered}
    base_form = document.form_type.replace("/A", "").replace("-A", "").upper()
    missing_required = set(REQUIRED_SECTIONS.get(base_form, [])) - found

    results: list[ExtractedSection] = []
    for idx, candidate in enumerate(ordered):
        section_name = candidate.section_name
        start = candidate.start_offset
        end = len(cleaned_full)
        if idx + 1 < len(ordered):
            end = ordered[idx + 1].start_offset
        raw_slice = cleaned_full[start:end].strip()
        cleaned = normalize_whitespace(raw_slice)
        word_count = _count_words(cleaned)
        sentence_count = _count_sentences(cleaned)
        confidence = max(0.4, min(0.95, candidate.score / 100))
        section_warnings = list(dict.fromkeys(candidate.warnings))
        if word_count < 50:
            confidence = min(confidence, 0.35)
            section_warnings.append("short_section")
        if end == len(cleaned_full):
            confidence = min(confidence, 0.75)
            section_warnings.append("open_ended_boundary")
        if missing_required:
            section_warnings.append("missing_required_section")
        results.append(
            ExtractedSection(
                section_name=section_name,
                raw_text=raw_slice,
                cleaned_text=cleaned,
                text_hash=_text_hash(cleaned),
                word_count=word_count,
                sentence_count=sentence_count,
                extraction_confidence=round(confidence, 2),
                extraction_method="sec_parser_sequence_v2",
                parser_version=parser_version,
                start_offset=start,
                end_offset=end,
                warnings=section_warnings,
            )
        )
    return results
