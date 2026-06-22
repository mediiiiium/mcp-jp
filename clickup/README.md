# clickup-mcp

ClickUp MCP サーバー。チーム・スペース・リスト・タスクの管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `CLICKUP_API_TOKEN` | ✅ | ClickUp Personal API Token |

## API トークン取得方法

1. ClickUp にログイン
2. 右上のアバター → **Settings**
3. **Apps** → **API Token** セクション → **Generate** をクリック

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `get_teams` | チーム（ワークスペース）一覧を取得する |
| `list_spaces` | チーム内のスペース一覧を取得する |
| `list_lists` | スペース内のリスト一覧を取得する |
| `list_tasks` | リスト内のタスク一覧を取得する |
| `create_task` | 新しいタスクを作成する |

## インストール

```bash
cd clickup
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "clickup": {
      "command": "clickup-mcp",
      "env": {
        "CLICKUP_API_TOKEN": "your_clickup_api_token"
      }
    }
  }
}
```
