## Problem
- 台本生成フローのみで音声合成が欠落し、AutoTubeの価値提案が未完成だった。
- ElevenLabs APIキー未設定時にランタイムエラーとなり、開発環境での検証手段がなかった。

## Approach
- `POST /api/projects/{id}/tts` を追加し、テンプレート台本→`TTSRequest`→`StreamingResponse` のパイプラインを構築。
- `enable_tts_mock` 設定を導入し、モック音声での疎通確認と503エラー分岐を実装。
- フロントエンドに音声生成ボタン・再生/ダウンロードUI・エラー表示を追加し、サービス層でBlobレスポンスを扱うヘルパーを実装。
- FastAPIのAPIテストとVitestのユーティリティテストを拡充し、音声生成成功・未設定・プロバイダエラーを網羅。

## Tests
- `cd backend && poetry run pytest`
- `cd frontend && pnpm test`

## Risk & Rollback
- ElevenLabs呼び出しで例外が多発する場合、`enable_tts_mock` を有効化することで即時にモックへ切り替え可能。
- 影響範囲は `/api/projects` 系とフロントトップページのみ。問題発生時は該当ファイル（`app/api/projects.py`, `services/tts/usecase.py`, `frontend/src/pages/index.tsx`, `frontend/src/services/projects.ts`）を巻き戻す。
