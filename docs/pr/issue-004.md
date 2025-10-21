## Problem
- テスト実行が手動依存で、自動化された品質ゲートが存在しない。
- プロジェクトルートに共通のMakeターゲットがなく、コマンドが人や環境でばらつく。

## Approach
- ルートMakefileを作成し、`backend`/`frontend` ディレクトリでテストを呼び出すターゲットと最終的な `make ci` を定義。
- GitHub Actions (`.github/workflows/ci.yaml`) を追加し、Node 18 / Python 3.11 上で依存関係インストール→テスト実行するジョブを構築。
- `ci/ai-safe-run.sh` の利用例を README か専用ドキュメントに追記し、自動継続運用との整合性を確保。

## Tests
- ローカルで `make ci` を実行
- GitHub Actionsワークフローのdry-run（`act` 無し。設定確認として `yamllint` は任意）

## Risk & Rollback
- Actionsワークフローに不具合があっても削除または`on`トリガをPRに限定することで影響を最小化できる。
- Makefileは個別ファイルのため、問題があれば以前の手動実行に戻すだけで復旧できる。
