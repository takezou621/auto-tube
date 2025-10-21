# Auto-Tube

YouTube向け自動動画生成・投稿サービス

## 概要

Auto-Tubeは、特定のテーマに関連する情報やニュースを自動的に収集し、5分程度のまとめ動画を生成してYouTubeに自動投稿するシステムです。

### 主な機能

- ニュース・情報の自動収集
- AIによるスクリプト生成（LLM）
- 自然な音声合成（TTS）
- 自動動画編集
- サムネイル自動生成
- SEO最適化
- YouTube自動アップロード
- トレンド分析・最適化

### 目標

- 視聴者数: 10万人以上
- YouTube収益化達成
- 高品質なコンテンツの継続的な提供

## 技術スタック

- **言語**: Python 3.11+
- **フレームワーク**: FastAPI, Celery
- **データベース**: PostgreSQL, Redis
- **AI/ML**: OpenAI GPT-4, ElevenLabs TTS
- **動画処理**: FFmpeg, MoviePy
- **インフラ**: Docker, AWS/GCP

## プロジェクト構成

```
auto-tube/
├── src/
│   ├── collectors/      # 情報収集モジュール
│   ├── analyzers/       # トレンド分析
│   ├── generators/      # スクリプト生成
│   ├── voice/           # 音声合成
│   ├── video/           # 動画編集
│   ├── thumbnail/       # サムネイル生成
│   ├── seo/             # SEO最適化
│   ├── uploader/        # YouTubeアップロード
│   ├── scheduler/       # スケジューリング
│   └── analytics/       # 分析・レポート
├── tests/               # テストコード
├── config/              # 設定ファイル
├── data/                # データディレクトリ
├── docs/                # ドキュメント
└── scripts/             # ユーティリティスクリプト
```

## セットアップ

### 前提条件

- Python 3.11以上
- Docker & Docker Compose
- FFmpeg
- 各種APIキー（OpenAI, ElevenLabs, NewsAPI等）

### インストール

```bash
# リポジトリのクローン
git clone https://github.com/takezou621/auto-tube.git
cd auto-tube

# 仮想環境の作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt

# 環境変数の設定
cp .env.example .env
# .envファイルを編集してAPIキーを設定

# データベースのセットアップ
docker-compose up -d postgres redis
python scripts/init_db.py
```

### 設定

`.env`ファイルに以下を設定:

```env
# OpenAI
OPENAI_API_KEY=your_key_here

# ElevenLabs
ELEVENLABS_API_KEY=your_key_here

# NewsAPI
NEWS_API_KEY=your_key_here

# YouTube
YOUTUBE_CLIENT_ID=your_client_id
YOUTUBE_CLIENT_SECRET=your_client_secret

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/autotube
REDIS_URL=redis://localhost:6379/0
```

## 使い方

### 動画の自動生成・投稿

```bash
# 単発実行
python -m src.main generate --topic "AI technology"

# スケジューラー起動（定期実行）
python -m src.scheduler start
```

### Web API

```bash
# APIサーバー起動
uvicorn src.api.main:app --reload

# APIドキュメント
# http://localhost:8000/docs
```

## 開発

### テスト実行

```bash
# 全テスト実行
pytest

# カバレッジ付き
pytest --cov=src tests/
```

### コード品質

```bash
# Linting
flake8 src/
black src/ --check

# フォーマット
black src/
isort src/
```

## ドキュメント

- [プロジェクト設計書](./PROJECT_DESIGN.md)
- [API仕様書](./docs/API.md)（準備中）
- [開発ガイド](./docs/DEVELOPMENT.md)（準備中）

## ライセンス

MIT License

## 貢献

プルリクエスト歓迎！詳細は[CONTRIBUTING.md](./CONTRIBUTING.md)を参照してください。

## 注意事項

- YouTube利用規約を遵守してください
- 著作権を侵害しないよう注意してください
- 生成されたコンテンツは必ず確認してから公開してください
- APIの利用制限に注意してください

## サポート

問題が発生した場合は、[Issues](https://github.com/takezou621/auto-tube/issues)で報告してください。
