#!/usr/bin/env python3
"""Evaluate section extraction against a gold-set directory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from disclosure_alpha.section_extractor import FilingDocument, extract_sections


def _load_case(case_dir: Path, *, include_unlabeled: bool = False) -> tuple[FilingDocument, set[str]] | None:
    labels_path = case_dir / "labels.json"
    html_files = list(case_dir.glob("*.html")) + list(case_dir.glob("*.htm"))
    if not labels_path.exists() or not html_files:
        return None
    labels = json.loads(labels_path.read_text(encoding="utf-8"))
    if not include_unlabeled and not labels.get("labeled", False):
        return None
    expected = {s["section_name"] for s in labels.get("sections", []) if s.get("section_name")}
    if not expected:
        return None
    meta = labels.get("filing", {})
    doc = FilingDocument(
        cik=meta.get("cik", "0000000000"),
        accession_number=meta.get("accession_number", case_dir.name),
        form_type=meta.get("form_type", "10-K"),
        html=html_files[0].read_text(encoding="utf-8", errors="replace"),
    )
    return doc, expected


def evaluate_gold_set(gold_dir: Path, *, include_unlabeled: bool = False) -> dict:
    cases = sorted(p for p in gold_dir.iterdir() if p.is_dir() and not p.name.startswith("."))
    if not cases:
        return {
            "gold_dir": str(gold_dir),
            "cases_total": 0,
            "cases_evaluated": 0,
            "cases_pending": 0,
            "section_name_accuracy": None,
            "avg_extraction_confidence": None,
            "status": "no_cases",
            "note": "Add case subdirs with labels.json + filing HTML under gold_set/",
        }

    name_hits = 0
    name_total = 0
    confidences: list[float] = []
    per_case: list[dict] = []
    pending = 0

    for case_dir in cases:
        labels_path = case_dir / "labels.json"
        if labels_path.exists():
            labels = json.loads(labels_path.read_text(encoding="utf-8"))
            has_html = bool(list(case_dir.glob("*.html")) + list(case_dir.glob("*.htm")))
            if not labels.get("labeled", False) or not labels.get("sections") or not has_html:
                pending += 1
        loaded = _load_case(case_dir, include_unlabeled=include_unlabeled)
        if loaded is None:
            continue
        doc, expected = loaded
        extracted = extract_sections(doc)
        found = {s.section_name for s in extracted}
        confidences.extend(float(s.extraction_confidence) for s in extracted)
        hits = len(expected & found)
        name_hits += hits
        name_total += len(expected)
        per_case.append(
            {
                "case": case_dir.name,
                "expected_sections": sorted(expected),
                "extracted_sections": sorted(found),
                "section_name_recall": hits / len(expected) if expected else None,
                "missing": sorted(expected - found),
                "extra": sorted(found - expected),
            }
        )

    accuracy = name_hits / name_total if name_total else None
    avg_conf = sum(confidences) / len(confidences) if confidences else None
    return {
        "gold_dir": str(gold_dir),
        "cases_total": len(cases),
        "cases_evaluated": len(per_case),
        "cases_pending": pending,
        "section_name_accuracy": round(accuracy, 4) if accuracy is not None else None,
        "avg_extraction_confidence": round(avg_conf, 4) if avg_conf is not None else None,
        "target_accuracy": 0.95,
        "status": "pass" if accuracy and accuracy >= 0.95 else "pending",
        "cases": per_case,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate section extraction gold set")
    parser.add_argument(
        "--gold-dir",
        default="data/parser_eval/gold_set",
        help="Directory with per-filing case subdirs (labels.json + HTML)",
    )
    parser.add_argument("--output", default="data/validation/reports/parser_eval_report.json")
    parser.add_argument(
        "--include-unlabeled",
        action="store_true",
        help="Evaluate template cases with labeled=false (debug only)",
    )
    args = parser.parse_args()

    report = evaluate_gold_set(Path(args.gold_dir), include_unlabeled=args.include_unlabeled)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
