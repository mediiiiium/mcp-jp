# stripe-mcp

Stripe（決済・請求管理）の MCP サーバー。顧客・決済・請求書・サブスクリプションの確認を AI から操作できます。

## セットアップ

```bash
cd stripe
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `STRIPE_SECRET_KEY` | Stripe シークレットキー（`sk_live_` または `sk_test_` で始まるキー） |

### APIキーの取得

1. Stripe ダッシュボードにログイン
2. 「開発者」→「APIキー」から取得
3. 本番環境: `sk_live_...` / テスト環境: `sk_test_...`

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "stripe": {
      "command": "stripe-mcp",
      "env": {
        "STRIPE_SECRET_KEY": "sk_live_your_secret_key_here"
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_customers` | 顧客一覧を取得（メールアドレスで絞り込み可） |
| `get_customer` | 顧客IDを指定して詳細情報を取得 |
| `list_charges` | 決済一覧を取得（顧客・日付範囲で絞り込み可） |
| `list_invoices` | 請求書一覧を取得（顧客・ステータスで絞り込み可） |
| `list_subscriptions` | サブスクリプション一覧を取得（ステータスで絞り込み可） |

## 使用例

```
顧客一覧を見せて
```

```
顧客ID cus_xxxxx の詳細を教えて
```

```
今月の決済一覧を表示して
```

```
未払いの請求書を一覧表示して
```

```
アクティブなサブスクリプションをすべて見せて
```
