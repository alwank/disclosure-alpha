import hashlib
import re
import warnings
from dataclasses import dataclass, field, replace

from disclosure_alpha.dictionaries import REQUIRED_SECTIONS, sections_for_form_type
from disclosure_alpha.text_cleaner import clean_html_text, normalize_whitespace

ANALYSIS_MIN_WORDS = 200

_ITEM_1A_END_PATTERNS = [
    re.compile(r"(?i)(?<![a-z])item\s*1b"),
    re.compile(r"(?i)(?<![a-z])item\s*2\.?(?![a-z0-9])"),
    re.compile(r"(?i)(?<![a-z])item\s*2\s"),
]


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


def _finalize_confidence(
    base_conf: float,
    word_count: int,
    section_warnings: list[str],
    *,
    end_is_eof: bool = False,
) -> float:
    conf = max(0.4, min(0.95, base_conf))
    if "short_section" in section_warnings or word_count < 50:
        return round(min(conf, 0.35), 2)
    if end_is_eof:
        conf = min(conf, 0.75)
    if word_count >= 2000:
        conf = max(conf, 0.85)
    elif word_count >= 200:
        conf = max(conf, 0.76)
    return round(conf, 2)


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
    try:
        import sec_parser as sp
    except ImportError:
        return []

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            elements = sp.Edgar10QParser().parse(html or "")
        except Exception:
            return []

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


def _select_candidates_ranked(
    candidates: list[HeadingCandidate],
) -> dict[str, list[HeadingCandidate]]:
    by_section: dict[str, list[HeadingCandidate]] = {}
    for candidate in sorted(candidates, key=lambda c: (-c.score, c.start_offset)):
        if candidate.score < 50:
            continue
        lst = by_section.setdefault(candidate.section_name, [])
        if len(lst) < 2:
            lst.append(candidate)
    return by_section


def _full_text(blocks: list[ParserBlock]) -> str:
    return "\n\n".join(block.normalized_text for block in blocks)


def _find_heading_positions(text: str, section_map: dict[str, str]) -> list[tuple[int, str, str]]:
    positions: list[tuple[int, str, str]] = []
    lower = text.lower()
    for section_name, pattern in section_map.items():
        for match in re.finditer(pattern, lower, flags=re.IGNORECASE):
            positions.append((match.start(), section_name, match.group(0)))
    positions.sort(key=lambda x: x[0])
    return positions


def _fallback_is_toc_like(text: str, start: int, heading: str) -> bool:
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

    all_starts = sorted({pos for pos, _, _ in positions})

    def _words_to_next(pos: int) -> int:
        next_pos = len(text)
        for p in all_starts:
            if p > pos:
                next_pos = p
                break
        return _count_words(text[pos:next_pos])

    viable = [
        (pos, heading)
        for pos, _, heading in candidates
        if not _fallback_is_toc_like(text, pos, heading)
    ]
    if not viable:
        pos, _, heading = candidates[-1]
        viable = [(pos, heading)]

    best_pos, best_heading = max(viable, key=lambda x: _words_to_next(x[0]))
    confidence = 0.9 if len(viable) == 1 else 0.75
    if _fallback_is_toc_like(text, best_pos, best_heading):
        confidence = 0.4
    return best_pos, confidence


def _next_strong_boundary(
    start: int,
    candidates: list[HeadingCandidate],
    current_section: str,
    *,
    min_offset: int,
) -> int | None:
    for c in sorted(candidates, key=lambda x: x.start_offset):
        if c.start_offset <= start or c.start_offset < min_offset:
            continue
        if c.section_name == current_section:
            continue
        if c.score >= 50:
            return c.start_offset
    return None


def _build_extracted_section(
    section_name: str,
    cleaned_full: str,
    start: int,
    end: int,
    *,
    candidate: HeadingCandidate | None,
    base_conf: float,
    parser_version: str,
    method: str,
    extra_warnings: list[str] | None = None,
) -> ExtractedSection:
    raw_slice = cleaned_full[start:end].strip()
    cleaned = normalize_whitespace(raw_slice)
    word_count = _count_words(cleaned)
    sentence_count = _count_sentences(cleaned)
    section_warnings = list(dict.fromkeys((candidate.warnings if candidate else []) + (extra_warnings or [])))
    if word_count < 50:
        section_warnings.append("short_section")
    end_is_eof = end >= len(cleaned_full)
    if end_is_eof:
        section_warnings.append("open_ended_boundary")
    score_conf = max(0.4, min(0.95, candidate.score / 100)) if candidate else base_conf
    confidence = _finalize_confidence(
        score_conf if candidate else base_conf,
        word_count,
        section_warnings,
        end_is_eof=end_is_eof,
    )
    return ExtractedSection(
        section_name=section_name,
        raw_text=raw_slice,
        cleaned_text=cleaned,
        text_hash=_text_hash(cleaned),
        word_count=word_count,
        sentence_count=sentence_count,
        extraction_confidence=confidence,
        extraction_method=method,
        parser_version=parser_version,
        start_offset=start,
        end_offset=end,
        warnings=section_warnings,
    )


def _pick_best_extraction(
    primary: ExtractedSection | None,
    fallback: ExtractedSection | None,
) -> ExtractedSection | None:
    if primary is None:
        return fallback
    if fallback is None:
        return primary
    use_fallback = False
    if primary.word_count < ANALYSIS_MIN_WORDS:
        if fallback.word_count >= ANALYSIS_MIN_WORDS:
            use_fallback = True
        elif fallback.word_count > primary.word_count * 2:
            use_fallback = True
    if not use_fallback:
        return primary
    merged_warnings = list(
        dict.fromkeys(primary.warnings + fallback.warnings + ["merged_from_fallback"])
    )
    return replace(
        fallback,
        extraction_method="heading_boundary_fallback_merged",
        warnings=merged_warnings,
    )


def _extract_sections_fallback(document: FilingDocument, parser_version: str) -> list[ExtractedSection]:
    """Regex heading boundaries when sec_parser is unavailable or yields no blocks."""
    cleaned_full = clean_html_text(document.html)
    if not cleaned_full.strip():
        return []

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
        results.append(
            _build_extracted_section(
                section_name,
                cleaned_full,
                start,
                end,
                candidate=None,
                base_conf=base_conf,
                parser_version=parser_version,
                method="heading_boundary_fallback",
            )
        )
    return results


def _best_item1a_from_clean_html(
    document: FilingDocument, parser_version: str
) -> ExtractedSection | None:
    base_form = document.form_type.replace("/A", "").replace("-A", "").upper()
    if base_form not in ("10-K", "10-Q"):
        return None

    cleaned = clean_html_text(document.html)
    if not cleaned.strip():
        return None

    section_map = sections_for_form_type(document.form_type)
    pattern = section_map.get("item_1a_risk_factors")
    matches: list[re.Match[str]] = []
    if pattern:
        matches.extend(re.finditer(pattern, cleaned, re.I))
    matches.extend(re.finditer(r"(?i)(?:item\s*)?1a\.?[^a-z]{0,60}risk", cleaned))
    if not matches:
        return None

    best: tuple[int, int, int] | None = None
    seen: set[int] = set()
    for match in matches:
        start = match.start()
        if start in seen:
            continue
        seen.add(start)
        end = len(cleaned)
        for end_pat in _ITEM_1A_END_PATTERNS:
            m = end_pat.search(cleaned, match.end())
            if m:
                end = min(end, m.start())
        wc = _count_words(cleaned[start:end])
        if best is None or wc > best[2]:
            best = (start, end, wc)

    if best is None or best[2] < 50:
        return None

    start, end, _ = best
    return _build_extracted_section(
        "item_1a_risk_factors",
        cleaned,
        start,
        end,
        candidate=None,
        base_conf=0.75,
        parser_version=parser_version,
        method="clean_html_best_match",
        extra_warnings=["clean_html_reslice"],
    )


def _extract_item1a_from_clean_html(
    document: FilingDocument, parser_version: str
) -> ExtractedSection | None:
    base_form = document.form_type.replace("/A", "").replace("-A", "").upper()
    if base_form not in ("10-K", "10-Q"):
        return None

    cleaned = clean_html_text(document.html)
    if not cleaned.strip():
        return None

    section_map = sections_for_form_type(document.form_type)
    pattern = section_map.get("item_1a_risk_factors")
    match = re.search(pattern, cleaned, re.I) if pattern else None
    if not match:
        match = re.search(r"(?i)(?:item\s*)?1a\.?[^a-z]{0,60}risk", cleaned)
    if not match:
        return None

    start = match.start()
    end = len(cleaned)
    for end_pat in _ITEM_1A_END_PATTERNS:
        m = end_pat.search(cleaned, match.end())
        if m:
            end = min(end, m.start())

    return _build_extracted_section(
        "item_1a_risk_factors",
        cleaned,
        start,
        end,
        candidate=None,
        base_conf=0.7,
        parser_version=parser_version,
        method="clean_html_last_resort",
        extra_warnings=["last_resort_extraction"],
    )


def _merge_with_fallback(
    primary_results: list[ExtractedSection],
    fallback_results: list[ExtractedSection],
    section_map: dict[str, str],
) -> list[ExtractedSection]:
    primary_by = {s.section_name: s for s in primary_results}
    fallback_by = {s.section_name: s for s in fallback_results}
    merged: list[ExtractedSection] = []
    for name in section_map:
        best = _pick_best_extraction(primary_by.get(name), fallback_by.get(name))
        if best is not None:
            merged.append(best)
    for name, sec in primary_by.items():
        if name not in section_map:
            merged.append(sec)
    merged.sort(key=lambda s: s.start_offset or 0)
    return merged


def _tag_extraction_suspect(results: list[ExtractedSection]) -> list[ExtractedSection]:
    out: list[ExtractedSection] = []
    for sec in results:
        if sec.section_name == "item_1a_risk_factors" and sec.word_count < ANALYSIS_MIN_WORDS:
            warnings = list(dict.fromkeys(sec.warnings + ["extraction_suspect"]))
            out.append(replace(sec, warnings=warnings))
        else:
            out.append(sec)
    return out


def _ensure_item1a(
    document: FilingDocument,
    results: list[ExtractedSection],
    parser_version: str,
) -> list[ExtractedSection]:
    item_name = "item_1a_risk_factors"
    existing = next((s for s in results if s.section_name == item_name), None)
    candidates = [
        _best_item1a_from_clean_html(document, parser_version),
        _extract_item1a_from_clean_html(document, parser_version),
    ]
    best_alt = max(
        (c for c in candidates if c is not None),
        key=lambda s: s.word_count,
        default=None,
    )
    if best_alt is None:
        return results

    if existing is None:
        return sorted(results + [best_alt], key=lambda s: s.start_offset or 0)

    if best_alt.word_count > existing.word_count and (
        best_alt.word_count >= ANALYSIS_MIN_WORDS
        or best_alt.word_count > existing.word_count * 2
    ):
        merged_warnings = list(
            dict.fromkeys(existing.warnings + best_alt.warnings + ["item1a_resliced"])
        )
        replacement = replace(best_alt, warnings=merged_warnings)
        results = [s for s in results if s.section_name != item_name] + [replacement]
        return sorted(results, key=lambda s: s.start_offset or 0)

    return results


def required_sections_present(form_type: str, extracted: list[ExtractedSection]) -> bool:
    base = form_type.replace("/A", "").replace("-A", "").upper()
    required = REQUIRED_SECTIONS.get(base, REQUIRED_SECTIONS.get("10-K", []))
    found = {s.section_name for s in extracted}
    return all(r in found for r in required)


def _extract_from_sec_parser(
    document: FilingDocument,
    parser_version: str,
    blocks: list[ParserBlock],
    section_map: dict[str, str],
) -> list[ExtractedSection]:
    candidates = _find_candidates(blocks, list(section_map))
    ranked = _select_candidates_ranked(candidates)
    ordered = _select_candidates(candidates)
    if not ordered:
        return []

    cleaned_full = _full_text(blocks)
    base_form = document.form_type.replace("/A", "").replace("-A", "").upper()
    missing_required = set(REQUIRED_SECTIONS.get(base_form, [])) - {
        c.section_name for c in ordered
    }
    if missing_required:
        extra_warnings = ["missing_required_section"]
    else:
        extra_warnings = []

    end_by_section = {c.section_name: len(cleaned_full) for c in ordered}
    for idx, candidate in enumerate(ordered):
        if idx + 1 < len(ordered):
            end_by_section[candidate.section_name] = ordered[idx + 1].start_offset

    results: list[ExtractedSection] = []
    for candidate in ordered:
        section_name = candidate.section_name
        start = candidate.start_offset
        end = end_by_section[section_name]

        section = _build_extracted_section(
            section_name,
            cleaned_full,
            start,
            end,
            candidate=candidate,
            base_conf=0.75,
            parser_version=parser_version,
            method="sec_parser_sequence_v2",
            extra_warnings=extra_warnings,
        )

        if section.word_count < 50:
            alt_end = _next_strong_boundary(
                start, candidates, section_name, min_offset=start + 200
            )
            if alt_end is not None and alt_end > end:
                section = _build_extracted_section(
                    section_name,
                    cleaned_full,
                    start,
                    alt_end,
                    candidate=candidate,
                    base_conf=0.75,
                    parser_version=parser_version,
                    method="sec_parser_sequence_v2",
                    extra_warnings=extra_warnings + ["boundary_extended"],
                )

        if section.word_count < ANALYSIS_MIN_WORDS and (
            "short_section" in section.warnings or "early_candidate" in section.warnings
        ):
            alts = ranked.get(section_name, [])
            for alt in alts[1:]:
                alt_end = end_by_section[section_name]
                alt_section = _build_extracted_section(
                    section_name,
                    cleaned_full,
                    alt.start_offset,
                    alt_end,
                    candidate=alt,
                    base_conf=0.75,
                    parser_version=parser_version,
                    method="sec_parser_sequence_v2",
                    extra_warnings=extra_warnings + ["alternate_candidate"],
                )
                if alt_section.word_count > section.word_count:
                    section = alt_section
                    if section.word_count >= 50:
                        break

        results.append(section)

    return results


def extract_sections(document: FilingDocument) -> list[ExtractedSection]:
    from disclosure_alpha.version import PARSER_VERSION

    parser_version = PARSER_VERSION
    section_map = sections_for_form_type(document.form_type)
    blocks = _parse_blocks(document.html)
    fallback = _extract_sections_fallback(document, parser_version)

    if not blocks:
        results = fallback
    else:
        primary = _extract_from_sec_parser(document, parser_version, blocks, section_map)
        if not primary:
            results = fallback
        else:
            results = _merge_with_fallback(primary, fallback, section_map)

    results = _ensure_item1a(document, results, parser_version)
    return _tag_extraction_suspect(results)
