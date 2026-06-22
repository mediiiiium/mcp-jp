# square-mcp

Square MCP サーバー。店舗・顧客・決済・注文の管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `SQUARE_ACCESS_TOKEN` | ✅ | Square アクセストークン |

## アクセストークン取得方法

1. [Square Developer](https://developer.squareup.com/) にアクセス
2. **Applications** → アプリを作成（または選択）
3. **Credentials** タブ → **Production Access Token** をコピー

テスト環境の場合は **Sandbox Access Token** を使用してください。

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_locations` | 店舗ロケーション一覧を取得する |
| `list_customers` | 顧客一覧を取得する |
| `search_customers` | メール・電話番号で顧客を検索する |
| `list_payments` | 決済一覧を取得する |
| `list_orders` | 注文一覧を取得する |

## インストール

```bash
cd square
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "square": {
      "command": "square-mcp",
      "env": {
        "SQUARE_ACCESS_TOKEN": "your_square_access_token"
      }
    }
  }
}
```
