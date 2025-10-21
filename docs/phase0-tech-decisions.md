# Phase 0 技術スタック検討メモ（Issue #15）

## 背景
- 参考とする Zenn 記事では、Gemini API・Claude・Render Cron ジョブを組み合わせた自動動画生成フローが紹介されているが、Gemini TTS はプレビュー扱いで安定性が懸念されると明記されている。[^zenn]
- 本プロジェクトでは不動産投資テーマの動画生成を継続運用するため、音声合成・検索・デプロイ構成を安定化させる必要がある。

## 1. Python 実行環境とパッケージ管理
### 候補比較
- **Poetry**: `pyproject.toml` ベースの依存・スクリプト管理ができ、仮想環境の自動作成やロックファイルを標準サポート。[^poetry]
- **Pipenv**: `Pipfile` 管理だが、メンテナンス頻度の低さと解決アルゴリズムの遅さが指摘されている。[^pipenv]

### 決定
- **Python 3.11 + Poetry** を採用。
  - 3.11 は 3.10 대비で 10〜60% の高速化が実測されており、動画生成用の並列バッチ処理に有利。[^python311]
  - 主要依存（FastAPI、LangChain、Anthropic SDK など）が 3.11 を正式サポート済み。Poetry により CLI・CI で同一環境を再現しやすい。

### リスク・フォロー
- 3.12 以降での追加最適化が必要になった場合、Poetry の `python` 節でマイナーバージョンを引き上げる。ただし 3.12 は一部音声・動画系ライブラリが未対応のため当面 3.11 を維持。

## 2. TTS プロバイダ比較と選定
| 項目 | Gemini TTS (Preview) | Google Cloud Text-to-Speech | ElevenLabs | OpenAI Text-to-Speech |
| --- | --- | --- | --- | --- |
| 対応言語 | 24 言語、プレビュー提供。日本語対応は公式未言及で不確実。[^gemini-tts] | `ja-JP` の Neural2/WaveNet 男性・女性ボイスあり。[^gcp-voices] | 29 言語（日本語含む）。[^11-langs] | 多言語対応。日本語サポートを公式が明示。[^openai-jp] |
| 料金体系 | プレビュー段階で正式料金未提供。呼び出し制限あり。[^gemini-tts] | 音声タイプ別に 100 万文字単位課金（Standard/Neural/WaveNet）。[^gcp-pricing] | 1 文字 = 1 クレジット。月額プラン枠と追加クレジットで柔軟に運用可能。[^11-credit] | `gpt-4o-mini-tts` が $15/100 万文字。入力/出力トークン従量課金。[^openai-pricing] |
| 音質・ボイス | Gemini Flash 音声サンプル提供中。ボイス選択は限定。 | WaveNet/Neural2 で男女 6 パターン。標準的。 | ハイファイ音声とボイスライブラリ豊富。VoiceLab でクローン可。[^11-voices] | 既定 7 ボイス＋ `voices` API で追加取得。ラベルから声質を選別可能。[^openai-voices] |
| 安定性・制限 | Preview。利用規約上の SLA 不明。 | GA。SLA あり。 | 商用利用実績豊富だがクレジット枯渇に注意。 | GA。OpenAI API と同一運用で管理容易。 |

### 決定
- **本番 TTS: ElevenLabs**
  - 日本語の男女ボイスが揃っており、不動産投資チャンネル向けに落ち着いた声色を選択しやすい。
  - クレジット制で 1 文字 = 1 クレジット。プラン枠を超えた場合でも追加クレジット購入で柔軟にスケールできる。[^11-credit]
- **バックアップ案**: Google Cloud Text-to-Speech（WaveNet）
  - API キー切替のみで復旧可能な第二候補として設定。
- **避ける選択**: Gemini TTS（Preview）
  - プレビューで正式料金・SLA が未確定。記事でも安定性への懸念が提示されているため、検証環境に限定。

### 実装メモ
1. ElevenLabs SDK (`elevenlabs==1.x`) を Poetry で追加。
2. Voice ID を環境変数で管理し、男女 2 パターンを切替できるようラッパを実装。
3. フォールバックで Google Cloud TTS を呼び出す抽象化インターフェースを設計。

## 3. Claude API で最新不動産情報を取得する戦略
### オプション比較
- **Claude Web Search ツール**（Anthropic 公式）
  - 1,000 リクエストあたり $10。プロンプト内から直接検索＋引用取得が可能。[^claude-search]
  - Claude を台本生成に使う場合、同一会話で検索→要約→台本生成まで完結可能。
- **Perplexity Sonar API**
  - Web 検索 API が $5/1,000 リクエスト。LLM 併用時は入力/出力トークン課金が別途発生。[^perplexity-pricing][^perplexity-techcrunch]
  - 最新ニュースが豊富だが、Claude とは別の API 認証・課金管理が必要。
- **手動リサーチ（共有スプレッドシート）**
  - コストゼロだが手間がかかり、運用者の負荷が高い。

### 方針
1. **Claude Web Search** を基本とし、動画生成バッチ直前に最新市況を取得。
2. 地域別統計や公式資料が必要な場合は **Perplexity Sonar API** を補助的に利用。
3. 信頼ソースを定期レビューできるよう、週次で spreadsheet に結果リンクを蓄積する運用ルールを設定。

## 4. Web フレームワーク比較
- **Flask**: シンプルだが型サポートが弱く、非同期処理は追加実装が必要。
- **FastAPI**: ASGI・Pydantic・OpenAPI 自動生成を標準搭載し、背景タスク・依存性注入が扱いやすい。[^fastapi]

### 決定
- **FastAPI** を採用。TTS ジョブの非同期実行、認証付き API、Swagger UI による運用確認が実装しやすい。

## 5. Render でのデプロイ構成
- **Web Service (FastAPI)**: API エンドポイントと進捗モニタリングを提供。
- **Background Worker**: 動画生成の重い処理を分離し、Web Service からキュー投入。[^render-worker]
- **Render Cron Job**: 1 日 1 回の定期実行でキュー投入／失敗リカバリを自動化。[^render-cron]
- GitHub Actions からの手動トリガも許容しつつ、Cron 失敗時の再実行を想定して冪等なジョブ設計とする。

## 6. 次アクション
1. `backend/` 直下に FastAPI アプリ雛形と Poetry 設定を作成。
2. ElevenLabs / Google Cloud の API キーを Secrets Manager（Render/CI）に設定。
3. Claude Web Search 利用時の利用規約と目的制限を確認し、プロンプトテンプレートを整備。
4. Render インフラ設定（Web Service + Worker + Cron）を IaC（`render.yaml`）で管理。

---
[^zenn]: https://zenn.dev/xtm_blog/articles/da1eba90525f91
[^poetry]: https://cylab.be/blog/370/poetry-vs-pipenv-which-python-dependency-manager-should-you-use-in-2025
[^pipenv]: https://cylab.be/blog/370/poetry-vs-pipenv-which-python-dependency-manager-should-you-use-in-2025
[^python311]: https://realpython.com/python311-new-features/
[^gemini-tts]: https://ai.google.dev/models/gemini#text_to_speech
[^gcp-voices]: https://cloud.google.com/text-to-speech/docs/voices?hl=en
[^gcp-pricing]: https://cloud.google.com/text-to-speech/docs/pricing?hl=en#prices
[^11-langs]: https://help.elevenlabs.io/hc/en-us/articles/13297718286545-What-languages-are-supported
[^11-credit]: https://help.elevenlabs.io/hc/en-us/articles/12887063755473-How-do-credits-work
[^11-voices]: https://elevenlabs.io/docs/introduction
[^openai-pricing]: https://platform.openai.com/docs/pricing
[^openai-jp]: https://gigazine.net/news/20241023-openai-gpt-4o-mini-tts
[^openai-voices]: https://platform.openai.com/docs/guides/text-to-speech
[^claude-search]: https://techcrunch.com/2025/08/28/anthropic-adds-new-search-and-data-integration-tools-to-claude/
[^perplexity-pricing]: https://docs.perplexity.ai/getting-started/pricing
[^perplexity-techcrunch]: https://techcrunch.com/2025/01/21/perplexity-launches-sonar-an-api-for-ai-search/
[^fastapi]: https://www.imaginarycloud.com/blog/flask-vs-fastapi/
[^render-worker]: https://render.com/docs/background-workers
[^render-cron]: https://render.com/docs/cron-jobs
