# AutoTube Backend (FastAPI)

不動産投資をテーマにした YouTube 自動生成サービスのバックエンド API 雛形です。

## 必要要件
- Python 3.11
- Poetry 1.8 以上

## セットアップ
```bash
cd backend
poetry install
```

## 開発サーバーの起動
```bash
poetry run uvicorn app.main:app --reload
```

## テスト
```bash
poetry run pytest
```

## 音声合成 (TTS)
- `ELEVENLABS_API_KEY` と `ELEVENLABS_VOICE_ID` を `.env` に設定してください。
- サーバー起動後に `/api/test` を叩いて疎通確認ができます。
