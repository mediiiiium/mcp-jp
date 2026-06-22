# harvest-mcp

Harvest MCP サーバー。プロジェクト・時間計測・クライアント・請求書の管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `HARVEST_ACCESS_TOKEN` | ✅ | Harvest Personal Access Token |
| `HARVEST_ACCOUNT_ID` | ✅ | Harvest Account ID |

## 認証情報取得方法

1. Harvest にログイン
2. 右上のアバター → **Developers**
3. **Create new personal access token** をクリック
4. Token name を入力して **Create personal access token** をクリック
5. 発行された Token と Account ID をコピー

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_projects` | プロジェクト一覧を取得する |
| `list_time_entries` | 時間計測エントリー一覧を取得する |
| `create_time_entry` | 新しい時間計測エントリーを作成する |
| `list_clients` | クライアント一覧を取得する |
| `list_invoices` | 請求書一覧を取得する |

## インストール

```bash
cd harvest
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "harvest": {
      "command": "harvest-mcp",
      "env": {
        "HARVEST_ACCESS_TOKEN": "your_harvest_access_token",
        "HARVEST_ACCOUNT_ID": "your_harvest_account_id"
      }
    }
  }
}
```
