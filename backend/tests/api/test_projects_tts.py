import pytest
from httpx import ASGITransport, AsyncClient

from app.core.settings import get_settings
from app.main import app
from app.services.tts.provider import TTSProviderError


async def _client() -> AsyncClient:
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://testserver")


def _sample_payload() -> dict[str, str]:
    return {
        "title": "港区プレミアムタワー",
        "location": "東京都港区",
        "highlight": "都心駅徒歩2分・平均実質利回り4.1%",
        "audience": "experienced",
        "duration": "short",
        "call_to_action": "今すぐ資料請求で優先案内を確保してください",
        "tone": "premium",
    }


@pytest.mark.asyncio
async def test_synthesize_project_tts_with_mock(monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_TTS_MOCK", "true")
    get_settings.cache_clear()
    async with await _client() as client:
        project = await client.post("/api/projects/", json=_sample_payload())
        project_id = project.json()["id"]
        response = await client.post(f"/api/projects/{project_id}/tts")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/")
    assert response.content.startswith(b"MOCK_AUDIO")
    get_settings.cache_clear()
    monkeypatch.delenv("ENABLE_TTS_MOCK", raising=False)


@pytest.mark.asyncio
async def test_synthesize_project_tts_unavailable(monkeypatch) -> None:
    monkeypatch.delenv("ENABLE_TTS_MOCK", raising=False)
    get_settings.cache_clear()
    async with await _client() as client:
        project = await client.post("/api/projects/", json=_sample_payload())
        project_id = project.json()["id"]
        response = await client.post(f"/api/projects/{project_id}/tts")
    assert response.status_code == 503
    assert response.json()["detail"] == "TTSプロバイダが未設定です"
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_synthesize_project_tts_provider_error(monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_TTS_MOCK", "false")
    get_settings.cache_clear()

    class _FailingProvider:
        async def synthesize(self, _request):  # type: ignore[no-untyped-def]
            raise TTSProviderError("provider error")

    monkeypatch.setattr("app.services.tts.usecase.get_tts_provider", lambda: _FailingProvider())

    async with await _client() as client:
        project = await client.post("/api/projects/", json=_sample_payload())
        project_id = project.json()["id"]
        response = await client.post(f"/api/projects/{project_id}/tts")
    assert response.status_code == 502
    assert "provider error" in response.json()["detail"]
    get_settings.cache_clear()
    monkeypatch.delenv("ENABLE_TTS_MOCK", raising=False)


@pytest.mark.asyncio
async def test_synthesize_project_tts_not_found() -> None:
    async with await _client() as client:
        response = await client.post("/api/projects/00000000-0000-0000-0000-000000000000/tts")
    assert response.status_code == 404
