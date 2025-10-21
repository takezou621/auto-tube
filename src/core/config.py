"""Application configuration management."""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="AutoTube", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Database
    database_url: str = Field(
        default="postgresql://autotube:password@localhost:5432/autotube",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # OpenAI
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", alias="OPENAI_MODEL")

    # Anthropic Claude
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")

    # ElevenLabs
    elevenlabs_api_key: str = Field(default="", alias="ELEVENLABS_API_KEY")
    elevenlabs_voice_id: str = Field(default="", alias="ELEVENLABS_VOICE_ID")

    # Google Cloud
    google_application_credentials: str = Field(
        default="", alias="GOOGLE_APPLICATION_CREDENTIALS"
    )

    # NewsAPI
    news_api_key: str = Field(default="", alias="NEWS_API_KEY")

    # YouTube
    youtube_client_id: str = Field(default="", alias="YOUTUBE_CLIENT_ID")
    youtube_client_secret: str = Field(default="", alias="YOUTUBE_CLIENT_SECRET")
    youtube_redirect_uri: str = Field(
        default="http://localhost:8080/oauth2callback", alias="YOUTUBE_REDIRECT_URI"
    )

    # Stability AI
    stability_api_key: str = Field(default="", alias="STABILITY_API_KEY")

    # Content Settings
    default_video_length: int = Field(default=300, alias="DEFAULT_VIDEO_LENGTH")
    default_language: str = Field(default="ja", alias="DEFAULT_LANGUAGE")
    default_category: str = Field(default="technology", alias="DEFAULT_CATEGORY")

    # Quality Settings
    video_resolution: str = Field(default="1920x1080", alias="VIDEO_RESOLUTION")
    video_fps: int = Field(default=30, alias="VIDEO_FPS")
    audio_bitrate: str = Field(default="128k", alias="AUDIO_BITRATE")
    video_bitrate: str = Field(default="5000k", alias="VIDEO_BITRATE")

    # Schedule Settings
    posting_schedule: str = Field(
        default="Mon:20:00,Wed:19:00,Fri:20:00,Sun:18:00",
        alias="POSTING_SCHEDULE",
    )
    content_generation_advance_hours: int = Field(
        default=12, alias="CONTENT_GENERATION_ADVANCE_HOURS"
    )

    # Trend Analysis
    min_trend_score: float = Field(default=0.6, alias="MIN_TREND_SCORE")
    max_content_age_hours: int = Field(default=48, alias="MAX_CONTENT_AGE_HOURS")

    # Safety & Compliance
    enable_content_review: bool = Field(default=True, alias="ENABLE_CONTENT_REVIEW")
    enable_copyright_check: bool = Field(default=True, alias="ENABLE_COPYRIGHT_CHECK")
    forbidden_keywords: str = Field(
        default="暴力,差別,誹謗中傷", alias="FORBIDDEN_KEYWORDS"
    )

    # Storage
    storage_path: Path = Field(default=Path("/app/data"), alias="STORAGE_PATH")
    video_output_path: Path = Field(
        default=Path("/app/data/videos"), alias="VIDEO_OUTPUT_PATH"
    )
    audio_output_path: Path = Field(
        default=Path("/app/data/audio"), alias="AUDIO_OUTPUT_PATH"
    )
    image_output_path: Path = Field(
        default=Path("/app/data/images"), alias="IMAGE_OUTPUT_PATH"
    )

    # API Rate Limits
    openai_rpm: int = Field(default=500, alias="OPENAI_RPM")
    elevenlabs_character_limit: int = Field(
        default=100000, alias="ELEVENLABS_CHARACTER_LIMIT"
    )
    youtube_quota_daily: int = Field(default=10000, alias="YOUTUBE_QUOTA_DAILY")

    # Monitoring
    sentry_dsn: str = Field(default="", alias="SENTRY_DSN")

    # Feature Flags
    enable_ai_image_generation: bool = Field(
        default=False, alias="ENABLE_AI_IMAGE_GENERATION"
    )
    enable_thumbnail_ab_test: bool = Field(
        default=False, alias="ENABLE_THUMBNAIL_AB_TEST"
    )
    enable_analytics: bool = Field(default=True, alias="ENABLE_ANALYTICS")

    @field_validator("storage_path", "video_output_path", "audio_output_path", "image_output_path")
    @classmethod
    def create_directories(cls, v: Path) -> Path:
        """Create directories if they don't exist."""
        if v and not v.exists():
            v.mkdir(parents=True, exist_ok=True)
        return v

    def get_forbidden_keywords_list(self) -> List[str]:
        """Get forbidden keywords as a list."""
        return [kw.strip() for kw in self.forbidden_keywords.split(",") if kw.strip()]

    def get_posting_schedule_dict(self) -> dict[str, str]:
        """Parse posting schedule into a dictionary."""
        schedule = {}
        for item in self.posting_schedule.split(","):
            if ":" in item:
                parts = item.split(":")
                day = parts[0].strip()
                time = ":".join(parts[1:]).strip()
                schedule[day] = time
        return schedule


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
