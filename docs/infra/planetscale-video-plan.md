# 永続化と動画レンダリング方針

## 1. PlanetScale 永続化計画
- **技術選定**: PlanetScale (MySQL 互換) + Prisma を前提。バックエンドは FastAPI だが、Prisma Client Python を利用。
- **スキーマ草案**:
  - `projects`: id(UUID), created_at, title, location, highlight, audience, duration, tone, call_to_action, summary
  - `project_sections`: project_id, order_index, title, body
  - `project_scenes`: project_id, order_index, cue, description
  - `project_storyboards`: project_id, order_index, shot_type, broll_idea, key_message, overlay_text
- **抽象化**:
  - 現行の `projects_store` を `ProjectRepository` インターフェースに置き換え、JSON実装とDB実装を切り替え可能に。
  - `ProjectRepository` に `create`, `get`, `list`, `reset` を定義。
- **移行手順**:
  1. Prisma スキーマ定義 (`prisma/schema.prisma`)
  2. PlanetScale ブランチ接続（アクセストークン）
  3. マイグレーション → Prisma Client 生成
  4. `ProjectRepository` DB 実装を FastAPI に組み込み、設定でJSON/DB切替。

## 2. 動画レンダリングワークフロー試作
- **目的**: 台本 + ストーリーボード + 音声から自動で動画ファイルを生成するパイプラインの叩き台を作る。
- **構成案**:
  - Render (Web Service + Background Worker) / Railway などのサーバレスワーカー。
  - Worker はキュー (PlanetScale / Redis / SQS) 経由で `project_id` を受け取り、FFmpeg + 画像素材 + 音声合成結果を組み合わせて動画mp4を生成。
  - 生成成果物は S3 / Cloudflare R2 等にアップロードし、URLをDBに保存。
- **API案**:
  - `POST /api/projects/{id}/render` → キュー投入、ジョブIDを返す。
  - `GET /api/render-jobs/{job_id}` → ステータスと完了時の動画URLを返す。
- **試作内容**:
  - ローカルでは `ffmpeg` を利用したCLIスクリプト（例: `scripts/render_project.py`）。
  - モックとして、ストーリーボードの B-roll 案に合わせたプレースホルダー画像＋音声(TTS)を結合。

## 3. CI/CD/Auto-Continue 考慮
- PlanetScale 接続情報は GitHub Actions のシークレットに格納。
- マイグレーションは `make db-migrate` / `make db-seed` を追加。
- Auto-Continue での安全性確保のため、`ci/ai-safe-run.sh` 経由で `make db-test` などを実行。

---
次ステップ: `ProjectRepository` インターフェース作成、JSON実装をリファクタ後、DB実装のひな形を追加する。
