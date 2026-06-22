# shopify-mcp

Shopify MCP サーバー。商品・注文・顧客の管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `SHOPIFY_ACCESS_TOKEN` | ✅ | Shopify Admin API アクセストークン |
| `SHOPIFY_STORE` | ✅ | ストアのサブドメイン（例: `mystore` → `mystore.myshopify.com`） |

## アクセストークン取得方法

1. Shopify 管理画面にログイン
2. **設定** → **アプリと販売チャネル** → **アプリを開発する**
3. **アプリを作成** → アプリ名を入力
4. **Admin API スコープを設定** → 必要な権限にチェック
5. **アプリをインストール** → Admin API アクセストークンをコピー

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_products` | 商品一覧を取得する |
| `list_orders` | 注文一覧を取得する |
| `get_order` | 注文の詳細を取得する |
| `list_customers` | 顧客一覧を取得する |
| `get_customer` | 顧客の詳細を取得する |

## インストール

```bash
cd shopify
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "shopify": {
      "command": "shopify-mcp",
      "env": {
        "SHOPIFY_ACCESS_TOKEN": "your_shopify_access_token",
        "SHOPIFY_STORE": "mystore"
      }
    }
  }
}
```
