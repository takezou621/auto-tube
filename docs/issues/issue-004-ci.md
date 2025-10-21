# Issue #4: CIパイプライン整備

## Problem
- 手動で `poetry run pytest` や `pnpm test` を実行しており、回帰検知が不十分。
- MakefileやCIスクリプトが存在せず、開発者やエージェントの統一的な実行手順が曖昧。
- 将来的なAuto-Continue/自動検証フローに備えた安全なコマンドラッパが整っていない。

## Goal
1. ルートMakefileに `make backend-test` / `make frontend-test` / `make ci` を用意し、CIで共通実行できるようにする。
2. GitHub Actionsワークフローを追加し、push/PR時にバックエンド・フロントエンドのテストが実行される。
3. `ci/ai-safe-run.sh` を活用した安全なコマンド実行例をドキュメント化する（必要ならテンプレスクリプトを配置）。

## Constraints
- Actions では Node.js 18 / Python 3.11 を使用し、`poetry install --no-root` と `pnpm install --frozen-lockfile` を使う。
- 将来的にPlanetScaleなどの外部サービスを扱う際に拡張しやすい構成にする。
- ワークフローは10分以内で終わることを意識し、特別なキャッシュ設定が不要なシンプルな形から始める。
