## Problem
- 映像制作の指針が無く、台本と音声だけでは動画の画作りに悩む。
- 過去生成したプロジェクトでも、どのシーンでどの映像を挿入すべきか記録されていない。

## Approach
- `storyboard_generator` を追加し、各シーン向けにショットタイプ/B-roll/テロップ案をテンプレートで生成。
- `/api/projects/{id}/storyboard` エンドポイントを実装し、PydanticレスポンスでUIに渡せるよう整形。
- フロントエンドでストーリーボード表示用APIを追加し、「ステップ6: ストーリーボード」セクションを実装。
- Vitest と Pytest にテストを追加し、API成功・404ケース、フロント側の変換ロジックを検証。

## Tests
- `cd backend && poetry run pytest`
- `cd frontend && pnpm test`

## Risk & Rollback
- ストーリーボードはテンプレ生成のため、品質調整はテンプレ文字列の見直しで容易にロールバック可能。
- UIは追加セクションのみ。問題があれば `frontend/src/pages/index.tsx` の該当ブロックを削除することで元に戻せる。
