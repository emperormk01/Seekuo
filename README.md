# Seekuo

Agent-friendly web search toolbox. No API keys, no rate limits, no monthly fees.

- **Chrome-trick fetching**: every request goes out behind rotating Chrome TLS fingerprints (`curl_cffi`), so engines see a browser, not a script.
- **HTML to Markdown**: result pages convert to compact Markdown for token optimization.
- **Freshness controls**: `today | week | month | year` or custom `YYYY-MM-DD..YYYY-MM-DD` ranges.
- **Agent mode**: structured JSON built for LLM consumption (title, url, source, published, snippet, content, content_type, word_count, retrieved_at, confidence).

## Install

```bash
pip install git+https://github.com/emperormk01/Seekuo.git
# or
git clone https://github.com/emperormk01/Seekuo.git && cd Seekuo && pip install -e .
```

## Use

```bash
# Basic agent JSON (Brave + DDG-lite in parallel)
seekuo "rust async tutorial" --engines brave,ddg-lite -n 5

# Freshness: past week only
seekuo "kimi k3 benchmark" --freshness week

# Custom date range
seekuo "naira to dollar" --freshness 2026-08-01..2026-09-10

# Full content as Markdown (slower, more tokens)
seekuo "edge0 8b moore" --fetch-content --content-chars 4000

# Markdown output instead of JSON
seekuo "best mechanical keyboards" --md
```

## Agent-mode JSON

```json
{
  "query": "rust async tutorial",
  "results": [
    {
      "title": "Introduction - Asynchronous Programming in Rust",
      "url": "https://rust-lang.github.io/async-book/",
      "source": "rust-lang.github.io",
      "published": "",
      "snippet": "In particular, async programming in Rust...",
      "content": "",
      "content_type": "article",
      "word_count": 12,
      "retrieved_at": "2026-09-10T10:00:00+00:00",
      "confidence": 0.8
    }
  ]
}
```

`content` fills only with `--fetch-content` (page fetched, converted to Markdown, capped by `--content-chars`). Without it you get titles, snippets, and URLs at minimal token cost.

## Python API

```python
import asyncio
from seekuo import agent_search

data = asyncio.run(agent_search(
    "rust async tutorial",
    engines=["brave", "ddg-lite"],
    max_results=5,
    freshness="week",
    fetch_content=True,
))
```

## Why two engines

Search engines serve bot-tier empty pages to datacenter IPs. Google returns a JS shell, classic DDG/Yahoo/Startpage return shells with zero results. Brave's HTML endpoint and DDG's Lite endpoint still serve real markup, so Seekuo races both and dedupes. Engines that die return nothing; the merge never fails because one engine failed.

## License

MIT. Emperor M.K.
