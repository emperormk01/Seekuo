"""Search engine adapters. Each engine: build request -> parse HTML."""

from dataclasses import dataclass, field


@dataclass
class Result:
    title: str
    url: str
    snippet: str
    engine: str
    published: str = ""

    def as_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "engine": self.engine,
            "published": self.published,
        }


@dataclass
class RequestSpec:
    url: str
    method: str = "GET"
    params: dict = field(default_factory=dict)
    data: dict = field(default_factory=dict)
    headers: dict = field(default_factory=dict)
    cookies: dict = field(default_factory=dict)


class Engine:
    name: str = ""
    supports_freshness: bool = False

    def build_request(
        self, query: str, max_results: int = 10, freshness: str = ""
    ) -> RequestSpec | list[RequestSpec]:
        raise NotImplementedError

    def parse_response(self, text: str) -> list[Result]:
        raise NotImplementedError
