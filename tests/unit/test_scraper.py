from __future__ import annotations

from monitor.scraper import _is_post_link, _parse

_SAMPLE_HTML = """
<html><body>
  <a href="/news/claude-3-5">Claude 3.5 is here</a>
  <a href="/research/scaling-laws">Scaling Laws Paper</a>
  <a href="/about">About Us</a>
  <a href="">Empty href</a>
  <a href="/news/claude-3-5">Claude 3.5 is here</a>
</body></html>
"""


def test_parse_extracts_post_links():
    from datetime import datetime, timezone
    posts = _parse(_SAMPLE_HTML, "https://www.anthropic.com/news", "Anthropic News")
    urls = [p.url for p in posts]
    assert "https://www.anthropic.com/news/claude-3-5" in urls
    assert "https://www.anthropic.com/research/scaling-laws" in urls


def test_parse_excludes_non_post_links():
    posts = _parse(_SAMPLE_HTML, "https://www.anthropic.com/news", "Anthropic News")
    urls = [p.url for p in posts]
    assert not any("about" in u for u in urls)


def test_parse_deduplicates():
    posts = _parse(_SAMPLE_HTML, "https://www.anthropic.com/news", "Anthropic News")
    urls = [p.url for p in posts]
    assert len(urls) == len(set(urls))


def test_is_post_link_valid():
    assert _is_post_link("/news/some-article", "") is True
    assert _is_post_link("/research/paper", "") is True


def test_is_post_link_invalid():
    assert _is_post_link("/about", "") is False
    assert _is_post_link("", "") is False
