import html
import re

from bs4 import BeautifulSoup


def _html_soup(raw_html: str) -> BeautifulSoup:
    """SEC inline XBRL 10-Ks are XML/XHTML; use xml parser to avoid lxml HTML warnings."""
    stripped = raw_html.lstrip()
    if stripped.startswith("<?xml") or stripped.lower().startswith("<xml"):
        return BeautifulSoup(raw_html, "lxml-xml")
    return BeautifulSoup(raw_html, "lxml")


def clean_html_text(raw_html: str) -> str:
    if not raw_html:
        return ""
    soup = _html_soup(raw_html)
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text("\n")
    text = html.unescape(text)
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    # ponytail: naive header/footer dedupe by dropping very short repeated lines
    seen: set[str] = set()
    cleaned: list[str] = []
    for line in lines:
        if len(line) < 40 and line in seen:
            continue
        seen.add(line)
        cleaned.append(line)
    return "\n\n".join(cleaned)


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
