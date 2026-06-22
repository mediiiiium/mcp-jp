# brevo-mcp

Brevo（旧 Sendinblue）MCP サーバー。メール送信・コンタクト管理・キャンペーン管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `BREVO_API_KEY` | ✅ | Brevo API キー |

## API キー取得方法

1. Brevo にログイン
2. 右上のアバター → **SMTP & API**
3. **API Keys** タブ → **Generate a new API key** をクリック

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `get_account` | アカウント情報を取得する |
| `send_email` | メールを送信する |
| `list_contacts` | コンタクト一覧を取得する |
| `create_contact` | 新しいコンタクトを作成する |
| `get_email_stats` | メールキャンペーンの統計を取得する |

## インストール

```bash
cd brevo
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "brevo": {
      "command": "brevo-mcp",
      "env": {
        "BREVO_API_KEY": "your_brevo_api_key"  # pragma: allowlist secret
      }
    }
  }
}
```
