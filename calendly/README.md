# calendly-mcp

Calendly MCP サーバー。スケジュール調整・予約管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `CALENDLY_ACCESS_TOKEN` | ✅ | Calendly Personal Access Token |

## トークン取得方法

1. Calendly にログイン
2. 右上のアバター → **Integrations & apps** → **API & Webhooks**
3. **Generate New Token** をクリック
4. Token name を入力して **Create Token** をクリック

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `get_current_user` | 現在のユーザー情報を取得する |
| `list_event_types` | イベントタイプ（予約ページ）一覧を取得する |
| `list_scheduled_events` | スケジュール済みイベント一覧を取得する |
| `get_event` | イベントの詳細を取得する |
| `list_invitees` | イベントの招待者一覧を取得する |

## インストール

```bash
cd calendly
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "calendly": {
      "command": "calendly-mcp",
      "env": {
        "CALENDLY_ACCESS_TOKEN": "your_calendly_access_token"
      }
    }
  }
}
```
