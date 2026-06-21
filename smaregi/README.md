# smaregi-mcp

スマレジ（POSレジ・店舗管理）の MCP サーバー。商品・売上取引・会員・店舗情報を AI から操作できます。

## セットアップ

```bash
cd smaregi
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `SMAREGI_ACCESS_TOKEN` | OAuth2 フローで取得したアクセストークン |
| `SMAREGI_CONTRACT_ID` | スマレジ 契約ID（管理画面で確認可） |

### アクセストークンの取得

スマレジは OAuth2 認証（認可コードフロー）を採用しています。スマレジ・デベロッパーズ（developers.smaregi.jp）でアプリ登録後、以下のスコープでトークンを取得してください。

必要なスコープ（最低限）:
- `pos.products:read` - 商品参照
- `pos.transactions:read` - 売上取引参照
- `pos.customers:read` - 会員参照
- `pos.stores:read` - 店舗参照

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "smaregi": {
      "command": "smaregi-mcp",
      "env": {
        "SMAREGI_ACCESS_TOKEN": "your_access_token_here",
        "SMAREGI_CONTRACT_ID": "your_contract_id"
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_products` | 商品一覧を取得（商品名・部門で絞り込み可） |
| `get_product` | 商品の詳細情報を取得 |
| `list_transactions` | 売上取引一覧を取得（日付・店舗・会員で絞り込み可） |
| `list_customers` | 会員一覧を取得（名前・ランクで絞り込み可） |
| `list_stores` | 店舗一覧を取得 |

## 使用例

```
今日の売上取引を一覧表示して
```

```
「コーヒー」という名前の商品を検索して
```

```
先月の全取引を集計して売上合計を計算して
```

```
会員番号 xxx の購入履歴を見せて
```
