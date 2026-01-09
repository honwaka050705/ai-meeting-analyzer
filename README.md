# AI議事録生成＆タスク抽出ツール

ビジネス会議の議事録から、AIが自動で**要約**と**タスク**を抽出するツールです。

## 🎯 概要

議事録テキストを入力すると、Gemini AIが以下を自動生成します：
- **構造化された要約**（議題・決定事項・課題・その他）
- **タスクリスト**（担当者・内容・期限）

## ✨ 主な機能

| 機能 | 説明 |
|------|------|
| 議事録管理 | 議事録の登録・一覧・詳細・削除 |
| AI要約生成 | セクション＋箇条書き形式で自動要約 |
| タスク自動抽出 | 担当者・内容・期限をJSON形式で抽出 |
| REST API | OpenAPI準拠のAPIを提供 |

## 🛠 技術スタック

| カテゴリ | 技術 |
|----------|------|
| **Backend** | Python 3.10+, FastAPI |
| **Database** | PostgreSQL (pgvector拡張) |
| **AI** | Gemini 2.5 Flash |
| **Infrastructure** | Docker Compose |

## 📁 ディレクトリ構成

```
ai-meeting-assistant/
├── app/
│   ├── main.py              # FastAPIアプリケーション
│   ├── config.py            # 設定管理
│   ├── database.py          # DB接続
│   ├── models/              # SQLAlchemyモデル
│   │   ├── minute.py        # 議事録モデル
│   │   └── task.py          # タスクモデル
│   ├── schemas/             # Pydanticスキーマ
│   ├── routers/             # APIルーティング
│   │   ├── minutes.py       # 議事録API
│   │   ├── tasks.py         # タスクAPI
│   │   └── ai.py            # AI関連API
│   └── services/            # ビジネスロジック
│       ├── ai_service.py    # Gemini API連携
│       ├── minute_service.py
│       └── task_service.py
├── alembic/                 # DBマイグレーション
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

## 🚀 セットアップ

### 1. リポジトリをクローン

```bash
git clone https://github.com/honwaka050705/ai-meeting-analyzer.git
cd ai-meeting-analyzer
```

### 2. 環境変数を設定

```bash
cp .env.example .env
```

`.env`ファイルを編集：

```env
DATABASE_URL=postgresql://postgres:postgres@db:5432/meeting_db
GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL=gemini-2.5-flash
DEBUG=True
```

### 3. Docker Composeで起動

```bash
docker-compose up -d
```

### 4. マイグレーション実行

```bash
docker-compose exec api alembic upgrade head
```

### 5. 動作確認

```bash
# ヘルスチェック
curl http://localhost:8000/health

# API ドキュメント
open http://localhost:8000/docs
```

## 📡 API エンドポイント

### 議事録関連

| Method | Endpoint | 説明 |
|--------|----------|------|
| `POST` | `/api/v1/minutes` | 議事録を新規作成 |
| `GET` | `/api/v1/minutes` | 議事録一覧を取得 |
| `GET` | `/api/v1/minutes/{id}` | 議事録詳細を取得 |
| `DELETE` | `/api/v1/minutes/{id}` | 議事録を削除 |
| `POST` | `/api/v1/minutes/{id}/analyze` | AI分析を実行 |

### タスク関連

| Method | Endpoint | 説明 |
|--------|----------|------|
| `GET` | `/api/v1/tasks` | タスク一覧を取得 |
| `GET` | `/api/v1/tasks/{id}` | タスク詳細を取得 |

## 📝 使用例

### 1. 議事録を登録

```bash
curl -X POST http://localhost:8000/api/v1/minutes \
  -H "Content-Type: application/json" \
  -d '{
    "title": "プロジェクト定例会",
    "content": "【出席者】田中、佐藤、鈴木\n\n田中より、プロジェクトAは予定通り進行中との報告。来週月曜日までに佐藤がデザインカンプを作成する。鈴木は今週金曜までにAPI設計書を完成させる。",
    "meeting_date": "2025-01-15T14:00:00"
  }'
```

### 2. AI分析を実行

```bash
curl -X POST http://localhost:8000/api/v1/minutes/1/analyze
```

### レスポンス例

```json
{
  "minute_id": 1,
  "summary": "## 議題\n- プロジェクトAの進捗確認\n\n## 決定事項\n- デザインカンプを来週月曜までに作成\n- API設計書を今週金曜までに完成\n\n## 課題・懸念点\n- 特になし\n\n## その他\n- 特になし",
  "tasks": [
    {
      "assignee": "佐藤",
      "content": "デザインカンプを作成",
      "due_date": "2025-01-20"
    },
    {
      "assignee": "鈴木",
      "content": "API設計書を完成させる",
      "due_date": "2025-01-17"
    }
  ]
}
```

## 🗄 データベース設計

### Minutesテーブル（議事録）

| カラム | 型 | 説明 |
|--------|------|------|
| id | SERIAL | 主キー |
| title | VARCHAR(255) | 会議タイトル |
| content | TEXT | 議事録本文 |
| meeting_date | TIMESTAMP | 会議日時 |
| summary | TEXT | AI生成の要約 |
| created_at | TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP | 更新日時 |

### Tasksテーブル（タスク）

| カラム | 型 | 説明 |
|--------|------|------|
| id | SERIAL | 主キー |
| minute_id | INTEGER | 議事録ID（FK） |
| assignee | VARCHAR(100) | 担当者 |
| content | TEXT | タスク内容 |
| due_date | DATE | 期限（NULL許可） |
| status | VARCHAR(20) | ステータス |
| created_at | TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP | 更新日時 |

## 🤖 AI機能の詳細

### 要約生成

議事録を以下の構造で要約します：
- **議題**: 会議で話し合われたテーマ
- **決定事項**: 会議で決まったこと
- **課題・懸念点**: 今後の課題や懸念
- **その他**: 次回MTGの日程など

### タスク抽出

以下のルールでタスクを抽出します：
- 明確な担当者が指定されているもののみ抽出
- 期限が明記されている場合は `YYYY-MM-DD` 形式で保存
- 期限が不明な場合は「期限未定」として表示

## 🔧 技術的なポイント

- **FastAPI**: 高速な非同期処理、自動OpenAPIドキュメント生成
- **Pydantic**: 型安全なリクエスト/レスポンス検証
- **SQLAlchemy**: ORMによるDB操作の抽象化
- **Alembic**: DBマイグレーション管理
- **Gemini API**: プロンプトエンジニアリングによる高精度な抽出
- **Docker Compose**: 開発環境の簡単構築


## 📄 ライセンス

MIT License

## 👤 作成者

- GitHub: [@honwaka050705](https://github.com/honwaka050705)
