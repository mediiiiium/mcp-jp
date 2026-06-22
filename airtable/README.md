# airtable-mcp

Airtable（スプレッドシート型データベース）の MCP サーバー。テーブルのレコード管理を AI から操作できます。

## セットアップ

```bash
cd airtable
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `AIRTABLE_API_TOKEN` | Airtable パーソナルアクセストークン |

### APIトークンの取得

1. [Airtable Account](https://airtable.com/account) にアクセス
2. 「API」→「Create personal access token」
3. スコープ: `data.records:read`, `data.records:write`, `schema.bases:read` を付与

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "airtable": {
      "command": "airtable-mcp",
      "env": {
        "AIRTABLE_API_TOKEN": "your_personal_access_token_here"
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_bases` | アクセス可能なベース一覧を取得 |
| `list_records` | テーブルのレコード一覧を取得（フィルター・ソート可） |
| `get_record` | レコードIDを指定して詳細を取得 |
| `create_record` | 新しいレコードを作成 |
| `update_record` | 既存レコードを更新 |

## 使用例

```
アクセスできるベース一覧を見せて
```

```
タスク管理テーブルのレコードを全部見せて
```

```
ステータスが「進行中」のタスクを検索して
```

```
タスクテーブルに「新機能開発」というレコードを追加して
```

```
レコード recXXXXX のステータスを「完了」に更新して
```
