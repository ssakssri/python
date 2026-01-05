"""Simple crawler for the latest Google AI news using Google News RSS."""
from __future__ import annotations

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from typing import List, Optional


@dataclass
class NewsItem:
    """Represents a single news entry from Google News RSS."""

    title: str
    link: str
    published: Optional[str]

    def formatted(self) -> str:
        """Return a human-friendly string for the news item."""
        if self.published:
            return f"{self.title} ({self.published})\n{self.link}"
        return f"{self.title}\n{self.link}"


def build_google_news_rss_url(
    query: str = "google AI", language: str = "en-US", region: str = "US"
) -> str:
    """Construct the Google News RSS URL for a query and locale.

    Parameters
    ----------
    query: str
        Search phrase to use when querying Google News.
    language: str
        BCP 47 language tag for the headline language (e.g., ``"en-US"``).
    region: str
        Region code to influence news location (e.g., ``"US"``).

    Returns
    -------
    str
        Fully constructed RSS feed URL for Google News.
    """

    encoded_query = urllib.parse.quote(query)
    ceid = f"{region}:{language.split('-')[0]}"
    return (
        "https://news.google.com/rss/search?q="
        f"{encoded_query}&hl={language}&gl={region}&ceid={ceid}"
    )


def _fetch_rss_feed(url: str) -> bytes:
    """Retrieve raw RSS XML data from a URL."""
    request = urllib.request.Request(
        url, headers={"User-Agent": "ssakssri-news-crawler/1.0"}
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.read()


def _parse_rss_items(xml_content: bytes, limit: Optional[int] = None) -> List[NewsItem]:
    """Parse RSS XML content into a list of ``NewsItem`` objects."""
    root = ET.fromstring(xml_content)
    channel = root.find("channel")
    if channel is None:
        return []

    items: List[NewsItem] = []
    for item in channel.findall("item"):
        title = item.findtext("title", default="").strip()
        link = item.findtext("link", default="").strip()
        published_text = item.findtext("pubDate")

        published_iso: Optional[str] = None
        if published_text:
            try:
                published_dt = parsedate_to_datetime(published_text)
                published_iso = published_dt.isoformat()
            except (TypeError, ValueError):
                published_iso = None

        items.append(NewsItem(title=title, link=link, published=published_iso))

        if limit is not None and len(items) >= limit:
            break

    return items


def fetch_latest_google_ai_news(
    limit: int = 10, query: str = "google AI", language: str = "en-US", region: str = "US"
) -> List[NewsItem]:
    """Fetch the latest news items about Google AI.

    Parameters
    ----------
    limit: int
        Maximum number of news items to return.
    query: str
        Search phrase to use (defaults to ``"google AI"``).
    language: str
        Language of the headlines.
    region: str
        Region code for Google News.

    Returns
    -------
    List[NewsItem]
        Parsed list of news items.
    """

    url = build_google_news_rss_url(query=query, language=language, region=region)
    rss_xml = _fetch_rss_feed(url)
    return _parse_rss_items(rss_xml, limit=limit)


if __name__ == "__main__":
    news_items = fetch_latest_google_ai_news()
    for idx, item in enumerate(news_items, start=1):
        print(f"{idx}. {item.formatted()}\n")