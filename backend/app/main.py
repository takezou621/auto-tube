"""FastAPI アプリケーションのエントリポイント。"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.core.settings import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.debug)

# CORS 設定
allowed_origins = [origin.strip() for origin in settings.backend_cors_origins.split(",") if origin]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターを登録
app.include_router(api_router)


@app.get("/", summary="ルート確認")
async def root() -> dict[str, str]:
    """トップレベルの疎通確認。"""

    return {"message": "AutoTube backend is running."}
