"""Celery tasks for scheduled operations."""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from celery import Task
from celery.utils.log import get_task_logger

from src.scheduler.celery_app import app
from src.core.config import get_settings
from src.core.database import async_session_maker, Video, Analytics
from src.pipeline.orchestrator import VideoGenerationPipeline

logger = get_task_logger(__name__)
settings = get_settings()


class AsyncTask(Task):
    """Base task class for async operations."""

    def __call__(self, *args, **kwargs):
        """Execute task in async context."""
        return asyncio.run(self.run_async(*args, **kwargs))

    async def run_async(self, *args, **kwargs):
        """Override this method in subclasses."""
        raise NotImplementedError


@app.task(
    name="src.scheduler.tasks.generate_and_upload_video",
    bind=True,
    base=AsyncTask,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
async def generate_and_upload_video(self, category: str = "technology") -> dict:
    """Generate and upload video for specified category.

    Args:
        category: Video category

    Returns:
        Dictionary with result
    """
    logger.info(f"Starting video generation for category: {category}")

    try:
        # Create pipeline
        pipeline = VideoGenerationPipeline()

        # Generate topic based on category
        if category == "weekly_summary":
            topic = "今週のテクノロジーニュースまとめ"
        else:
            topic = f"{category} latest news"

        # Generate video
        result = await pipeline.generate_complete_video(
            topic=topic,
            category=category,
        )

        if result.get("status") == "success":
            logger.info(f"Video generated successfully: {result.get('video_id')}")

            # Upload to YouTube if enabled
            if result.get("video_path"):
                from src.uploader.youtube_uploader import YouTubeUploader

                uploader = YouTubeUploader()
                credentials_path = Path("config/youtube_credentials.json")

                try:
                    uploader.authenticate(credentials_path)

                    upload_result = await uploader.upload_video(
                        video_path=Path(result["video_path"]),
                        title=result["title"],
                        description=result["description"],
                        tags=result.get("tags", []),
                        category_id="28",  # Science & Technology
                        privacy_status="public",
                    )

                    # Set thumbnail
                    if result.get("thumbnail_path"):
                        await uploader.set_thumbnail(
                            upload_result["id"],
                            Path(result["thumbnail_path"]),
                        )

                    logger.info(f"Video uploaded to YouTube: {upload_result['url']}")
                    result["youtube_url"] = upload_result["url"]
                    result["youtube_id"] = upload_result["id"]

                except Exception as e:
                    logger.error(f"Failed to upload to YouTube: {e}")
                    result["upload_error"] = str(e)

        return result

    except Exception as exc:
        logger.error(f"Error generating video: {exc}")
        # Retry task
        raise self.retry(exc=exc)


@app.task(name="src.scheduler.tasks.collect_video_analytics")
async def collect_video_analytics() -> dict:
    """Collect analytics data for all published videos.

    Returns:
        Dictionary with collection results
    """
    logger.info("Collecting video analytics")

    try:
        from src.uploader.youtube_uploader import YouTubeUploader
        from sqlalchemy import select

        uploader = YouTubeUploader()
        credentials_path = Path("config/youtube_credentials.json")

        try:
            uploader.authenticate(credentials_path)
        except Exception as e:
            logger.error(f"Failed to authenticate with YouTube: {e}")
            return {"status": "error", "message": str(e)}

        collected = 0
        errors = 0

        async with async_session_maker() as session:
            # Get all published videos
            result = await session.execute(
                select(Video).where(Video.youtube_id.isnot(None))
            )
            videos = result.scalars().all()

            for video in videos:
                try:
                    # Get analytics from YouTube
                    analytics_data = await uploader.get_video_analytics(video.youtube_id)

                    if analytics_data:
                        # Save to database
                        analytics = Analytics(
                            video_id=video.id,
                            youtube_id=video.youtube_id,
                            views=analytics_data.get("views", 0),
                            likes=analytics_data.get("likes", 0),
                            comments=analytics_data.get("comments", 0),
                            data_snapshot=analytics_data,
                        )
                        session.add(analytics)
                        collected += 1

                except Exception as e:
                    logger.error(f"Error collecting analytics for video {video.id}: {e}")
                    errors += 1

            await session.commit()

        logger.info(f"Analytics collection complete: {collected} collected, {errors} errors")

        return {
            "status": "success",
            "collected": collected,
            "errors": errors,
        }

    except Exception as e:
        logger.error(f"Error in analytics collection: {e}")
        return {"status": "error", "message": str(e)}


@app.task(name="src.scheduler.tasks.cleanup_old_files")
def cleanup_old_files(days_old: int = 30) -> dict:
    """Clean up old video, audio, and image files.

    Args:
        days_old: Delete files older than this many days

    Returns:
        Dictionary with cleanup results
    """
    logger.info(f"Cleaning up files older than {days_old} days")

    deleted_count = 0
    freed_space = 0

    try:
        cutoff_date = datetime.now() - timedelta(days=days_old)
        directories = [
            settings.video_output_path,
            settings.audio_output_path,
            settings.image_output_path,
        ]

        for directory in directories:
            if not directory.exists():
                continue

            for file_path in directory.glob("*"):
                if not file_path.is_file():
                    continue

                # Check file age
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

                if file_mtime < cutoff_date:
                    file_size = file_path.stat().st_size
                    try:
                        file_path.unlink()
                        deleted_count += 1
                        freed_space += file_size
                        logger.debug(f"Deleted: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to delete {file_path}: {e}")

        freed_space_mb = freed_space / (1024 * 1024)
        logger.info(
            f"Cleanup complete: {deleted_count} files deleted, "
            f"{freed_space_mb:.2f}MB freed"
        )

        return {
            "status": "success",
            "deleted_count": deleted_count,
            "freed_space_mb": round(freed_space_mb, 2),
        }

    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return {"status": "error", "message": str(e)}


@app.task(name="src.scheduler.tasks.test_task")
def test_task(message: str = "Hello") -> str:
    """Simple test task.

    Args:
        message: Test message

    Returns:
        Response message
    """
    logger.info(f"Test task received message: {message}")
    return f"Task completed: {message}"
