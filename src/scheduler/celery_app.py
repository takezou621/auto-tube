"""Celery application for task scheduling."""

from celery import Celery
from celery.schedules import crontab

from src.core.config import get_settings

settings = get_settings()

# Create Celery app
app = Celery(
    "autotube",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["src.scheduler.tasks"],
)

# Configure Celery
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Tokyo",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=10,
)

# Configure periodic tasks
app.conf.beat_schedule = {
    # Generate video every Monday at 20:00
    "generate-monday-video": {
        "task": "src.scheduler.tasks.generate_and_upload_video",
        "schedule": crontab(hour=20, minute=0, day_of_week=1),  # Monday
        "args": ("technology",),
    },
    # Generate video every Wednesday at 19:00
    "generate-wednesday-video": {
        "task": "src.scheduler.tasks.generate_and_upload_video",
        "schedule": crontab(hour=19, minute=0, day_of_week=3),  # Wednesday
        "args": ("business",),
    },
    # Generate video every Friday at 20:00
    "generate-friday-video": {
        "task": "src.scheduler.tasks.generate_and_upload_video",
        "schedule": crontab(hour=20, minute=0, day_of_week=5),  # Friday
        "args": ("technology",),
    },
    # Generate video every Sunday at 18:00 (weekly summary)
    "generate-sunday-video": {
        "task": "src.scheduler.tasks.generate_and_upload_video",
        "schedule": crontab(hour=18, minute=0, day_of_week=0),  # Sunday
        "args": ("weekly_summary",),
    },
    # Collect analytics data daily at 1:00 AM
    "collect-analytics": {
        "task": "src.scheduler.tasks.collect_video_analytics",
        "schedule": crontab(hour=1, minute=0),
    },
    # Clean up old files weekly on Monday at 2:00 AM
    "cleanup-old-files": {
        "task": "src.scheduler.tasks.cleanup_old_files",
        "schedule": crontab(hour=2, minute=0, day_of_week=1),
    },
}
