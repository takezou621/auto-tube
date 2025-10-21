"""FastAPI application for Auto-Tube."""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from src.core.config import get_settings
from src.core.logging import setup_logging, get_logger
from src.pipeline.orchestrator import VideoGenerationPipeline
from src.analytics.analyzer import AnalyticsAnalyzer
from src.core.database import async_session_maker, Video, Analytics, init_db
from sqlalchemy import select

setup_logging()
logger = get_logger(__name__)
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Auto-Tube API",
    description="Automated YouTube video generation and publishing service",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class VideoGenerationRequest(BaseModel):
    """Video generation request model."""

    topic: Optional[str] = None
    category: str = "technology"
    auto_upload: bool = False


class VideoResponse(BaseModel):
    """Video response model."""

    id: int
    title: str
    description: Optional[str]
    category: str
    status: str
    youtube_url: Optional[str]
    created_at: datetime


class AnalyticsResponse(BaseModel):
    """Analytics response model."""

    video_id: int
    views: int
    likes: int
    comments: int
    ctr: float
    avg_view_duration: float
    collected_at: datetime


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info("Starting Auto-Tube API")
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")


# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "status": "ok",
        "service": "Auto-Tube API",
        "version": "1.0.0",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


# Video generation endpoints
@app.post("/videos/generate")
async def generate_video(
    request: VideoGenerationRequest,
    background_tasks: BackgroundTasks,
):
    """Generate a new video.

    This endpoint starts video generation asynchronously.
    """
    logger.info(f"Received video generation request: {request}")

    try:
        pipeline = VideoGenerationPipeline()

        # Run in background
        background_tasks.add_task(
            pipeline.generate_complete_video,
            topic=request.topic,
            category=request.category,
            auto_upload=request.auto_upload,
        )

        return {
            "status": "accepted",
            "message": "Video generation started",
            "request": request.dict(),
        }

    except Exception as e:
        logger.error(f"Error starting video generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/videos", response_model=List[VideoResponse])
async def list_videos(
    limit: int = 10,
    offset: int = 0,
    category: Optional[str] = None,
):
    """List all videos."""
    try:
        async with async_session_maker() as session:
            query = select(Video).order_by(Video.created_at.desc())

            if category:
                query = query.where(Video.category == category)

            query = query.limit(limit).offset(offset)

            result = await session.execute(query)
            videos = result.scalars().all()

            return [
                VideoResponse(
                    id=v.id,
                    title=v.title,
                    description=v.description,
                    category=v.category,
                    status=v.status,
                    youtube_url=v.youtube_url,
                    created_at=v.created_at,
                )
                for v in videos
            ]

    except Exception as e:
        logger.error(f"Error listing videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/videos/{video_id}", response_model=VideoResponse)
async def get_video(video_id: int):
    """Get video by ID."""
    try:
        async with async_session_maker() as session:
            result = await session.execute(
                select(Video).where(Video.id == video_id)
            )
            video = result.scalar_one_or_none()

            if not video:
                raise HTTPException(status_code=404, detail="Video not found")

            return VideoResponse(
                id=video.id,
                title=video.title,
                description=video.description,
                category=video.category,
                status=video.status,
                youtube_url=video.youtube_url,
                created_at=video.created_at,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/{video_id}", response_model=List[AnalyticsResponse])
async def get_video_analytics(video_id: int):
    """Get analytics for a video."""
    try:
        async with async_session_maker() as session:
            result = await session.execute(
                select(Analytics)
                .where(Analytics.video_id == video_id)
                .order_by(Analytics.collected_at.desc())
                .limit(30)
            )
            analytics = result.scalars().all()

            if not analytics:
                raise HTTPException(status_code=404, detail="No analytics found")

            return [
                AnalyticsResponse(
                    video_id=a.video_id,
                    views=a.views,
                    likes=a.likes,
                    comments=a.comments,
                    ctr=a.click_through_rate,
                    avg_view_duration=a.average_view_duration,
                    collected_at=a.collected_at,
                )
                for a in analytics
            ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_channel_stats(days: int = 30):
    """Get channel statistics."""
    try:
        analyzer = AnalyticsAnalyzer()
        stats = await analyzer.get_channel_statistics(days=days)
        return stats

    except Exception as e:
        logger.error(f"Error getting channel stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/insights")
async def get_insights():
    """Get insights and recommendations."""
    try:
        analyzer = AnalyticsAnalyzer()
        insights = await analyzer.generate_insights()
        return {"insights": insights}

    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/top-videos")
async def get_top_videos(limit: int = 10, days: int = 30):
    """Get top performing videos."""
    try:
        analyzer = AnalyticsAnalyzer()
        top_videos = await analyzer.get_top_performing_videos(limit=limit, days=days)

        return {
            "top_videos": [
                {
                    "video_id": v.video_id,
                    "title": v.title,
                    "views": v.views,
                    "likes": v.likes,
                    "ctr": v.ctr,
                    "retention": v.audience_retention,
                    "score": v.score,
                }
                for v in top_videos
            ]
        }

    except Exception as e:
        logger.error(f"Error getting top videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
