"""Agent mode: parallel search plus structured JSON results.

Output shape per result:
{
  "title": ..., "url": ..., "source": ..., "published": ...,
  "snippet": ..., "content": ..., "content_type": ...,
  "word_count": ..., "retrieved_at": ..., "confidence": ...
}
"""

import asyncio
import random
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

from curl_cffi.requests import AsyncSession

from .client import fetch
from .engines import ALL_ENGINES
from .engines.base import Engine
from .freshness import Freshness
from .md import html_to_markdown

# Retry schedule (seconds) before an engine is declared dead for a query.
# Total wait capped at ~7s: 1.0 + 2.5 sleeps plus up to 1.5s jitter each.
RETRY_BACKOFF = (1.0, 2.5)
RETRY_JITTER = 1.5

# Cooldown: an engine that fully fails this many queries in a row sits out
# for COOLDOWN_SECS instead of burning retry budget every time.
COOLDOWN_FAILS = 2
COOLDOWN_SECS = 60.0
_COOLDOWN_UNTIL: dict[str, float] = {}
_CONSEC_FAILS: dict[str, int] = {}


async def agent_search(
    query: str,
    *,
    engines: list[str] | None = None,
    max_results: int = 5,
    freshness: str = "",
    fetch_content: bool = False,
    content_chars: int = 4000,
    timeout: int = 12,
) -> dict:
    """Run agent-mode search. Returns {"query", "results": [...]}."""
    fresh = Freshness.parse(freshness)
    names = engines or ["brave", "ddg-lite"]
    selected = [ALL_ENGINES[n] for n in names if n in ALL_ENGINES]
    if not selected:
        raise ValueError(f"Unknown engines: {names}")

    async def run_one(e: Engine) -> tuple[str, list[dict]]:
        # Cooldown: a repeatedly throttled engine sits this query out.
        if time.time() < _COOLDOWN_UNTIL.get(e.name, 0):
            return e.name, []
        # Fresh session per engine: DDG-lite serves degraded bot-check shells
        # on reused connections, so sharing one session poisons results.
        async with AsyncSession() as session:
            return await _run_engine(
                e, query, max_results * 2, fresh.engine_param(), timeout, session
            )

    grouped = await asyncio.gather(*(run_one(e) for e in selected))

    seen: set[str] = set()
    results: list[dict] = []
    for engine_name, items in grouped:
        for item in items:
            if item["url"] in seen:
                continue
            seen.add(item["url"])
            if not fresh.matches(item.get("published", "")):
                continue
            results.append(item)
            if len(results) >= max_results:
                break
        if len(results) >= max_results:
            break

    if fetch_content:
        await _attach_content(results, content_chars, timeout)

    return {"query": query, "results": results[:max_results]}


async def _run_engine(
    engine: Engine,
    query: str,
    limit: int,
    freshness: str,
    timeout: int,
    session: AsyncSession,
) -> tuple[str, list[dict]]:
    now = datetime.now(timezone.utc).isoformat()
    for attempt in range(len(RETRY_BACKOFF) + 1):
        try:
            spec = engine.build_request(query, limit, freshness)
            specs = spec if isinstance(spec, list) else [spec]
            s = specs[-1]
            text = await fetch(
                s.url,
                method=s.method,
                params=s.params or None,
                data=s.data or None,
                headers=s.headers or None,
                cookies=s.cookies or None,
                timeout=timeout,
                session=session,
            )
            parsed = engine.parse_response(text)[:limit]
            if parsed:
                _CONSEC_FAILS[engine.name] = 0
                return engine.name, [_structure(r.as_dict(), now) for r in parsed]
        except Exception:
            pass
        if attempt < len(RETRY_BACKOFF):
            await asyncio.sleep(RETRY_BACKOFF[attempt] + random.uniform(0, RETRY_JITTER))
    # Fully failed: count toward cooldown so throttled engines sit out.
    _CONSEC_FAILS[engine.name] = _CONSEC_FAILS.get(engine.name, 0) + 1
    if _CONSEC_FAILS[engine.name] >= COOLDOWN_FAILS:
        _COOLDOWN_UNTIL[engine.name] = time.time() + COOLDOWN_SECS
    return engine.name, []


def _structure(r: dict, now: str) -> dict:
    host = urlparse(r["url"]).netloc.replace("www.", "")
    snippet = r.get("snippet", "")
    return {
        "title": r["title"],
        "url": r["url"],
        "source": host,
        "published": r.get("published", ""),
        "snippet": snippet,
        "content": "",
        "content_type": "article",
        "word_count": len(snippet.split()),
        "retrieved_at": now,
        "confidence": _confidence(r),
    }


def _confidence(r: dict) -> float:
    score = 0.5
    if r.get("snippet"):
        score += 0.2
    if r["url"].startswith("https"):
        score += 0.1
    if r.get("published"):
        score += 0.1
    return round(min(score, 0.99), 2)


async def _attach_content(
    results: list[dict], max_chars: int, timeout: int
) -> None:
    """Fetch each URL and fill content/content_type/word_count as Markdown."""

    async def one(item: dict) -> None:
        try:
            html = await fetch(item["url"], timeout=timeout)
            md, words = html_to_markdown(html, max_chars)
            item["content"] = md
            item["word_count"] = words
            item["content_type"] = "article" if words > 50 else "page"
        except Exception:
            item["content"] = ""
            item["content_type"] = "unreachable"

    await asyncio.gather(*(one(r) for r in results))
