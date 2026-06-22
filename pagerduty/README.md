# pagerduty-mcp

PagerDuty MCP サーバー。インシデント・サービス・オンコールの管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `PAGERDUTY_API_TOKEN` | ✅ | PagerDuty API トークン（User API Key または Account API Key） |

## API トークン取得方法

1. PagerDuty にログイン
2. 右上のアバター → **My Profile**
3. **User Settings** タブ → **Create API User Token** をクリック
4. 発行されたトークンをコピー

アカウント全体のトークンは：**Integrations** → **API Access Keys** → **Create New API Key**

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_incidents` | インシデント一覧を取得する |
| `get_incident` | インシデントの詳細を取得する |
| `create_incident` | 新しいインシデントを作成する |
| `list_services` | サービス一覧を取得する |
| `list_oncalls` | 現在オンコール中のユーザー一覧を取得する |

## インストール

```bash
cd pagerduty
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "pagerduty": {
      "command": "pagerduty-mcp",
      "env": {
        "PAGERDUTY_API_TOKEN": "your_pagerduty_api_token"
      }
    }
  }
}
```
