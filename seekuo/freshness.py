"""Freshness controls: today, week, month, year, or custom date ranges.

DDG-lite and Brave accept single-letter / short freshness params natively.
Custom ranges (YYYY-MM-DD..YYYY-MM-DD) are applied as a post-filter on the
`published` field when the engine returns dates, and passed through to
engines that support them.
"""

import re
from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class Freshness:
    preset: str = ""  # day | week | month | year | ""
    since: str = ""  # YYYY-MM-DD
    until: str = ""  # YYYY-MM-DD

    @classmethod
    def parse(cls, spec: str) -> "Freshness":
        """Parse 'today|day|week|month|year' or 'YYYY-MM-DD..YYYY-MM-DD'."""
        s = (spec or "").strip().lower()
        if s in ("today", "day", "week", "month", "year"):
            preset = "day" if s == "today" else s
            return cls(preset=preset)
        m = re.fullmatch(
            r"(\d{4}-\d{2}-\d{2})\.\.(\d{4}-\d{2}-\d{2})", s
        )
        if m:
            return cls(since=m.group(1), until=m.group(2))
        if s in ("", "any", "all"):
            return cls()
        raise ValueError(
            f"Bad freshness {spec!r}: use today|week|month|year or YYYY-MM-DD..YYYY-MM-DD"
        )

    def engine_param(self) -> str:
        """Preset string engines understand ('day'|'week'|'month'|'year'|'')."""
        return self.preset

    def matches(self, published: str) -> bool:
        """Post-filter a result's published date against a custom range."""
        if not self.since:
            return True
        day = _coerce_date(published)
        if day is None:
            return True  # keep undated results, don't nuke recall
        return self.since <= day <= (self.until or "9999-12-31")


def _coerce_date(published: str) -> str | None:
    """Best-effort ' -> YYYY-MM-DD' for common engine date formats."""
    s = (published or "").strip()
    for fmt in ("%Y-%m-%d", "%b %d, %Y", "%d %b %Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    m = re.search(r"(\d{4}-\d{2}-\d{2})", s)
    if m:
        return m.group(1)
    m = re.search(r"(\d+)\s+(day|week|month|year)s?\s+ago", s.lower())
    if m:
        from datetime import timedelta

        n = int(m.group(1))
        unit = m.group(2)
        days = {"day": 1, "week": 7, "month": 30, "year": 365}[unit] * n
        return (date.today() - timedelta(days=days)).isoformat()
    return None
