"""Analytics and optimization system."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import Video, Analytics, async_session_maker
from src.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """Video performance metrics."""

    video_id: int
    title: str
    views: int
    likes: int
    comments: int
    ctr: float
    avg_view_duration: float
    audience_retention: float
    score: float


class AnalyticsAnalyzer:
    """Analyze video performance and provide insights."""

    def __init__(self) -> None:
        """Initialize analytics analyzer."""
        pass

    async def get_video_performance(
        self,
        video_id: int,
        session: AsyncSession,
    ) -> Optional[PerformanceMetrics]:
        """Get performance metrics for a video.

        Args:
            video_id: Video ID
            session: Database session

        Returns:
            PerformanceMetrics or None
        """
        try:
            # Get video
            video_result = await session.execute(
                select(Video).where(Video.id == video_id)
            )
            video = video_result.scalar_one_or_none()

            if not video:
                return None

            # Get latest analytics
            analytics_result = await session.execute(
                select(Analytics)
                .where(Analytics.video_id == video_id)
                .order_by(Analytics.collected_at.desc())
                .limit(1)
            )
            analytics = analytics_result.scalar_one_or_none()

            if not analytics:
                return None

            # Calculate performance score
            score = self._calculate_performance_score(analytics)

            return PerformanceMetrics(
                video_id=video.id,
                title=video.title,
                views=analytics.views,
                likes=analytics.likes,
                comments=analytics.comments,
                ctr=analytics.click_through_rate,
                avg_view_duration=analytics.average_view_duration,
                audience_retention=analytics.audience_retention,
                score=score,
            )

        except Exception as e:
            logger.error(f"Error getting video performance: {e}")
            return None

    def _calculate_performance_score(self, analytics: Analytics) -> float:
        """Calculate overall performance score.

        Args:
            analytics: Analytics data

        Returns:
            Performance score (0.0 to 1.0)
        """
        # Normalize metrics
        views_score = min(analytics.views / 10000, 1.0)  # 10k views = max
        likes_ratio = analytics.likes / max(analytics.views, 1)
        likes_score = min(likes_ratio * 20, 1.0)  # 5% like ratio = max
        ctr_score = min(analytics.click_through_rate / 10, 1.0)  # 10% CTR = max
        retention_score = analytics.audience_retention  # Already 0-1

        # Weighted average
        score = (
            views_score * 0.3 +
            likes_score * 0.2 +
            ctr_score * 0.25 +
            retention_score * 0.25
        )

        return score

    async def get_top_performing_videos(
        self,
        limit: int = 10,
        days: int = 30,
    ) -> List[PerformanceMetrics]:
        """Get top performing videos.

        Args:
            limit: Number of videos to return
            days: Look back period in days

        Returns:
            List of performance metrics
        """
        async with async_session_maker() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Get videos with analytics
            result = await session.execute(
                select(Video)
                .where(Video.created_at >= cutoff_date)
                .order_by(Video.created_at.desc())
            )
            videos = result.scalars().all()

            performances = []
            for video in videos:
                perf = await self.get_video_performance(video.id, session)
                if perf:
                    performances.append(perf)

            # Sort by score
            performances.sort(key=lambda x: x.score, reverse=True)

            return performances[:limit]

    async def get_channel_statistics(self, days: int = 30) -> Dict:
        """Get overall channel statistics.

        Args:
            days: Look back period in days

        Returns:
            Dictionary with channel stats
        """
        async with async_session_maker() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Count videos
            video_count_result = await session.execute(
                select(func.count(Video.id))
                .where(Video.created_at >= cutoff_date)
            )
            video_count = video_count_result.scalar()

            # Get latest analytics for all videos
            analytics_result = await session.execute(
                select(Analytics)
                .join(Video, Analytics.video_id == Video.id)
                .where(Video.created_at >= cutoff_date)
            )
            all_analytics = analytics_result.scalars().all()

            # Calculate totals
            total_views = sum(a.views for a in all_analytics)
            total_likes = sum(a.likes for a in all_analytics)
            total_comments = sum(a.comments for a in all_analytics)

            # Calculate averages
            avg_views = total_views / max(video_count, 1)
            avg_ctr = sum(a.click_through_rate for a in all_analytics) / max(len(all_analytics), 1)
            avg_retention = sum(a.audience_retention for a in all_analytics) / max(len(all_analytics), 1)

            return {
                "period_days": days,
                "video_count": video_count,
                "total_views": total_views,
                "total_likes": total_likes,
                "total_comments": total_comments,
                "avg_views_per_video": round(avg_views, 2),
                "avg_ctr": round(avg_ctr, 4),
                "avg_retention": round(avg_retention, 4),
            }

    async def generate_insights(self) -> List[str]:
        """Generate insights and recommendations.

        Returns:
            List of insight strings
        """
        insights = []

        # Get top videos
        top_videos = await self.get_top_performing_videos(limit=5, days=30)

        if top_videos:
            best_video = top_videos[0]
            insights.append(
                f"📈 Best performing video: '{best_video.title}' "
                f"({best_video.views:,} views, {best_video.score:.2f} score)"
            )

        # Get channel stats
        stats = await self.get_channel_statistics(days=30)

        insights.append(
            f"📊 Last 30 days: {stats['video_count']} videos, "
            f"{stats['total_views']:,} total views"
        )

        # CTR recommendations
        if stats['avg_ctr'] < 0.04:
            insights.append(
                "💡 CTR below 4% - consider improving thumbnails and titles"
            )
        elif stats['avg_ctr'] > 0.06:
            insights.append(
                "✓ Excellent CTR! Your thumbnails and titles are working well"
            )

        # Retention recommendations
        if stats['avg_retention'] < 0.40:
            insights.append(
                "💡 Low retention - consider shorter videos or better hooks"
            )
        elif stats['avg_retention'] > 0.50:
            insights.append(
                "✓ Great retention! Viewers are staying engaged"
            )

        return insights

    async def compare_video_performance(
        self,
        video_id_1: int,
        video_id_2: int,
    ) -> Dict:
        """Compare performance of two videos.

        Args:
            video_id_1: First video ID
            video_id_2: Second video ID

        Returns:
            Comparison dictionary
        """
        async with async_session_maker() as session:
            perf1 = await self.get_video_performance(video_id_1, session)
            perf2 = await self.get_video_performance(video_id_2, session)

            if not perf1 or not perf2:
                return {"error": "One or both videos not found"}

            return {
                "video1": {
                    "id": perf1.video_id,
                    "title": perf1.title,
                    "views": perf1.views,
                    "ctr": perf1.ctr,
                    "retention": perf1.audience_retention,
                    "score": perf1.score,
                },
                "video2": {
                    "id": perf2.video_id,
                    "title": perf2.title,
                    "views": perf2.views,
                    "ctr": perf2.ctr,
                    "retention": perf2.audience_retention,
                    "score": perf2.score,
                },
                "winner": "video1" if perf1.score > perf2.score else "video2",
                "score_difference": abs(perf1.score - perf2.score),
            }
