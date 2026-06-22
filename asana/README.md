# asana-mcp

Asana MCP サーバー。ワークスペース・プロジェクト・タスクの管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `ASANA_ACCESS_TOKEN` | ✅ | Personal Access Token |

## トークン取得方法

1. [Asana Developer Console](https://app.asana.com/0/my-apps) にアクセス
2. **Create new token** をクリック
3. Token name を入力して **Create token** をクリック
4. 発行されたトークンをコピー

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_workspaces` | ワークスペース一覧を取得する |
| `list_projects` | ワークスペース内のプロジェクト一覧を取得する |
| `list_tasks` | プロジェクト内のタスク一覧を取得する |
| `get_task` | タスクの詳細を取得する |
| `create_task` | 新しいタスクを作成する |

## インストール

```bash
cd asana
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "asana": {
      "command": "asana-mcp",
      "env": {
        "ASANA_ACCESS_TOKEN": "your_access_token_here"
      }
    }
  }
}
```
