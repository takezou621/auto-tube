# QMS - Quality Management System

QMSは、品質管理業務を効率化するためのシステムです。このプロジェクトはMVP（Minimum Viable Product）の開発に焦点を当てています。

## 機能概要

- **ユーザー認証**: JWTベースの認証システム
- **品質チェック記録**: 品質チェックの記録・管理
- **検査結果管理**: 検査結果の記録・管理
- **是正処置管理**: 是正処置の記録・管理
- **レポート出力**: 品質レポートの生成・出力

## 技術構成

### バックエンド
- **言語**: Go 1.21
- **フレームワーク**: 標準ライブラリ + Gorilla Mux
- **GraphQL**: gqlgen
- **データベース**: PostgreSQL
- **メッセージキュー**: Kafka
- **ORM**: GORM

### フロントエンド
- **フレームワーク**: Next.js 13
- **言語**: TypeScript
- **スタイリング**: Tailwind CSS
- **GraphQLクライアント**: Apollo Client

## 開発環境セットアップ

### 前提条件
- Docker Desktop
- Go 1.21以上
- Node.js 18以上

### セットアップ手順

1. リポジトリをクローン
```bash
git clone <repository-url>
cd auto-tube
```

2. 依存関係のインストール
```bash
# バックエンド依存関係
cd backend
go mod download

# フロントエンド依存関係
cd ../frontend
npm install
```

3. 開発環境の起動
```bash
# プロジェクトルートで実行
make setup
```

4. マイグレーションの実行
```bash
make migrate
```

### 開発サーバーの起動

バックエンドのみ起動する場合:
```bash
cd backend
go run cmd/main.go
```

フロントエンドのみ起動する場合:
```bash
cd frontend
npm run dev
```

## 開発ルール

このプロジェクトは以下のルールに基づいて開発されています：

- **MVP優先**: 動作する最小限の機能に集中
- **シンプルさ優先**: 複雑な設計よりシンプルな実装を優先
- **ハードコーディング可**: 設定値のハードコーディングを許可
- **手動運用可**: 自動化が複雑な場合は手動運用を許可

## テスト・CI 実行方法

ルートディレクトリで以下のコマンドを利用できます。

```bash
make backend-test   # Poetry で依存を入れた後に pytest を実行
make frontend-test  # pnpm install 後に Vitest を実行
make ci             # 上記をまとめて実行
```

GitHub Actions（`.github/workflows/ci.yaml`）でも `make ci` が走るよう構成しています。手動で安全にコマンドを回したい場合は `ci/ai-safe-run.sh make ci` のようにラッパ経由で実行してください。

詳細な開発ルールは `docs/development-rules.md` を参照してください。

## プロジェクト構造

```
auto-tube/
├── backend/                 # Goバックエンドアプリケーション
│   ├── cmd/                 # メインアプリケーション
│   ├── internal/            # 内部パッケージ
│   │   ├── config/          # 設定管理
│   │   ├── database/        # データベース接続
│   │   ├── handlers/        # HTTPハンドラー
│   │   ├── models/          # データモデル
│   │   ├── repositories/    # データアクセス層
│   │   ├── services/        # ビジネスロジック層
│   │   └── resolvers/       # GraphQLリゾルバー
│   ├── pkg/                 # 共通パッケージ
│   │   ├── middleware/      # ミドルウェア
│   │   └── utils/           # ユーティリティ関数
│   ├── graphql/             # GraphQL関連ファイル
│   └── migrations/          # データベースマイグレーション
├── frontend/                # Next.jsフロントエンドアプリケーション
│   ├── src/
│   │   ├── components/      # Reactコンポーネント
│   │   ├── pages/           # Next.jsページ
│   │   ├── services/        # APIサービス
│   │   └── types/           # TypeScript型定義
│   └── public/              # 静的ファイル
├── docker/                  # Docker関連ファイル
└── docs/                    # ドキュメント
```

## APIドキュメント

GraphQL APIは以下のエンドポイントで利用可能です：

- **GraphQLエンドポイント**: `http://localhost:8080/query`
- **GraphQL Playground**: `http://localhost:8080/playground`

## 環境変数

バックエンドアプリケーションで使用する環境変数：

- `PORT`: サーバーポート（デフォルト: 8080）
- `DATABASE_URL`: データベース接続文字列
- `JWT_SECRET`: JWT署名用の秘密鍵
- `ENVIRONMENT`: 環境設定（development/production）

## 貢献方法

1. Issueを作成する
2. ブランチを作成する（`git checkout -b feature/issue-number`）
3. 変更を実装する
4. テストを実行する
5. Pull Requestを作成する

## ライセンス

このプロジェクトは内部使用のみを目的としています。
