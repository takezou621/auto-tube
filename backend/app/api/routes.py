"""API ルーティング定義。"""
from fastapi import APIRouter

from app.api.projects import router as projects_router

router = APIRouter()
router.include_router(projects_router)


@router.get("/health", summary="ヘルスチェック")
async def health_check() -> dict[str, str]:
    """疎通確認用エンドポイント。"""

    return {"status": "ok"}


@router.get("/api/test", summary="テスト用 API")
async def api_test() -> dict[str, str]:
    """フロント連携確認用の簡易 API。"""

    return {
        "message": "AutoTube API が正常に動作しています",
        "status": "ok",
    }
