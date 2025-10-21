## Problem
- JSON永続化だけではスケールや信頼性が不足し、PlanetScale移行計画が必要。
- 動画レンダリングを含む最終成果物生成フローが未整備で、プロダクト完成までのギャップが大きい。

## Approach
- `project_repository` を導入し、JSONリポジトリを抽象化して後続でPlanetScale実装に差し替え可能にした。
- docs/infra に PlanetScale + Prisma を前提としたスキーマ案と動画レンダリングパイプラインの設計メモを追加。
- Auto-Continue 環境でのリポジトリ初期化を考慮し、テスト用フィクスチャでリポジトリキャッシュをクリアする運用を採用。

## Tests
- `cd backend && poetry run pytest`
- `cd frontend && pnpm test`
- `cd backend && poetry run yamllint ../.github/workflows/ci.yaml`

## Risk & Rollback
- 新リポジトリ層は旧APIをラップしており、問題発生時は `app/services/project_repository.py` を差し戻すことで元のJSON実装のみの状態に戻せる。
- PlanetScale実装はまだ導入していないため、現行動作に影響は限定的。今後のDB接続テストで問題が出た場合はJSON実装にフォールバックできる。
