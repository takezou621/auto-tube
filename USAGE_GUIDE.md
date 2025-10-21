# Auto-Tube 使い方ガイド

## 目次

1. [セットアップ](#セットアップ)
2. [基本的な使い方](#基本的な使い方)
3. [API使用方法](#api使用方法)
4. [スケジューリング](#スケジューリング)
5. [トラブルシューティング](#トラブルシューティング)

---

## セットアップ

### 1. 環境構築

```bash
# リポジトリのクローン
git clone https://github.com/takezou621/auto-tube.git
cd auto-tube

# 仮想環境の作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt
```

### 2. 環境変数の設定

```bash
# .envファイルを作成
cp .env.example .env

# .envファイルを編集してAPIキーを設定
nano .env
```

必須の環境変数:
- `OPENAI_API_KEY`: OpenAI API キー（スクリプト生成用）
- `NEWS_API_KEY`: NewsAPI キー（ニュース収集用）

推奨の環境変数:
- `ELEVENLABS_API_KEY`: ElevenLabs API キー（高品質音声合成用）
- `YOUTUBE_CLIENT_ID`: YouTube API クライアントID
- `YOUTUBE_CLIENT_SECRET`: YouTube API クライアントシークレット

### 3. データベースの初期化

```bash
# PostgreSQLとRedisを起動
docker-compose up -d postgres redis

# データベースを初期化
python scripts/init_db.py
```

---

## 基本的な使い方

### コマンドラインから動画生成

#### 1. シンプルな動画生成

```bash
python -m src.main
```

デフォルトで「最新テクノロジーニュース」の動画を生成します。

#### 2. トピックを指定して生成

```bash
python -m src.main --topic "AI技術の最新動向"
```

#### 3. カテゴリを指定

```bash
python -m src.main --topic "スタートアップニュース" --category business
```

#### 4. 複数動画の一括生成

```bash
python -m src.main --batch 3
```

#### 5. テストモード（動画生成なし）

```bash
python -m src.main --test
```

トレンド分析のみを実行し、候補トピックを表示します。

---

## API使用方法

### APIサーバーの起動

```bash
# 開発モード
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# または
python -m src.api.main
```

APIドキュメント: http://localhost:8000/docs

### 主要エンドポイント

#### 1. 動画生成リクエスト

```bash
curl -X POST "http://localhost:8000/videos/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AI技術の最新動向",
    "category": "technology",
    "auto_upload": false
  }'
```

#### 2. 動画リスト取得

```bash
curl "http://localhost:8000/videos?limit=10"
```

#### 3. 動画詳細取得

```bash
curl "http://localhost:8000/videos/1"
```

#### 4. 分析データ取得

```bash
curl "http://localhost:8000/analytics/1"
```

#### 5. チャンネル統計

```bash
curl "http://localhost:8000/stats?days=30"
```

#### 6. インサイト取得

```bash
curl "http://localhost:8000/insights"
```

#### 7. トップ動画

```bash
curl "http://localhost:8000/top-videos?limit=5&days=30"
```

---

## スケジューリング

### Celeryを使った自動投稿

#### 1. Celeryワーカーの起動

```bash
# ワーカー起動
celery -A src.scheduler.celery_app worker --loglevel=info

# Beatスケジューラ起動（別ターミナル）
celery -A src.scheduler.celery_app beat --loglevel=info
```

#### 2. Dockerを使った起動

```bash
docker-compose up -d celery-worker celery-beat
```

### デフォルトスケジュール

- **月曜日 20:00**: テクノロジーニュース
- **水曜日 19:00**: ビジネスニュース
- **金曜日 20:00**: テクノロジーニュース
- **日曜日 18:00**: 週間まとめ

### スケジュールのカスタマイズ

`src/scheduler/celery_app.py` の `beat_schedule` を編集:

```python
app.conf.beat_schedule = {
    "my-custom-task": {
        "task": "src.scheduler.tasks.generate_and_upload_video",
        "schedule": crontab(hour=21, minute=0, day_of_week=2),  # 火曜21:00
        "args": ("technology",),
    },
}
```

---

## 高度な使い方

### カスタムパイプライン

```python
from src.pipeline.orchestrator import VideoGenerationPipeline

async def my_custom_pipeline():
    pipeline = VideoGenerationPipeline()

    result = await pipeline.generate_complete_video(
        topic="カスタムトピック",
        category="technology",
        auto_upload=False,
    )

    print(f"Video generated: {result['video_path']}")

# 実行
import asyncio
asyncio.run(my_custom_pipeline())
```

### 個別モジュールの使用

#### ニュース収集のみ

```python
from src.collectors.news_collector import NewsCollector

async def collect_news():
    collector = NewsCollector()
    articles = await collector.collect_tech_news(max_results=10)

    for article in articles:
        print(f"- {article.title}")

asyncio.run(collect_news())
```

#### トレンド分析のみ

```python
from src.analyzers.trend_analyzer import TrendAnalyzer

async def analyze_trends():
    analyzer = TrendAnalyzer()

    keywords = ["AI", "機械学習", "ChatGPT"]
    trends = await analyzer.get_google_trends(keywords)

    print(trends)

asyncio.run(analyze_trends())
```

---

## トラブルシューティング

### よくある問題

#### 1. API キーエラー

**エラー**: `OpenAI API key not configured`

**解決策**: `.env` ファイルに `OPENAI_API_KEY` を設定

```bash
OPENAI_API_KEY=sk-your-key-here
```

#### 2. データベース接続エラー

**エラー**: `Connection refused`

**解決策**: PostgreSQLとRedisが起動しているか確認

```bash
docker-compose up -d postgres redis
```

#### 3. FFmpeg not found

**エラー**: `ffmpeg: command not found`

**解決策**: FFmpegをインストール

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# https://ffmpeg.org/download.html からダウンロード
```

#### 4. MoviePy エラー

**エラー**: `ModuleNotFoundError: No module named 'moviepy'`

**解決策**: 依存関係を再インストール

```bash
pip install -r requirements.txt
```

#### 5. YouTube アップロードエラー

**エラー**: `YouTube client not initialized`

**解決策**:
1. Google Cloud Consoleで YouTube Data API v3を有効化
2. OAuth 2.0クライアントIDを作成
3. `.env` に認証情報を設定
4. `uploader.authenticate()` を実行

---

## パフォーマンス最適化

### 1. キャッシュの活用

- 画像やニュースデータは `data/cache/` にキャッシュされます
- 定期的にクリーンアップタスクが実行されます

### 2. 並列処理

複数動画を並列生成:

```bash
# 3つの動画を順次生成
python -m src.main --batch 3
```

### 3. リソース管理

- `settings.openai_rpm`: OpenAI API レート制限
- `settings.elevenlabs_character_limit`: ElevenLabs 文字数制限

---

## セキュリティのベストプラクティス

1. **APIキーの管理**
   - `.env` ファイルをgitignoreに追加済み
   - 環境変数として管理

2. **YouTube認証**
   - OAuth 2.0トークンは `config/youtube_credentials.json` に保存
   - このファイルもgitignoreに追加

3. **データベース**
   - 本番環境では強力なパスワードを使用
   - `.env` の `DATABASE_URL` を更新

---

## モニタリングとログ

### ログの確認

```bash
# リアルタイムログ
tail -f logs/autotube_$(date +%Y-%m-%d).log

# エラーログのみ
tail -f logs/autotube_errors_$(date +%Y-%m-% d).log
```

### 分析ダッシュボード

APIの `/stats` と `/insights` エンドポイントで確認:

```bash
curl http://localhost:8000/stats
curl http://localhost:8000/insights
```

---

## さらなるカスタマイズ

### 動画スタイルの変更

`src/video/editor.py` でイントロ/アウトロをカスタマイズ

### サムネイルテンプレート

`src/thumbnail/generator.py` で新しいテンプレートを追加

### SEO戦略

`src/seo/optimizer.py` でタイトル・説明文の生成ロジックを調整

---

## サポート

問題が解決しない場合:

1. [GitHub Issues](https://github.com/takezou621/auto-tube/issues) で報告
2. ログファイルを添付
3. 実行環境の情報を提供（OS、Pythonバージョン等）

---

**Happy Auto-Tubing! 🎬🤖**
