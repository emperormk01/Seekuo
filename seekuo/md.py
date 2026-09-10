"""HTML-to-Markdown for token optimization.

Strips scripts, styles, nav, and ads, then converts headings, links, lists,
code, and tables to compact Markdown. Pure stdlib (html.parser), no deps.
"""

import re
from html.parser import HTMLParser

SKIP_TAGS = {"script", "style", "nav", "header", "footer", "aside", "noscript"}
SKIP_ATTRS = ("ad", "sidebar", "popup", "modal", "cookie", "banner")


class _MD(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.out: list[str] = []
        self.skip_depth = 0
        self.link: str | None = None
        self.in_pre = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        cls = " ".join(v or "" for k, v in attrs if k in ("class", "id")).lower()
        if any(s in cls for s in SKIP_ATTRS):
            self.skip_depth += 1
            return
        d = dict(attrs)
        if tag in ("h1", "h2", "h3", "h4"):
            self.out.append("\n\n" + "#" * int(tag[1]) + " ")
        elif tag == "p":
            self.out.append("\n\n")
        elif tag == "br":
            self.out.append("\n")
        elif tag in ("li",):
            self.out.append("\n- ")
        elif tag in ("tr",):
            self.out.append("\n| ")
        elif tag in ("td", "th"):
            self.out.append(" | ")
        elif tag == "pre":
            self.in_pre = True
            self.out.append("\n\n```\n")
        elif tag == "code" and not self.in_pre:
            self.out.append("`")
        elif tag == "a":
            self.link = d.get("href", "")
        elif tag == "img":
            alt = d.get("alt", "")
            if alt:
                self.out.append(f"![{alt}]()")

    def handle_endtag(self, tag: str) -> None:
        if self.skip_depth:
            if tag in SKIP_TAGS:
                self.skip_depth -= 1
            return
        if tag == "pre":
            self.in_pre = False
            self.out.append("\n```\n")
        elif tag == "code" and not self.in_pre:
            self.out.append("`")
        elif tag == "a":
            self.link = None

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        if self.in_pre:
            self.out.append(data)
            return
        text = re.sub(r"\s+", " ", data)
        if not text.strip():
            return
        if self.link:
            self.out.append(f"[{text.strip()}]({self.link})")
            self.link = None
        else:
            self.out.append(text)


def html_to_markdown(html: str, max_chars: int = 8000) -> tuple[str, int]:
    """Convert HTML to compact Markdown. Returns (markdown, word_count)."""
    p = _MD()
    p.feed(html)
    md = re.sub(r"\n{3,}", "\n\n", "".join(p.out)).strip()
    if len(md) > max_chars:
        md = md[:max_chars].rsplit(" ", 1)[0] + "..."
    return md, len(md.split())
