import json

import pytest
from httpx import AsyncClient, MockTransport, Request, Response

from app.services.tts.elevenlabs import ElevenLabsTTSProvider
from app.services.tts.provider import TTSProviderError
from app.services.tts.types import TTSRequest, VoiceSettings


@pytest.mark.asyncio
async def test_synthesize_success(monkeypatch):
    payload_captured: dict[str, object] = {}

    def handler(request: Request) -> Response:
        nonlocal payload_captured
        payload_captured = json.loads(request.content.decode("utf-8"))
        assert request.headers["xi-api-key"] == "test-key"
        return Response(200, headers={"content-type": "audio/mpeg", "x-request-id": "req-1"}, content=b"audio")

    transport = MockTransport(handler)

    def client_factory() -> AsyncClient:
        return AsyncClient(transport=transport, base_url="https://api.elevenlabs.io")

    provider = ElevenLabsTTSProvider(
        api_key="test-key",
        default_voice_id="voice-id",
        default_model_id="model-id",
        default_output_format="mp3_44100_128",
        default_voice_settings=VoiceSettings(stability=0.3, similarity=0.6),
        client_factory=client_factory,
    )

    result = await provider.synthesize(TTSRequest(text="こんにちは"))

    assert result.audio == b"audio"
    assert result.content_type == "audio/mpeg"
    assert result.request_id == "req-1"
    assert payload_captured["text"] == "こんにちは"
    assert payload_captured["model_id"] == "model-id"
    assert payload_captured["output_format"] == "mp3_44100_128"
    assert payload_captured["voice_settings"] == {"stability": 0.3, "similarity_boost": 0.6}


@pytest.mark.asyncio
async def test_synthesize_http_error(monkeypatch):
    def handler(_: Request) -> Response:
        return Response(500, content=b"internal error")

    transport = MockTransport(handler)

    def client_factory() -> AsyncClient:
        return AsyncClient(transport=transport, base_url="https://api.elevenlabs.io")

    provider = ElevenLabsTTSProvider(
        api_key="test-key",
        default_voice_id="voice-id",
        client_factory=client_factory,
    )

    with pytest.raises(TTSProviderError):
        await provider.synthesize(TTSRequest(text="失敗ケース"))
