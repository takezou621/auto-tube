## Problem
- プロジェクト履歴がメモリオンリーのため、再起動や多人数運用時に情報が消えてしまう。
- UIから過去生成分を呼び出す導線がなく、動画制作の再利用効率が低い。

## Approach
- `Settings` に `projects_store_path` を追加し、`projects_store` をJSONベースの永続化層へ置き換え。作成時に書き込み、一覧・取得時はファイルから再読込できるようにする。
- `/api/projects` に GET を追加して履歴一覧を返却し、`ProjectResponse` を再利用して整形。
- フロントサービスに `fetchProjects` を追加し、フォーム右カラムに「ステップ5: 生成履歴」を新設。履歴項目から即座に台本を再表示できるようにし、VitestでAPI成功/失敗パターンを検証。
- Pytest では永続化ファイルをテストごとに分離する autouse fixture を追加し、一覧APIの正常系・永続性・空状態のケースを網羅する。

## Tests
- `cd backend && poetry run pytest`
- `cd frontend && pnpm test`

## Risk & Rollback
- JSONファイルが壊れた場合は削除して再生成すれば復旧可能。`projects_store.reset_store(delete_file=True)` でクリーン状態へ戻せる。
- フロントの履歴UIに不具合が出た場合、`frontend/src/pages/index.tsx` と `frontend/src/services/projects.ts` の変更をリバートすれば以前の挙動へ戻せる。
