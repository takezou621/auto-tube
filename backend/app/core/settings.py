"""アプリ全体の設定管理モジュール。"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """環境変数経由で読み込む設定値。"""

    app_name: str = "AutoTube API"
    environment: str = "development"
    debug: bool = False
    backend_cors_origins: str = "*"
    port: int = 8000

    elevenlabs_api_key: str | None = None
    elevenlabs_voice_id: str = ""
    elevenlabs_model_id: str = "eleven_multilingual_v2"
    elevenlabs_output_format: str = "mp3_44100_128"
    elevenlabs_stability: float | None = None
    elevenlabs_similarity: float | None = None
    elevenlabs_style: float | None = None
    elevenlabs_use_speaker_boost: bool | None = None
    enable_tts_mock: bool = False
    projects_store_path: str = "data/projects.json"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """設定をキャッシュして何度も読み込まないようにする。"""

    return Settings()
