# yappli-crm-mcp

Yappli CRM（モバイルアプリ向けノーコードCRM・会員管理）の MCP サーバー。公式 MCP 未提供。

## セットアップ

```bash
cd yappli-crm
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `YAPPLI_CRM_APP_URL` | Yappli CRM のアプリURL（例: `https://your-app.yappli.co`） |
| `YAPPLI_CRM_CLIENT_ID` | 管理画面で発行したOAuth クライアントID |
| `YAPPLI_CRM_CLIENT_SECRET` | 管理画面で発行したOAuth クライアントシークレット |  # pragma: allowlist secret

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "yappli-crm": {
      "command": "yappli-crm-mcp",
      "env": {
        "YAPPLI_CRM_APP_URL": "https://your-app.yappli.co",
        "YAPPLI_CRM_CLIENT_ID": "your_client_id",
        "YAPPLI_CRM_CLIENT_SECRET": "your_client_secret_here"  # pragma: allowlist secret
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_users` | CRMユーザー（会員）一覧を取得する |
| `get_user` | 会員IDで特定のユーザー情報を取得する |
| `create_user` | 新規会員を登録する |
| `get_user_points` | 会員のポイント付与・利用履歴を取得する |
| `add_user_points` | 会員にポイントを付与または減算する |

## 使用例

```
会員一覧を取得して
```

```
会員ID user_001 のポイント履歴を見せて
```

```
会員ID user_001 に500ポイントを付与して、理由は「誕生日ポイント」
```

```
メールアドレス test@example.com で新規会員を登録して
```
