from __future__ import annotations

from typing import Any

from disclosure_alpha.dictionaries import sections_for_form_type
from disclosure_alpha.section_extractor import ExtractedSection
from disclosure_alpha.validation.scoring_version import normalize_scoring_version

_MATRIX_FIELD_MAP = {
    "overall": "overall_disclosure_risk_score",
    "components": "components",
    "coverage": "score_coverage_ratio",
    "confidence": "confidence_score",
    "missing": "missing_components",
    "aggregates": "aggregates",
    "provenance": "provenance",
}


def parse_sections_param(
    sections: str | None, *, form_type: str
) -> set[str] | None:
    if sections is None or not sections.strip():
        return None
    known = set(sections_for_form_type(form_type))
    names = {s.strip() for s in sections.split(",") if s.strip()}
    unknown = names - known
    if unknown:
        raise ValueError(
            f"Unknown section(s): {', '.join(sorted(unknown))}. "
            f"Valid: {', '.join(sorted(known))}"
        )
    return names


def parse_scoring_model_version(version: str) -> str:
    return normalize_scoring_version(version)


def parse_compare_param(compare: str) -> bool:
    if compare == "prior":
        return True
    if compare == "none":
        return False
    raise ValueError("compare must be 'prior' or 'none'")


def parse_include_param(include: str | None) -> set[str]:
    if include is None:
        return {"metrics", "provenance"}
    if not include.strip():
        return set()
    valid = {"metrics", "provenance"}
    parts = {p.strip() for p in include.split(",") if p.strip()}
    unknown = parts - valid
    if unknown:
        raise ValueError(
            f"Unknown include value(s): {', '.join(sorted(unknown))}. "
            f"Valid: metrics, provenance"
        )
    return parts


def parse_fields_param(fields: str | None) -> set[str] | None:
    if fields is None or not fields.strip():
        return None
    names = {f.strip() for f in fields.split(",") if f.strip()}
    unknown = names - set(_MATRIX_FIELD_MAP)
    if unknown:
        raise ValueError(
            f"Unknown field(s): {', '.join(sorted(unknown))}. "
            f"Valid: {', '.join(sorted(_MATRIX_FIELD_MAP))}"
        )
    return names


def section_summaries(
    sections: list[ExtractedSection], *, include_text: bool
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for section in sections:
        item: dict[str, Any] = {
            "section_name": section.section_name,
            "word_count": section.word_count,
            "extraction_confidence": section.extraction_confidence,
            "parser_version": section.parser_version,
            "warnings": list(section.warnings),
        }
        if include_text:
            item["cleaned_text"] = section.cleaned_text
        out.append(item)
    return out


def shape_matrix_scores(
    scores_dict: dict[str, Any],
    *,
    include_provenance: bool,
    fields: set[str] | None,
) -> dict[str, Any]:
    shaped = dict(scores_dict)
    if not include_provenance:
        shaped.pop("provenance", None)
    if fields is None:
        return shaped
    result: dict[str, Any] = {}
    for api_field in fields:
        score_key = _MATRIX_FIELD_MAP[api_field]
        if score_key in shaped:
            result[score_key] = shaped[score_key]
    return result
