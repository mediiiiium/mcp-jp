# freshdesk-mcp

Freshdesk MCP サーバー。チケット・コンタクトの管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `FRESHDESK_API_KEY` | ✅ | Freshdesk API キー |
| `FRESHDESK_SUBDOMAIN` | ✅ | サブドメイン（例: `mycompany` → `mycompany.freshdesk.com`） |

## API キー取得方法

1. Freshdesk にログイン
2. 右上のプロフィールアイコン → **Profile Settings**
3. ページ右側に **Your API Key** が表示される

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_tickets` | チケット一覧を取得する |
| `get_ticket` | チケットの詳細を取得する |
| `create_ticket` | 新しいチケットを作成する |
| `list_contacts` | コンタクト（顧客）一覧を取得する |
| `get_contact` | コンタクトの詳細を取得する |

## ステータス・優先度の値

**ステータス**: 2=Open, 3=Pending, 4=Resolved, 5=Closed

**優先度**: 1=Low, 2=Medium, 3=High, 4=Urgent

## インストール

```bash
cd freshdesk
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "freshdesk": {
      "command": "freshdesk-mcp",
      "env": {
        "FRESHDESK_API_KEY": "your_freshdesk_api_key",  # pragma: allowlist secret
        "FRESHDESK_SUBDOMAIN": "mycompany"
      }
    }
  }
}
```
