# jira-mcp

Jira MCP サーバー。プロジェクト・イシューの管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `JIRA_EMAIL` | ✅ | Atlassian アカウントのメールアドレス |
| `JIRA_API_TOKEN` | ✅ | Atlassian API トークン |
| `JIRA_SUBDOMAIN` | ✅ | サブドメイン（例: `mycompany` → `mycompany.atlassian.net`） |

## トークン取得方法

1. [Atlassian API tokens](https://id.atlassian.com/manage-profile/security/api-tokens) にアクセス
2. **Create API token** をクリック
3. Label を入力して **Create** をクリック
4. 発行されたトークンをコピー

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_projects` | プロジェクト一覧を取得する |
| `search_issues` | JQL でイシューを検索する |
| `get_issue` | イシューの詳細を取得する |
| `create_issue` | 新しいイシューを作成する |
| `update_issue` | イシューを更新する（ステータス変更含む） |

## インストール

```bash
cd jira
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "jira": {
      "command": "jira-mcp",
      "env": {
        "JIRA_EMAIL": "you@example.com",
        "JIRA_API_TOKEN": "your_api_token_here",
        "JIRA_SUBDOMAIN": "mycompany"
      }
    }
  }
}
```
