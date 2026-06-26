"""Server-side HTML for OpenBB html widgets."""

from __future__ import annotations

import html
from typing import Any

from disclosure_alpha.openbb.labels import (
    DISCLOSURE_ALPHA_HOME_URL,
    band_label,
    delta_label,
    format_delta_value,
    format_score,
    risk_band,
    section_changes_subtitle,
    tier_color,
)

_BAND_COLORS = {
    "low": "#2563eb",
    "moderate": "#ea580c",
    "elevated": "#dc2626",
    "high": "#991b1b",
    "missing": "#9ca3af",
}


def _esc(value: Any) -> str:
    if value is None:
        return ""
    return html.escape(str(value))


def _comp_row_html(
    *,
    label: str,
    subline: str,
    score: float | None,
    inverted: bool = False,
) -> str:
    band = risk_band(score, inverted=inverted)
    width = 0 if score is None else min(float(score), 100.0)
    subline_html = f'<div class="comp-key">{_esc(subline)}</div>' if subline else ""
    return f"""
        <div class="comp-row">
          <div class="comp-meta">
            <div class="comp-label">{_esc(label)}</div>
            {subline_html}
          </div>
          <div class="comp-bar-wrap"><div class="comp-bar" style="width:{width}%;background:{_BAND_COLORS[band]}"></div></div>
          <div class="comp-score" style="color:{_BAND_COLORS[band]}">{_esc(format_score(score))}</div>
        </div>"""


def render_score_card_html(ctx: dict[str, Any]) -> str:
    filing = ctx.get("filing") or {}
    ticker = _esc(filing.get("ticker", ""))
    fiscal_year = _esc(filing.get("fiscal_year", ""))
    form_type = _esc(filing.get("form_type", "10-K"))
    overall = ctx.get("overall")
    overall_band = risk_band(overall)
    overall_text = format_score(overall)
    hero_sub = band_label(overall_band)

    demo_banner = ""
    if ctx.get("demo"):
        demo_banner = (
            '<div class="demo-banner">DEMO DATA — not live EDGAR. '
            "Scores from committed fixtures.</div>"
        )

    component_rows = ""
    for row in ctx.get("headline_rows") or []:
        component_rows += _comp_row_html(
            label=str(row.get("label") or ""),
            subline=f"{row.get('key')} · {row.get('weight_pct')}%",
            score=row.get("score"),
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Disclosure Risk — {ticker}</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    margin: 0; padding: 16px; background: #f8fafc; color: #0f172a; font-size: 14px; }}
  .demo-banner {{ background: #fef3c7; border: 1px solid #f59e0b; padding: 8px 12px;
    border-radius: 6px; margin-bottom: 12px; font-weight: 600; }}
  .card {{ display: grid; grid-template-columns: 280px 1fr; gap: 20px;
    background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 20px; }}
  .header {{ grid-column: 1 / -1; font-size: 15px; font-weight: 600; color: #334155; }}
  .hero-score {{ font-size: 48px; font-weight: 700; color: {_BAND_COLORS[overall_band]}; line-height: 1; }}
  .hero-sub {{ color: #64748b; margin-top: 8px; font-size: 13px; }}
  .meta-table {{ margin-top: 20px; width: 100%; border-collapse: collapse; }}
  .meta-table td {{ padding: 6px 0; border-bottom: 1px solid #f1f5f9; }}
  .meta-key {{ color: #64748b; }}
  .right h2 {{ font-size: 11px; text-transform: uppercase; letter-spacing: .05em;
    color: #94a3b8; margin: 0 0 12px; }}
  .comp-row {{ display: grid; grid-template-columns: 1fr 120px 48px; gap: 10px;
    align-items: center; margin-bottom: 10px; }}
  .comp-label {{ font-weight: 500; }}
  .comp-key {{ font-size: 11px; color: #94a3b8; }}
  .comp-bar-wrap {{ background: #f1f5f9; height: 8px; border-radius: 4px; overflow: hidden; }}
  .comp-bar {{ height: 100%; border-radius: 4px; }}
  .comp-score {{ text-align: right; font-weight: 600; font-variant-numeric: tabular-nums; }}
  .legend {{ grid-column: 1 / -1; display: flex; flex-wrap: wrap; gap: 12px;
    font-size: 11px; color: #64748b; margin-top: 8px; }}
  .legend span::before {{ content: ''; display: inline-block; width: 10px; height: 10px;
    border-radius: 2px; margin-right: 4px; vertical-align: middle; }}
  .leg-low::before {{ background: {_BAND_COLORS['low']}; }}
  .leg-mod::before {{ background: {_BAND_COLORS['moderate']}; }}
  .leg-elev::before {{ background: {_BAND_COLORS['elevated']}; }}
  .leg-high::before {{ background: {_BAND_COLORS['high']}; }}
  @media (max-width: 720px) {{ .card {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
{demo_banner}
<div class="card">
  <div class="header">{ticker} · FY{fiscal_year} · {form_type}</div>
  <div class="left">
    <div class="hero-score">{_esc(overall_text)}</div>
    <div class="hero-sub">{_esc(hero_sub)}</div>
    <table class="meta-table">
      <tr><td class="meta-key">score_coverage_ratio</td><td>{_esc(ctx.get('score_coverage_ratio'))}</td></tr>
      <tr><td class="meta-key">confidence_score</td><td>{_esc(ctx.get('confidence_score'))}</td></tr>
      <tr><td class="meta-key">components_present</td><td>{_esc(ctx.get('components_present'))}</td></tr>
    </table>
  </div>
  <div class="right">
    <h2>Nine headline-weighted components</h2>
    {component_rows}
  </div>
  <div class="legend">
    <span class="leg-low">0–25 Low</span>
    <span class="leg-mod">26–50 Moderate</span>
    <span class="leg-elev">51–75 Elevated</span>
    <span class="leg-high">76–100 High</span>
  </div>
</div>
</body>
</html>"""


def _section_change_rows_html(changes: list[dict[str, Any]]) -> str:
    if not changes:
        return '<p class="empty">No section changes vs prior filing.</p>'
    rows = ""
    for row in changes:
        delta_name = row.get("top_delta_name")
        delta_value = row.get("top_delta_value")
        subline = ""
        if delta_name:
            arrow = "↑" if (delta_value or 0) > 0 else "↓" if (delta_value or 0) < 0 else "→"
            subline = f"{arrow} {delta_label(delta_name)}  {format_delta_value(delta_value)}"
        rows += _comp_row_html(
            label=str(row.get("section_label") or ""),
            subline=subline,
            score=row.get("change_score"),
        )
    return rows


def _score_card_body_and_styles(score_html: str) -> tuple[str, str]:
    """Split full score-card HTML into embedded styles + body inner HTML."""
    style_start = score_html.find("<style>")
    style_end = score_html.find("</style>")
    styles = ""
    if style_start != -1 and style_end != -1:
        styles = score_html[style_start : style_end + len("</style>")]

    body_start = score_html.find("<body>")
    body_end = score_html.find("</body>")
    if body_start != -1 and body_end != -1:
        body = score_html[body_start + len("<body>") : body_end].strip()
    else:
        body = score_html
    return styles, body


def _flag_more_label(section_count: int) -> str:
    extra = section_count - 1
    if extra == 1:
        return "+1 section"
    return f"+{extra} sections"


def _flag_summary_html(summary: list[dict[str, Any]]) -> str:
    if not summary:
        return ""
    chips = ""
    for row in summary:
        tier = row.get("tier") or "moderate"
        color = tier_color(tier)
        more = ""
        count = int(row.get("section_count") or 0)
        if count > 1:
            more = f'<span class="flag-more">{_esc(_flag_more_label(count))}</span>'
        chips += (
            f'<span class="flag-chip" style="border-color:{color}">'
            f"{_esc(row.get('label'))}{more}</span>"
        )
    return f'<div class="flag-summary">{chips}</div>'


def _flag_section_groups_html(groups: list[dict[str, Any]]) -> str:
    if not groups:
        return ""
    body = ""
    for group in groups:
        pills = ""
        for flag in group.get("flags") or []:
            tier = flag.get("tier") or "moderate"
            color = tier_color(tier)
            pills += (
                f'<span class="flag-pill" style="border-color:{color}">'
                f"{_esc(flag.get('label'))}</span>"
            )
        body += (
            f'<div class="flag-section">'
            f'<div class="flag-section-title">{_esc(group.get("section_label"))}</div>'
            f'<div class="flag-pills">{pills}</div></div>'
        )
    return f'<div class="flag-sections">{body}</div>'


def _active_flags_html(flag_display: dict[str, Any]) -> str:
    summary = flag_display.get("summary") or []
    groups = flag_display.get("section_groups") or []
    hit_count = int(flag_display.get("hit_count") or 0)
    if not summary:
        return '<p class="empty">No active flags in extracted sections.</p>'

    unique_count = len(summary)
    section_count = len(groups)
    stats = (
        f'<p class="flag-stats">{unique_count} unique · {hit_count} hits · '
        f"{section_count} sections</p>"
    )
    return (
        stats
        + _flag_summary_html(summary)
        + _flag_section_groups_html(groups)
    )


def _company_footer_html() -> str:
    url = _esc(DISCLOSURE_ALPHA_HOME_URL)
    return f"""<footer class="company-footer" data-marker="company-footer">
  <span>Powered by <a class="company-footer-brand" href="{url}" target="_blank" rel="noopener noreferrer">Disclosure Alpha</a></span>
</footer>"""


def render_company_html(
    ctx: dict[str, Any],
    flag_display: dict[str, Any],
    changes: list[dict[str, Any]],
) -> str:
    """Combined Company tab: score card + flags + section changes."""
    score_styles, score_body = _score_card_body_and_styles(render_score_card_html(ctx))

    flags_html = _active_flags_html(flag_display)
    change_rows_html = _section_change_rows_html(changes)
    filing = ctx.get("filing") or {}
    changes_sub = section_changes_subtitle(str(filing.get("form_type") or "10-K"))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Disclosure Company — {_esc((ctx.get('filing') or {}).get('ticker', ''))}</title>
{score_styles}
<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    margin: 0; padding: 16px; background: #f8fafc; color: #0f172a; font-size: 14px; }}
  .section {{ margin-top: 20px; background: #fff; border: 1px solid #e2e8f0;
    border-radius: 10px; padding: 16px; }}
  .section h2 {{ font-size: 13px; text-transform: uppercase; letter-spacing: .05em;
    color: #64748b; margin: 0 0 12px; }}
  .section-sub {{ font-size: 12px; color: #94a3b8; margin: -8px 0 12px; }}
  .flag-stats {{ font-size: 12px; color: #64748b; margin: 0 0 12px; }}
  .flag-summary {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }}
  .flag-chip {{ display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px;
    font-size: 12px; font-weight: 500; background: #f8fafc; border: 1px solid #e2e8f0;
    border-left-width: 3px; border-radius: 6px; }}
  .flag-more {{ font-size: 11px; font-weight: 400; color: #64748b; }}
  .flag-sections {{ display: flex; flex-direction: column; gap: 14px; }}
  .flag-section-title {{ font-size: 12px; font-weight: 600; color: #475569; margin-bottom: 8px; }}
  .flag-pills {{ display: flex; flex-wrap: wrap; gap: 6px; }}
  .flag-pill {{ display: inline-block; padding: 3px 10px; font-size: 12px;
    background: #fff; border: 1px solid #e2e8f0; border-left-width: 3px; border-radius: 999px; }}
  p.empty {{ color: #94a3b8; font-style: italic; margin: 0; }}
  .company-panels {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 20px;
    align-items: stretch; }}
  .company-panels .section {{ margin-top: 0; min-width: 0; height: 100%; }}
  @media (max-width: 900px) {{ .company-panels {{ grid-template-columns: 1fr; }} }}
  .company-footer {{ display: flex; flex-wrap: wrap; justify-content: flex-end;
    align-items: center; margin-top: 12px; padding-top: 10px;
    border-top: 1px solid #f1f5f9; font-size: 11px; color: #94a3b8; }}
  .company-footer-brand {{ color: #475569; font-weight: 600; text-decoration: none; }}
  .company-footer-brand:hover {{ color: #2563eb; text-decoration: underline; }}
</style>
</head>
<body>
{score_body}
<div class="company-panels">
<section class="section" id="active-flags" data-marker="active-flags">
  <h2>Active flags</h2>
  <p class="section-sub">Phrase-pattern hits in extracted sections — not confirmed events.</p>
  {flags_html}
</section>
<section class="section" id="section-changes" data-marker="section-changes">
  <h2>Section changes</h2>
  <p class="section-sub">{_esc(changes_sub)}</p>
  {change_rows_html}
</section>
</div>
{_company_footer_html()}
</body>
</html>"""


def render_error_html(status: int, detail: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>Error {status}</title>
<style>body{{font-family:sans-serif;padding:24px;background:#fef2f2;color:#991b1b}}
.panel{{background:#fff;border:1px solid #fecaca;border-radius:8px;padding:16px;max-width:480px}}</style>
</head><body><div class="panel"><h2>Disclosure Alpha — HTTP {status}</h2>
<p>{_esc(detail)}</p></div></body></html>"""
