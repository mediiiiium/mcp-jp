# mailchimp-mcp

Mailchimp MCP サーバー。オーディエンス（メーリングリスト）・キャンペーンの管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `MAILCHIMP_API_KEY` | ✅ | Mailchimp API キー（末尾に `-us1` などのサーバープレフィックスが付く） |
| `MAILCHIMP_SERVER_PREFIX` | | サーバープレフィックス（省略時は API キーから自動抽出） |

## API キー取得方法

1. Mailchimp にログイン
2. 右上のアバター → **Account & billing**
3. **Extras** → **API keys**
4. **Create A Key** をクリック

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `get_account_info` | アカウント情報を取得する |
| `list_audiences` | オーディエンス一覧を取得する |
| `list_members` | オーディエンスのメンバー一覧を取得する |
| `add_member` | オーディエンスにメンバーを追加する |
| `list_campaigns` | キャンペーン一覧を取得する |

## インストール

```bash
cd mailchimp
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "mailchimp": {
      "command": "mailchimp-mcp",
      "env": {
        "MAILCHIMP_API_KEY": "your_mailchimp_api_key"  # pragma: allowlist secret
      }
    }
  }
}
```
