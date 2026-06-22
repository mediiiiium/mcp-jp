# cloudflare-mcp

Cloudflare MCP サーバー。DNS・CDN・キャッシュ・アナリティクスの管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `CLOUDFLARE_API_TOKEN` | ✅ | Cloudflare API Token |

## API Token 取得方法

1. Cloudflare ダッシュボードにログイン
2. **My Profile** → **API Tokens** → **Create Token**
3. テンプレートを選択するか **Create Custom Token** をクリック
4. 必要な権限を設定して **Create Token** をクリック

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_zones` | ゾーン（ドメイン）一覧を取得する |
| `list_dns_records` | DNS レコード一覧を取得する |
| `create_dns_record` | DNS レコードを作成する |
| `purge_cache` | ゾーンのキャッシュをパージする |
| `get_zone_analytics` | ゾーンのアクセス統計を取得する |

## インストール

```bash
cd cloudflare
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "cloudflare": {
      "command": "cloudflare-mcp",
      "env": {
        "CLOUDFLARE_API_TOKEN": "your_cloudflare_api_token"
      }
    }
  }
}
```
