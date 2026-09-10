"""Seekuo unit tests (no network)."""

from seekuo.agent import _confidence, _structure
from seekuo.freshness import Freshness
from seekuo.md import html_to_markdown


def test_freshness_presets():
    assert Freshness.parse("today").preset == "day"
    assert Freshness.parse("week").preset == "week"
    assert Freshness.parse("").preset == ""
    f = Freshness.parse("2026-08-01..2026-09-10")
    assert (f.since, f.until) == ("2026-08-01", "2026-09-10")
    assert f.matches("2026-08-15")
    assert not f.matches("2026-10-01")
    assert f.matches("")  # undated results survive


def test_md_strips_and_converts():
    html = """
    <html><head><style>.x{color:red}</style></head>
    <body><nav>menu</nav><h1>Title</h1>
    <p>Hello <a href="https://x.com/">world</a></p>
    <ul><li>one</li><li>two</li></ul>
    <script>alert(1)</script></body></html>
    """
    md, words = html_to_markdown(html)
    assert "# Title" in md
    assert "[world](https://x.com/)" in md
    assert "- one" in md
    assert "alert" not in md and "menu" not in md
    assert words > 5


def test_agent_structure_shape():
    r = {
        "title": "T",
        "url": "https://example.com/a",
        "snippet": "some words here",
        "engine": "brave",
        "published": "2026-09-01",
    }
    out = _structure(r, "2026-09-10T00:00:00+00:00")
    assert out["source"] == "example.com"
    assert out["content"] == ""
    assert out["content_type"] == "article"
    assert out["word_count"] == 3
    assert 0.5 <= out["confidence"] <= 0.99
    assert _confidence({"url": "http://x", "snippet": ""}) < out["confidence"]
