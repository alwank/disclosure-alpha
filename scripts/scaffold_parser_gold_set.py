#!/usr/bin/env python3
"""Scaffold parser gold-set cases from cached SEC HTML (seed labels from extractor)."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from disclosure_alpha.section_extractor import FilingDocument, extract_sections

CACHE_DIR = Path("data/cache/sec_filings")
GOLD_DIR = Path("data/parser_eval/gold_set")


def _form_from_path(html_path: Path) -> str:
    # ponytail: assume 10-K for cached annual filings; refine when cache has form metadata
    return "10-K"


def scaffold_from_cache(*, limit: int = 10, gold_dir: Path = GOLD_DIR) -> int:
    gold_dir.mkdir(parents=True, exist_ok=True)
    html_files = sorted(CACHE_DIR.glob("*/*.html"))[:limit]
    created = 0
    for html_path in html_files:
        accession = html_path.stem
        cik = html_path.parent.name
        case_dir = gold_dir / accession
        case_dir.mkdir(parents=True, exist_ok=True)
        dest_html = case_dir / f"{accession}.html"
        if not dest_html.exists():
            shutil.copy2(html_path, dest_html)
        form_type = _form_from_path(html_path)
        doc = FilingDocument(
            cik=cik,
            accession_number=accession,
            form_type=form_type,
            html=dest_html.read_text(encoding="utf-8", errors="replace"),
        )
        extracted = extract_sections(doc)
        labels = {
            "filing": {
                "cik": cik,
                "accession_number": accession,
                "form_type": form_type,
            },
            "sections": [{"section_name": s.section_name} for s in extracted],
            "note": "Auto-seeded from extract_sections; human review required for production gate.",
        }
        (case_dir / "labels.json").write_text(json.dumps(labels, indent=2), encoding="utf-8")
        created += 1
    return created


def scaffold_templates(*, count: int, gold_dir: Path = GOLD_DIR) -> int:
    """Placeholder case dirs with labels template only (no HTML)."""
    gold_dir.mkdir(parents=True, exist_ok=True)
    start = len(list(gold_dir.iterdir()))
    created = 0
    for i in range(count):
        name = f"template_{start + i + 1:03d}"
        case_dir = gold_dir / name
        case_dir.mkdir(parents=True, exist_ok=True)
        labels_path = case_dir / "labels.json"
        if labels_path.exists():
            continue
        labels_path.write_text(
            json.dumps(
                {
                    "filing": {
                        "cik": "0000000000",
                        "accession_number": name,
                        "form_type": "10-K",
                    },
                    "sections": [
                        {"section_name": "item_1a_risk_factors"},
                        {"section_name": "item_7_mdna"},
                    ],
                    "note": "Add filing HTML and verify section names before eval.",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        created += 1
    return created


def main() -> None:
    parser = argparse.ArgumentParser(description="Scaffold parser gold set from SEC cache")
    parser.add_argument("--seed-from-cache", type=int, default=10)
    parser.add_argument("--template-count", type=int, default=20)
    parser.add_argument("--gold-dir", default=str(GOLD_DIR))
    args = parser.parse_args()
    gold = Path(args.gold_dir)
    seeded = scaffold_from_cache(limit=args.seed_from_cache, gold_dir=gold)
    templated = scaffold_templates(count=args.template_count, gold_dir=gold)
    print(f"Seeded {seeded} cases from cache, added {templated} template cases under {gold}")


if __name__ == "__main__":
    main()
