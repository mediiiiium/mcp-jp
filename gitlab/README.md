# gitlab-mcp

GitLab MCP サーバー。プロジェクト・イシュー・マージリクエストの管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `GITLAB_ACCESS_TOKEN` | ✅ | Personal Access Token（`api` スコープが必要） |
| `GITLAB_BASE_URL` | | API ベース URL（デフォルト: `https://gitlab.com/api/v4`、セルフホスト時に変更） |

## トークン取得方法

1. GitLab にログイン
2. 右上のアバター → **Edit profile** → 左サイドバー **Access Tokens**
3. **Add new token** → Token name 入力 → Scopes で `api` にチェック
4. **Create personal access token** をクリックして発行

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_projects` | プロジェクト一覧を取得する |
| `list_issues` | プロジェクトのイシュー一覧を取得する |
| `get_issue` | イシューの詳細を取得する |
| `create_issue` | 新しいイシューを作成する |
| `list_merge_requests` | マージリクエスト一覧を取得する |

## インストール

```bash
cd gitlab
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "gitlab": {
      "command": "gitlab-mcp",
      "env": {
        "GITLAB_ACCESS_TOKEN": "your_access_token_here"
      }
    }
  }
}
```

セルフホスト GitLab の場合:

```json
{
  "mcpServers": {
    "gitlab": {
      "command": "gitlab-mcp",
      "env": {
        "GITLAB_ACCESS_TOKEN": "your_access_token_here",
        "GITLAB_BASE_URL": "https://gitlab.your-company.com/api/v4"
      }
    }
  }
}
```
