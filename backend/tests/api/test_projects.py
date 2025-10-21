import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services import projects_store


async def _client() -> AsyncClient:
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://testserver")


def _sample_payload() -> dict[str, str]:
    return {
        "title": "シティタワー品川イースト",
        "location": "東京都港区港南",
        "highlight": "駅直結で想定利回り4.2%の稀少物件",
        "audience": "entry",
        "duration": "standard",
        "call_to_action": "無料ウェビナーで詳細をご確認ください",
        "tone": "trust",
    }


@pytest.mark.asyncio
async def test_create_project() -> None:
    async with await _client() as client:
        response = await client.post("/api/projects/", json=_sample_payload())
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "シティタワー品川イースト"
    assert len(body["sections"]) == 4
    assert body["sections"][0]["title"] in {"オープニング", "イントロ", "導入"}
    assert body["summary"].startswith("シティタワー品川イースト")


@pytest.mark.asyncio
async def test_get_project() -> None:
    async with await _client() as client:
        create_res = await client.post("/api/projects/", json=_sample_payload())
        project_id = create_res.json()["id"]
        get_res = await client.get(f"/api/projects/{project_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == project_id


@pytest.mark.asyncio
async def test_validation_error() -> None:
    async with await _client() as client:
        res = await client.post(
            "/api/projects/",
            json={
                "title": "x",
                "location": "y",
                "highlight": "短い",
                "audience": "entry",
                "duration": "short",
                "call_to_action": "ok",
                "tone": "trust",
            },
        )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_list_projects_empty() -> None:
    async with await _client() as client:
        response = await client.get("/api/projects/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_projects_returns_created_items() -> None:
    async with await _client() as client:
        await client.post("/api/projects/", json=_sample_payload())
        await client.post("/api/projects/", json=_sample_payload() | {"title": "別案件"})
        response = await client.get("/api/projects/")
    payloads = response.json()
    assert len(payloads) == 2
    titles = [item["title"] for item in payloads]
    assert titles[0] == "別案件"  # 新しい順


@pytest.mark.asyncio
async def test_list_projects_reads_from_persisted_file(monkeypatch) -> None:
    async with await _client() as client:
        created = await client.post("/api/projects/", json=_sample_payload())
        project_id = created.json()["id"]

        # メモリキャッシュをクリアしても、ファイルから読み込まれることを検証
        projects_store.reset_store()

        response = await client.get("/api/projects/")

    ids = [item["id"] for item in response.json()]
    assert project_id in ids
