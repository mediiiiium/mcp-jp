# datadog-mcp

Datadog MCP サーバー。モニター・ダッシュボード・メトリクス・イベントの管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `DATADOG_API_KEY` | ✅ | Datadog API キー |
| `DATADOG_APP_KEY` | ✅ | Datadog Application キー |
| `DATADOG_SITE` | | Datadog サイト（デフォルト: `datadoghq.com`、日本は `ap1.datadoghq.com` など） |

## API キー取得方法

1. Datadog にログイン
2. **Organization Settings** → **API Keys** → **New Key** をクリック
3. 同様に **Application Keys** → **New Key** でアプリケーションキーも作成

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_monitors` | モニター一覧を取得する |
| `get_monitor` | モニターの詳細を取得する |
| `list_dashboards` | ダッシュボード一覧を取得する |
| `query_metrics` | メトリクスデータをクエリする |
| `list_events` | イベント一覧を取得する |

## インストール

```bash
cd datadog
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "datadog": {
      "command": "datadog-mcp",
      "env": {
        "DATADOG_API_KEY": "your_datadog_api_key",  # pragma: allowlist secret
        "DATADOG_APP_KEY": "your_datadog_app_key"  # pragma: allowlist secret
      }
    }
  }
}
```
