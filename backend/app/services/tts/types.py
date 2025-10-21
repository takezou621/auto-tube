"""TTS サービスで共有する型定義。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(slots=True)
class VoiceSettings:
    """ElevenLabs API の voice_settings に対応する設定値。"""

    stability: float | None = None
    similarity: float | None = None
    style: float | None = None
    use_speaker_boost: bool | None = None

    def model_dump(self) -> dict[str, float | bool]:
        """None を除外した辞書を返す。"""

        return {
            key: value
            for key, value in {
                "stability": self.stability,
                "similarity_boost": self.similarity,
                "style": self.style,
                "use_speaker_boost": self.use_speaker_boost,
            }.items()
            if value is not None
        }


OutputFormat = Literal[
    "mp3_44100_64",
    "mp3_44100_96",
    "mp3_44100_128",
    "mp3_44100_192",
    "mp3_48000_192",
    "pcm_16000",
    "pcm_22050",
    "pcm_24000",
    "pcm_44100",
    "ulaw_8000",
]


@dataclass(slots=True)
class TTSRequest:
    """音声合成リクエスト。"""

    text: str
    voice_id: str | None = None
    model_id: str | None = None
    output_format: OutputFormat | None = None
    voice_settings: VoiceSettings | None = None


@dataclass(slots=True)
class TTSResult:
    """音声合成の結果。"""

    audio: bytes
    content_type: str
    request_id: str | None = None
