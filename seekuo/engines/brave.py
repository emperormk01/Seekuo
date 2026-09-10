"""Brave Search engine. Most bot-tolerant full HTML endpoint."""

from lxml import html

from .base import Engine, RequestSpec, Result


class Brave(Engine):
    name = "brave"
    supports_freshness = True

    def build_request(
        self, query: str, max_results: int = 10, freshness: str = ""
    ) -> RequestSpec:
        params = {"q": query, "source": "web"}
        fresh = _freshness_param(freshness)
        if fresh:
            params["freshness"] = fresh
        return RequestSpec(
            url="https://search.brave.com/search",
            params=params,
            headers={"Accept": "text/html,application/xhtml+xml"},
        )

    def parse_response(self, text: str) -> list[Result]:
        results: list[Result] = []
        tree = html.fromstring(text)
        for el in tree.xpath('//div[@data-type="web"]'):
            link = el.xpath('.//a[@href]')
            if not link:
                continue
            href = link[0].get("href", "")
            if not href.startswith("http"):
                continue
            # Clean title: div.title's title attr (anchor text has breadcrumbs).
            title = ""
            tdiv = el.xpath('.//div[contains(@class, "title")]')
            if tdiv:
                title = (tdiv[0].get("title") or tdiv[0].text_content() or "").strip()
            if not title:
                title = (link[0].text_content() or "").strip()
            if not title:
                continue
            snippet = ""
            desc = el.xpath('.//div[contains(@class, "generic-snippet")]')
            if desc:
                snippet = (desc[0].text_content() or "").strip()
            pub = ""
            time_el = el.xpath(".//time")
            if time_el:
                pub = (
                    time_el[0].get("datetime")
                    or time_el[0].text_content()
                    or ""
                ).strip()
            results.append(
                Result(
                    title=title,
                    url=href,
                    snippet=snippet,
                    engine=self.name,
                    published=pub,
                )
            )
        return results


def _freshness_param(freshness: str) -> str:
    return {
        "day": "pd",
        "week": "pw",
        "month": "pm",
        "year": "py",
    }.get(freshness.lower(), "")
