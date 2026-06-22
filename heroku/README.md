# heroku-mcp

Heroku MCP サーバー。アプリ・ダイノ・アドオンの管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `HEROKU_API_TOKEN` | ✅ | Heroku API Token |

## API Token 取得方法

1. Heroku にログイン
2. **Account settings** → **Applications** → **Authorizations** → **Create authorization**
3. Description を入力して **Create** をクリック

または CLI で: `heroku auth:token`

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_apps` | アプリ一覧を取得する |
| `get_app` | アプリの詳細を取得する |
| `list_dynos` | ダイノ（実行インスタンス）一覧を取得する |
| `list_addons` | アドオン一覧を取得する |
| `get_account` | アカウント情報を取得する |

## インストール

```bash
cd heroku
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "heroku": {
      "command": "heroku-mcp",
      "env": {
        "HEROKU_API_TOKEN": "your_heroku_api_token"
      }
    }
  }
}
```
