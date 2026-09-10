"""Seekuo CLI: agent-friendly search from the terminal.

  seekuo "rust async tutorial" --engines brave,ddg-lite -n 5
  seekuo "kimi k3 benchmark" --freshness week --fetch-content
  seekuo "naira to dollar" --freshness 2026-08-01..2026-09-10 --json
"""

import argparse
import asyncio
import json
import sys

from .agent import agent_search
from .engines import ALL_ENGINES


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="seekuo", description="Agent-friendly web search. No API keys."
    )
    p.add_argument("query", help="Search query")
    p.add_argument(
        "-e",
        "--engines",
        default="brave,ddg-lite",
        help=f"Comma-separated engines (default: brave,ddg-lite). Available: {','.join(sorted(ALL_ENGINES))}",
    )
    p.add_argument(
        "-n", "--max-results", type=int, default=5, help="Max results (default: 5)"
    )
    p.add_argument(
        "-f",
        "--freshness",
        default="",
        help="today|week|month|year or YYYY-MM-DD..YYYY-MM-DD (default: any)",
    )
    p.add_argument(
        "--fetch-content",
        action="store_true",
        help="Fetch each result and return Markdown content (slower, more tokens)",
    )
    p.add_argument(
        "--content-chars",
        type=int,
        default=4000,
        help="Max Markdown chars per result with --fetch-content (default: 4000)",
    )
    p.add_argument(
        "--timeout", type=int, default=12, help="Per-request timeout secs (default: 12)"
    )
    p.add_argument(
        "--md",
        action="store_true",
        help="Render results as Markdown instead of JSON",
    )
    return p


def render_md(data: dict) -> str:
    lines = [f"# {data['query']}", ""]
    for i, r in enumerate(data["results"], 1):
        lines.append(f"## {i}. [{r['title']}]({r['url']})")
        lines.append(f"*{r['source']}*")
        if r["snippet"]:
            lines.append(f"\n{r['snippet']}\n")
        if r["content"]:
            lines.append(r["content"])
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    engines = [e.strip() for e in args.engines.split(",") if e.strip()]
    try:
        data = asyncio.run(
            agent_search(
                args.query,
                engines=engines,
                max_results=args.max_results,
                freshness=args.freshness,
                fetch_content=args.fetch_content,
                content_chars=args.content_chars,
                timeout=args.timeout,
            )
        )
    except ValueError as e:
        print(f"seekuo: error: {e}", file=sys.stderr)
        return 2
    if args.md:
        sys.stdout.write(render_md(data))
    else:
        json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
