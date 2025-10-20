"""Trend analysis and content selection AI."""

from datetime import datetime, timedelta
from typing import List, Optional
from dataclasses import dataclass

from pytrends.request import TrendReq

from src.core.config import get_settings
from src.core.logging import get_logger
from src.collectors.news_collector import NewsArticle

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class TrendScore:
    """Trend score data structure."""

    topic: str
    score: float
    search_volume: float
    recency: float
    engagement: float
    relevance: float
    competition: float
    trending_keywords: List[str]


class TrendAnalyzer:
    """Analyze trends and select content for video generation."""

    def __init__(self) -> None:
        """Initialize trend analyzer."""
        self.pytrends = TrendReq(hl="ja-JP", tz=540)  # Japan timezone
        self.min_score = settings.min_trend_score

    async def get_google_trends(
        self,
        keywords: List[str],
        timeframe: str = "now 7-d",
    ) -> dict:
        """Get Google Trends data for keywords.

        Args:
            keywords: List of keywords to analyze
            timeframe: Timeframe for trends (e.g., "now 7-d", "today 3-m")

        Returns:
            Dictionary with trend data
        """
        try:
            # Build payload
            self.pytrends.build_payload(
                keywords,
                cat=0,
                timeframe=timeframe,
                geo="JP",
                gprop="",
            )

            # Get interest over time
            interest_over_time = self.pytrends.interest_over_time()

            if interest_over_time.empty:
                logger.warning(f"No trend data found for keywords: {keywords}")
                return {}

            # Calculate average interest
            trends = {}
            for keyword in keywords:
                if keyword in interest_over_time.columns:
                    avg_interest = interest_over_time[keyword].mean()
                    max_interest = interest_over_time[keyword].max()
                    trends[keyword] = {
                        "average": float(avg_interest),
                        "max": float(max_interest),
                        "current": float(interest_over_time[keyword].iloc[-1]),
                    }

            logger.info(f"Retrieved trends for {len(trends)} keywords")
            return trends

        except Exception as e:
            logger.error(f"Error getting Google Trends: {e}")
            return {}

    async def get_related_queries(self, keyword: str) -> List[str]:
        """Get related queries from Google Trends.

        Args:
            keyword: Keyword to analyze

        Returns:
            List of related queries
        """
        try:
            self.pytrends.build_payload([keyword], cat=0, timeframe="now 7-d", geo="JP")
            related = self.pytrends.related_queries()

            queries = []
            if keyword in related and related[keyword]["top"] is not None:
                top_queries = related[keyword]["top"]
                queries = top_queries["query"].tolist()[:10]

            logger.info(f"Found {len(queries)} related queries for '{keyword}'")
            return queries

        except Exception as e:
            logger.error(f"Error getting related queries: {e}")
            return []

    def calculate_recency_score(self, published_date: Optional[datetime]) -> float:
        """Calculate recency score based on publish date.

        Args:
            published_date: Article publish date

        Returns:
            Recency score (0.0 to 1.0)
        """
        if not published_date:
            return 0.5

        now = datetime.utcnow()
        age_hours = (now - published_date).total_seconds() / 3600

        # Score decreases with age
        # 0-6 hours: 1.0
        # 6-24 hours: 0.8
        # 24-48 hours: 0.5
        # 48+ hours: 0.2

        if age_hours < 6:
            return 1.0
        elif age_hours < 24:
            return 0.8
        elif age_hours < 48:
            return 0.5
        else:
            return 0.2

    def calculate_engagement_score(
        self,
        article: NewsArticle,
        trend_data: dict,
    ) -> float:
        """Calculate engagement score.

        Args:
            article: News article
            trend_data: Google Trends data

        Returns:
            Engagement score (0.0 to 1.0)
        """
        # Simple heuristic based on content length and keywords
        content_length = len(article.content)
        length_score = min(content_length / 1000, 1.0)

        # Check if keywords are trending
        keyword_score = 0.0
        if article.keywords and trend_data:
            trending_keywords = [
                kw for kw in article.keywords
                if kw in trend_data and trend_data[kw].get("current", 0) > 50
            ]
            keyword_score = len(trending_keywords) / max(len(article.keywords), 1)

        return (length_score * 0.5 + keyword_score * 0.5)

    def calculate_relevance_score(
        self,
        article: NewsArticle,
        category: str,
    ) -> float:
        """Calculate relevance score.

        Args:
            article: News article
            category: Target category

        Returns:
            Relevance score (0.0 to 1.0)
        """
        if article.category == category:
            return 1.0
        elif article.category:
            return 0.5
        else:
            return 0.3

    async def calculate_trend_score(
        self,
        article: NewsArticle,
        category: str = "technology",
    ) -> TrendScore:
        """Calculate comprehensive trend score for an article.

        Args:
            article: News article to analyze
            category: Target category

        Returns:
            TrendScore object
        """
        # Get trend data for article keywords
        keywords = article.keywords[:5] if article.keywords else [article.title[:50]]
        trend_data = await self.get_google_trends(keywords)

        # Calculate search volume score
        search_volume = 0.0
        if trend_data:
            avg_volumes = [data.get("average", 0) for data in trend_data.values()]
            search_volume = sum(avg_volumes) / len(avg_volumes) / 100  # Normalize to 0-1

        # Calculate component scores
        recency = self.calculate_recency_score(article.published_date)
        engagement = self.calculate_engagement_score(article, trend_data)
        relevance = self.calculate_relevance_score(article, category)

        # Competition score (inverse - lower competition is better)
        # Simple heuristic: assume lower search volume = less competition
        competition = 1.0 - min(search_volume, 1.0)

        # Calculate final score
        final_score = (
            search_volume * 0.3 +
            recency * 0.25 +
            engagement * 0.25 +
            relevance * 0.1 +
            competition * 0.1
        )

        # Get trending keywords
        trending_keywords = []
        if trend_data:
            trending_keywords = [
                kw for kw, data in trend_data.items()
                if data.get("current", 0) > 60
            ]

        return TrendScore(
            topic=article.title,
            score=final_score,
            search_volume=search_volume,
            recency=recency,
            engagement=engagement,
            relevance=relevance,
            competition=competition,
            trending_keywords=trending_keywords,
        )

    async def select_best_topics(
        self,
        articles: List[NewsArticle],
        category: str = "technology",
        max_topics: int = 5,
    ) -> List[tuple[NewsArticle, TrendScore]]:
        """Select best topics from article list.

        Args:
            articles: List of news articles
            category: Target category
            max_topics: Maximum number of topics to select

        Returns:
            List of (article, trend_score) tuples, sorted by score
        """
        logger.info(f"Analyzing {len(articles)} articles for best topics")

        scored_articles = []

        for article in articles:
            try:
                trend_score = await self.calculate_trend_score(article, category)

                if trend_score.score >= self.min_score:
                    scored_articles.append((article, trend_score))
                    logger.info(
                        f"Topic: {article.title[:50]}... | Score: {trend_score.score:.2f}"
                    )
            except Exception as e:
                logger.error(f"Error scoring article: {e}")
                continue

        # Sort by score (descending)
        scored_articles.sort(key=lambda x: x[1].score, reverse=True)

        # Return top N
        selected = scored_articles[:max_topics]
        logger.info(f"Selected {len(selected)} top topics")

        return selected

    async def is_duplicate_topic(
        self,
        topic: str,
        recent_topics: List[str],
        similarity_threshold: float = 0.7,
    ) -> bool:
        """Check if topic is duplicate or too similar to recent topics.

        Args:
            topic: Topic to check
            recent_topics: List of recent topics
            similarity_threshold: Similarity threshold (0.0 to 1.0)

        Returns:
            True if duplicate, False otherwise
        """
        # Simple word-based similarity check
        topic_words = set(topic.lower().split())

        for recent_topic in recent_topics:
            recent_words = set(recent_topic.lower().split())

            # Calculate Jaccard similarity
            intersection = len(topic_words & recent_words)
            union = len(topic_words | recent_words)

            if union > 0:
                similarity = intersection / union
                if similarity >= similarity_threshold:
                    logger.info(f"Duplicate detected: '{topic}' similar to '{recent_topic}'")
                    return True

        return False
