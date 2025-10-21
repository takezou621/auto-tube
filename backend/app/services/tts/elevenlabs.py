"""ElevenLabs API を利用した TTS プロバイダ実装。"""
from __future__ import annotations

import logging
from typing import Callable

import httpx

from .provider import TTSProvider, TTSProviderError
from .types import TTSRequest, TTSResult, VoiceSettings

LOGGER = logging.getLogger(__name__)


class ElevenLabsTTSProvider(TTSProvider):
    """ElevenLabs Text-to-Speech を利用する実装。"""

    BASE_URL = "https://api.elevenlabs.io"

    def __init__(
        self,
        api_key: str,
        *,
        default_voice_id: str,
        default_model_id: str = "eleven_monolingual_v1",
        default_output_format: str = "mp3_44100_128",
        default_voice_settings: VoiceSettings | None = None,
        timeout: float = 30.0,
        client_factory: Callable[[], httpx.AsyncClient] | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("ElevenLabs API キーが設定されていません。")
        if not default_voice_id:
            raise ValueError("デフォルトの voice_id が設定されていません。")

        self._api_key = api_key
        self._default_voice_id = default_voice_id
        self._default_model_id = default_model_id
        self._default_output_format = default_output_format
        self._default_voice_settings = default_voice_settings or VoiceSettings()
        self._timeout = timeout
        self._client_factory = client_factory or self._create_default_client

    def _create_default_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=self.BASE_URL, timeout=self._timeout)

    async def synthesize(self, request: TTSRequest) -> TTSResult:
        voice_id = request.voice_id or self._default_voice_id
        if not voice_id:
            raise TTSProviderError("voice_id が指定されていません。")

        payload: dict[str, object] = {"text": request.text}
        payload["model_id"] = request.model_id or self._default_model_id
        payload["output_format"] = request.output_format or self._default_output_format

        voice_settings = request.voice_settings or self._default_voice_settings
        settings_payload = voice_settings.model_dump()
        if settings_payload:
            payload["voice_settings"] = settings_payload

        headers = {
            "xi-api-key": self._api_key,
            "Accept": "audio/mpeg",
        }

        endpoint = f"/v1/text-to-speech/{voice_id}"

        client = self._client_factory()
        async with client:
            try:
                response = await client.post(endpoint, headers=headers, json=payload)
            except httpx.HTTPError as exc:  # pragma: no cover - 低頻度エラーの保険
                LOGGER.exception("ElevenLabs API 呼び出しで通信エラー", exc_info=exc)
                raise TTSProviderError("ElevenLabs API との通信に失敗しました。") from exc

        if response.status_code >= 400:
            try:
                detail = response.json()
            except ValueError:  # JSON でないエラー応答
                detail = {"error": response.text}
            LOGGER.error("ElevenLabs API エラー: %s", detail)
            raise TTSProviderError(
                f"ElevenLabs API 呼び出しが失敗しました (status={response.status_code})"
            )

        return TTSResult(
            audio=response.content,
            content_type=response.headers.get("content-type", "audio/mpeg"),
            request_id=response.headers.get("x-request-id"),
        )
