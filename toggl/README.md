# toggl-mcp

Toggl Track MCP サーバー。時間計測・プロジェクト・工数管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `TOGGL_API_TOKEN` | ✅ | Toggl Track API トークン |

## API トークン取得方法

1. Toggl Track にログイン
2. 右上のアバター → **Profile Settings**
3. 下部の **API Token** セクションに表示される

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `get_profile` | 現在のユーザープロファイルを取得する |
| `list_workspaces` | ワークスペース一覧を取得する |
| `list_projects` | ワークスペース内のプロジェクト一覧を取得する |
| `list_time_entries` | 時間計測エントリー一覧を取得する |
| `create_time_entry` | 新しい時間計測エントリーを作成する |

## インストール

```bash
cd toggl
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "toggl": {
      "command": "toggl-mcp",
      "env": {
        "TOGGL_API_TOKEN": "your_toggl_api_token"
      }
    }
  }
}
```
