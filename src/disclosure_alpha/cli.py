#!/usr/bin/env python3
"""CLI for deterministic SEC filing analytics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from disclosure_alpha.pipeline import (
    compute_section_metrics,
    extract_sections_from_html,
    score_deterministic,
    score_filing_html,
)


def _load_html(path: str | None) -> str:
    if path and path != "-":
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    return sys.stdin.read()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Disclosure Alpha — deterministic SEC filing analytics"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    extract_p = sub.add_parser("extract", help="Extract sections from filing HTML")
    extract_p.add_argument("--html", required=True, help="Path to HTML file or '-' for stdin")
    extract_p.add_argument("--form", required=True, help="Form type, e.g. 10-K")

    score_p = sub.add_parser("score", help="Full pipeline: HTML → deterministic scores")
    score_p.add_argument("--html", required=True)
    score_p.add_argument("--form", required=True)
    score_p.add_argument("--prior-html", help="Optional prior filing HTML for diffs")

    metrics_p = sub.add_parser("metrics", help="Extract + compute section metrics")
    metrics_p.add_argument("--html", required=True)
    metrics_p.add_argument("--form", required=True)
    metrics_p.add_argument("--prior-html")

    args = parser.parse_args()

    if args.command == "extract":
        html = _load_html(args.html)
        sections = extract_sections_from_html(html, args.form)
        out = [
            {
                "section_name": s.section_name,
                "word_count": s.word_count,
                "extraction_confidence": s.extraction_confidence,
                "parser_version": s.parser_version,
            }
            for s in sections
        ]
        print(json.dumps(out, indent=2))
        return

    if args.command == "metrics":
        html = _load_html(args.html)
        sections = extract_sections_from_html(html, args.form)
        prior_sections = None
        if args.prior_html:
            prior_html = _load_html(args.prior_html)
            prior_sections = extract_sections_from_html(prior_html, args.form)
        metrics = compute_section_metrics(sections, prior_sections)
        print(json.dumps(metrics.__dict__, indent=2, default=str))
        return

    if args.command == "score":
        html = _load_html(args.html)
        prior_html = _load_html(args.prior_html) if args.prior_html else None
        result = score_filing_html(html, args.form, prior_html=prior_html)
        print(json.dumps(result.to_dict(), indent=2, default=str))
        return


if __name__ == "__main__":
    main()
