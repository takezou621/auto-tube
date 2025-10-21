"""Database configuration and models."""

from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, Boolean, JSON
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.core.config import get_settings

settings = get_settings()

# Convert postgres:// to postgresql+asyncpg://
database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine
engine = create_async_engine(
    database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class Video(Base):
    """Video model for storing video metadata."""

    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    category = Column(String(100), nullable=False)
    script = Column(Text, nullable=False)
    thumbnail_path = Column(String(500), nullable=True)
    video_path = Column(String(500), nullable=False)
    audio_path = Column(String(500), nullable=True)
    duration = Column(Integer, nullable=False)  # in seconds
    youtube_id = Column(String(100), nullable=True, unique=True)
    youtube_url = Column(String(500), nullable=True)
    status = Column(String(50), default="draft")  # draft, processing, ready, uploaded, published
    trend_score = Column(Float, nullable=True)
    source_urls = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    uploaded_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)


class ContentSource(Base):
    """Content source model for tracking collected information."""

    __tablename__ = "content_sources"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(1000), nullable=False, unique=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    source_type = Column(String(50), nullable=False)  # news_api, rss, scrape, reddit, twitter
    published_date = Column(DateTime, nullable=True)
    trend_score = Column(Float, nullable=True)
    keywords = Column(JSON, nullable=True)
    is_used = Column(Boolean, default=False)
    collected_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Analytics(Base):
    """Analytics model for storing video performance data."""

    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, nullable=False, index=True)
    youtube_id = Column(String(100), nullable=False, index=True)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    dislikes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    watch_time_hours = Column(Float, default=0.0)
    average_view_duration = Column(Float, default=0.0)
    click_through_rate = Column(Float, default=0.0)
    audience_retention = Column(Float, default=0.0)
    impressions = Column(Integer, default=0)
    data_snapshot = Column(JSON, nullable=True)
    collected_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ScheduledPost(Base):
    """Scheduled post model for managing video publishing schedule."""

    __tablename__ = "scheduled_posts"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, nullable=True)
    topic = Column(String(500), nullable=False)
    category = Column(String(100), nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    priority = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session.

    Yields:
        AsyncSession: Database session
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """Drop all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
