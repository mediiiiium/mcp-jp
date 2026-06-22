# notion-mcp

Notion（ナレッジ管理・プロジェクト管理）の MCP サーバー。ページ・データベースの検索・閲覧・作成を AI から操作できます。

## セットアップ

```bash
cd notion
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `NOTION_API_TOKEN` | Notion Internal Integration トークン |

### APIトークンの取得

1. [Notion Integrations](https://www.notion.so/my-integrations) にアクセス
2. 「+ 新しいインテグレーション」を作成
3. 発行されたシークレットをコピー
4. 連携したいページ/DBを開き「...」→「コネクト先」→作成したインテグレーションを追加

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "notion": {
      "command": "notion-mcp",
      "env": {
        "NOTION_API_TOKEN": "your_integration_token_here"
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `search` | ページ・データベースをキーワードで検索 |
| `get_page` | ページIDを指定してページ情報を取得 |
| `get_page_content` | ページのブロック（本文）を取得 |
| `query_database` | データベースのレコードを取得・フィルタリング |
| `create_page` | ページまたはDBレコードを作成 |

## 使用例

```
「プロジェクト計画」という名前のページを検索して
```

```
ページID abc123 の内容を教えて
```

```
タスク管理DBから未完了のタスクを取得して
```

```
議事録フォルダに「2024年1月MTG議事録」ページを作成して
```

```
プロジェクトDBに新しいレコード「新機能開発」を追加して
```
