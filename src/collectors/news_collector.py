"""News collection module using various APIs and RSS feeds."""

from datetime import datetime, timedelta
from typing import List, Optional
from dataclasses import dataclass

import feedparser
import requests
from bs4 import BeautifulSoup

from src.core.config import get_settings
from src.core.logging import get_logger
from src.utils.helpers import is_valid_url, extract_domain

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class NewsArticle:
    """News article data structure."""

    title: str
    content: str
    url: str
    source: str
    published_date: Optional[datetime]
    category: str
    keywords: List[str]


class NewsCollector:
    """Collect news from various sources."""

    def __init__(self) -> None:
        """Initialize news collector."""
        self.api_key = settings.news_api_key
        self.base_url = "https://newsapi.org/v2"

    async def collect_from_newsapi(
        self,
        query: str,
        category: Optional[str] = None,
        max_results: int = 10
    ) -> List[NewsArticle]:
        """Collect news from NewsAPI.

        Args:
            query: Search query
            category: News category
            max_results: Maximum number of results

        Returns:
            List of news articles
        """
        if not self.api_key:
            logger.warning("NewsAPI key not configured")
            return []

        try:
            url = f"{self.base_url}/everything"
            params = {
                "q": query,
                "apiKey": self.api_key,
                "language": "ja",
                "sortBy": "publishedAt",
                "pageSize": max_results,
                "from": (datetime.now() - timedelta(days=2)).isoformat(),
            }

            if category:
                params["category"] = category

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            articles = []
            for item in data.get("articles", []):
                article = NewsArticle(
                    title=item.get("title", ""),
                    content=item.get("description", "") + "\n\n" + item.get("content", ""),
                    url=item.get("url", ""),
                    source=item.get("source", {}).get("name", "Unknown"),
                    published_date=datetime.fromisoformat(
                        item.get("publishedAt", "").replace("Z", "+00:00")
                    ) if item.get("publishedAt") else None,
                    category=category or "general",
                    keywords=[],
                )
                articles.append(article)

            logger.info(f"Collected {len(articles)} articles from NewsAPI for query: {query}")
            return articles

        except Exception as e:
            logger.error(f"Error collecting from NewsAPI: {e}")
            return []

    async def collect_from_rss(self, feed_url: str, category: str) -> List[NewsArticle]:
        """Collect news from RSS feed.

        Args:
            feed_url: RSS feed URL
            category: News category

        Returns:
            List of news articles
        """
        try:
            feed = feedparser.parse(feed_url)
            articles = []

            for entry in feed.entries[:20]:  # Limit to 20 items
                # Extract publish date
                pub_date = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])

                # Extract content
                content = ""
                if hasattr(entry, "summary"):
                    content = entry.summary
                elif hasattr(entry, "description"):
                    content = entry.description

                article = NewsArticle(
                    title=entry.get("title", ""),
                    content=content,
                    url=entry.get("link", ""),
                    source=extract_domain(feed_url) or "RSS",
                    published_date=pub_date,
                    category=category,
                    keywords=[],
                )
                articles.append(article)

            logger.info(f"Collected {len(articles)} articles from RSS: {feed_url}")
            return articles

        except Exception as e:
            logger.error(f"Error collecting from RSS {feed_url}: {e}")
            return []

    async def collect_from_urls(
        self,
        urls: List[str],
        category: str
    ) -> List[NewsArticle]:
        """Collect content from specific URLs via web scraping.

        Args:
            urls: List of URLs to scrape
            category: Content category

        Returns:
            List of news articles
        """
        articles = []

        for url in urls:
            if not is_valid_url(url):
                logger.warning(f"Invalid URL skipped: {url}")
                continue

            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, "html.parser")

                # Extract title
                title = ""
                if soup.find("h1"):
                    title = soup.find("h1").get_text().strip()
                elif soup.find("title"):
                    title = soup.find("title").get_text().strip()

                # Extract main content (simple approach)
                content = ""
                # Try to find article content
                article_tags = soup.find_all(["article", "main", "div"], class_=["article", "content", "post"])
                if article_tags:
                    content = article_tags[0].get_text().strip()
                else:
                    # Fallback to all paragraphs
                    paragraphs = soup.find_all("p")
                    content = "\n\n".join([p.get_text().strip() for p in paragraphs])

                article = NewsArticle(
                    title=title,
                    content=content,
                    url=url,
                    source=extract_domain(url) or "Web",
                    published_date=None,
                    category=category,
                    keywords=[],
                )
                articles.append(article)
                logger.info(f"Scraped content from: {url}")

            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                continue

        return articles

    async def collect_tech_news(self, max_results: int = 20) -> List[NewsArticle]:
        """Collect technology news from multiple sources.

        Args:
            max_results: Maximum results per source

        Returns:
            List of news articles
        """
        all_articles = []

        # NewsAPI
        api_articles = await self.collect_from_newsapi(
            query="AI OR technology OR ガジェット OR テクノロジー",
            category="technology",
            max_results=max_results,
        )
        all_articles.extend(api_articles)

        # Tech RSS feeds
        tech_feeds = [
            ("https://www.techcrunch.com/feed/", "technology"),
            ("https://gigazine.net/news/rss_2.0/", "technology"),
        ]

        for feed_url, category in tech_feeds:
            rss_articles = await self.collect_from_rss(feed_url, category)
            all_articles.extend(rss_articles)

        logger.info(f"Total tech articles collected: {len(all_articles)}")
        return all_articles
