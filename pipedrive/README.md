# pipedrive-mcp

Pipedrive MCP サーバー。コンタクト・案件・アクティビティの管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `PIPEDRIVE_API_TOKEN` | ✅ | Pipedrive API トークン |

## API トークン取得方法

1. Pipedrive にログイン
2. 右上のアバター → **Personal preferences**
3. **API** タブを選択
4. **Your personal API token** をコピー

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_persons` | 人物（コンタクト）一覧を取得する |
| `search_persons` | 名前・メールで人物を検索する |
| `list_deals` | 案件（Deal）一覧を取得する |
| `create_deal` | 新しい案件を作成する |
| `list_activities` | アクティビティ（商談活動）一覧を取得する |

## インストール

```bash
cd pipedrive
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "pipedrive": {
      "command": "pipedrive-mcp",
      "env": {
        "PIPEDRIVE_API_TOKEN": "your_pipedrive_api_token"
      }
    }
  }
}
```
