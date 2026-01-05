"""Utility library for data conversion and news retrieval."""

from .news_crawler import fetch_latest_google_ai_news, NewsItem

__all__ = ["fetch_latest_google_ai_news", "NewsItem"]