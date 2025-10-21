"""設定値から TTS プロバイダを生成するヘルパー。"""
from __future__ import annotations

from functools import lru_cache

from app.core.settings import get_settings

from .elevenlabs import ElevenLabsTTSProvider
from .provider import TTSProvider
from .types import VoiceSettings


@lru_cache
def get_tts_provider() -> TTSProvider:
    settings = get_settings()
    if not settings.elevenlabs_api_key:
        raise RuntimeError("ElevenLabs API キーが設定されていません。環境変数を確認してください。")

    return ElevenLabsTTSProvider(
        api_key=settings.elevenlabs_api_key,
        default_voice_id=settings.elevenlabs_voice_id,
        default_model_id=settings.elevenlabs_model_id,
        default_output_format=settings.elevenlabs_output_format,
        default_voice_settings=VoiceSettings(
            stability=settings.elevenlabs_stability,
            similarity=settings.elevenlabs_similarity,
            style=settings.elevenlabs_style,
            use_speaker_boost=settings.elevenlabs_use_speaker_boost,
        ),
    )
