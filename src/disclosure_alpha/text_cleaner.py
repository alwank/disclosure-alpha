import html
import re
import warnings

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


def clean_html_text(raw_html: str) -> str:
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "lxml")
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
