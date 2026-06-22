# sentry-mcp

Sentry MCP サーバー。エラートラッキング・イシュー管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `SENTRY_AUTH_TOKEN` | ✅ | Sentry Auth Token |
| `SENTRY_ORG` | ✅ | 組織スラッグ（Organization slug） |

## Auth Token 取得方法

1. Sentry にログイン
2. **Settings** → **Auth Tokens** → **Create New Token**
3. スコープを設定して **Create Token** をクリック

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_projects` | プロジェクト一覧を取得する |
| `list_issues` | イシュー（エラー）一覧を取得する |
| `get_issue` | イシューの詳細を取得する |
| `update_issue` | イシューのステータスを更新する |
| `list_events` | イシューに関連するイベント一覧を取得する |

## インストール

```bash
cd sentry
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "sentry": {
      "command": "sentry-mcp",
      "env": {
        "SENTRY_AUTH_TOKEN": "your_sentry_auth_token",
        "SENTRY_ORG": "my-organization"
      }
    }
  }
}
```
