"""DuckDuckGo Lite engine. Minimal no-JS endpoint, rarely bot-gated."""

import re
from urllib.parse import unquote

from lxml import html

from .base import Engine, RequestSpec, Result


class DuckDuckGoLite(Engine):
    name = "ddg-lite"
    supports_freshness = True

    def build_request(
        self, query: str, max_results: int = 10, freshness: str = ""
    ) -> RequestSpec:
        params = {"q": query}
        df = _freshness_param(freshness)
        if df:
            params["df"] = df
        return RequestSpec(url="https://lite.duckduckgo.com/lite/", params=params)

    def parse_response(self, text: str) -> list[Result]:
        results: list[Result] = []
        tree = html.fromstring(text)
        anchors = tree.xpath("//a[contains(@class, 'result-link')]")
        snippets = tree.xpath("//td[@class='result-snippet']")
        for i, a in enumerate(anchors):
            href = a.get("href", "")
            title = (a.text_content() or "").strip()
            url = _real_url(href)
            if not title or not url:
                continue
            snippet = ""
            if i < len(snippets):
                snippet = re.sub(
                    r"\s+", " ", (snippets[i].text_content() or "")
                ).strip()
            results.append(
                Result(
                    title=title, url=url, snippet=snippet, engine=self.name
                )
            )
        return results


def _real_url(href: str) -> str | None:
    """Unwrap DDG redirect (`uddg=<pct-encoded>`) to the real URL."""
    m = re.search(r"uddg=([^&]+)", href)
    if not m:
        return None
    url = unquote(m.group(1))
    return url if url.startswith("http") else None


def _freshness_param(freshness: str) -> str:
    return {"day": "d", "week": "w", "month": "m", "year": "y"}.get(
        freshness.lower(), ""
    )
