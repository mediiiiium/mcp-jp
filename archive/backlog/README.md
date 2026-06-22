# backlog-mcp

Backlog（プロジェクト管理・課題追跡）の MCP サーバー。課題の検索・作成・コメント追加を AI から操作できます。

## セットアップ

```bash
cd backlog
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `BACKLOG_API_KEY` | Backlog API キー（個人設定から取得） |
| `BACKLOG_SPACE` | スペースキー（URLの `xxxx.backlog.jp` の `xxxx` 部分） |
| `BACKLOG_DOMAIN` | ドメイン（`backlog.jp` または `backlog.com`、デフォルト: `backlog.jp`） |

### APIキーの取得

1. Backlog にログイン
2. 個人設定 → API → 「APIキーを登録する」で発行

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "backlog": {
      "command": "backlog-mcp",
      "env": {
        "BACKLOG_API_KEY": "your_api_key_here",
        "BACKLOG_SPACE": "your-space-name"
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_projects` | プロジェクト一覧を取得 |
| `list_issues` | 課題一覧を取得（プロジェクト・担当者・ステータス・キーワードで絞り込み可） |
| `get_issue` | 課題の詳細情報を取得 |
| `create_issue` | 新しい課題を作成 |
| `add_issue_comment` | 課題にコメントを追加 |

## 使用例

```
プロジェクト一覧を見せて
```

```
未対応のバグ課題をすべて表示して
```

```
課題 PROJECT-123 の詳細を見せて
```

```
「ログイン画面のボタンが動かない」という優先度高の課題を作って
```

```
課題 PROJECT-456 に「確認しました。明日対応します」とコメントして
```
