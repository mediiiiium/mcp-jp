# vercel-mcp

Vercel MCP サーバー。プロジェクト・デプロイメント・ドメインの管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `VERCEL_ACCESS_TOKEN` | ✅ | Vercel Access Token |

## Access Token 取得方法

1. Vercel にログイン
2. 右上のアバター → **Settings** → **Tokens**
3. **Create** → Token name を入力して **Create Token** をクリック

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_projects` | プロジェクト一覧を取得する |
| `get_project` | プロジェクトの詳細を取得する |
| `list_deployments` | デプロイメント一覧を取得する |
| `get_deployment` | デプロイメントの詳細を取得する |
| `list_domains` | ドメイン一覧を取得する |

## インストール

```bash
cd vercel
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "vercel": {
      "command": "vercel-mcp",
      "env": {
        "VERCEL_ACCESS_TOKEN": "your_vercel_access_token"
      }
    }
  }
}
```
