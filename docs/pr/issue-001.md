## Problem
- 動画スクリプト生成APIが存在せず、フロントエンドからAutoTubeのユースケースを操作できない。
- UIがQMS向けのダミー状態で、投資家向けプロジェクト入力や生成結果の確認ができない。

## Approach
- FastAPIに `/api/projects/` (POST/GET) を追加し、テンプレートベースで台本・シーン情報を生成するサービス層を実装。
- 生成結果を保持するインメモリストアとPydanticレスポンスを新設し、ユニットテストを整備。
- フロントエンドをAutoTube仕様のフォーム/UIに刷新し、API呼び出しをラップするサービスモジュールとVitestによる最小テストを追加。
- プロダクト全体の優先課題を `docs/product-roadmap.md` と Issue ドキュメントで整理し、今後の開発指針を明文化。

## Tests
- `cd backend && poetry run pytest`
- `cd frontend && pnpm test`

## Risk & Rollback
- ElevenLabs連携など未着手機能は今後のIssueに切り分け済み。現状はテンプレート生成のみのため外部依存はない。
- 問題発生時は `backend/app/api/projects.py` と `frontend/src/pages/index.tsx` の差分を巻き戻すことで旧ダミー状態へ戻せる。
