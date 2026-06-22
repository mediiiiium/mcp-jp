# confluence-mcp

Confluence MCP サーバー。スペース・ページの管理・検索ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `CONFLUENCE_EMAIL` | ✅ | Atlassian アカウントのメールアドレス |
| `CONFLUENCE_API_TOKEN` | ✅ | Atlassian API トークン |
| `CONFLUENCE_SUBDOMAIN` | ✅ | サブドメイン（例: `mycompany` → `mycompany.atlassian.net`） |

## API トークン取得方法

Jira と同じ Atlassian API トークンを使用できます。

1. [Atlassian API tokens](https://id.atlassian.com/manage-profile/security/api-tokens) にアクセス
2. **Create API token** をクリック
3. Label を入力して **Create** をクリック
4. 発行されたトークンをコピー

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_spaces` | スペース一覧を取得する |
| `search` | CQL でコンテンツを全文検索する |
| `get_page` | ページの詳細を取得する |
| `create_page` | 新しいページを作成する |
| `update_page` | 既存ページを更新する |

## インストール

```bash
cd confluence
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "confluence": {
      "command": "confluence-mcp",
      "env": {
        "CONFLUENCE_EMAIL": "you@example.com",
        "CONFLUENCE_API_TOKEN": "your_api_token_here",
        "CONFLUENCE_SUBDOMAIN": "mycompany"
      }
    }
  }
}
```
