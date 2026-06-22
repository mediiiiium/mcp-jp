# payjp-mcp

PAY.JP（日本向け決済・課金サービス）の MCP サーバー。公式 MCP 未提供。

## セットアップ

```bash
cd payjp
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `PAYJP_SECRET_KEY` | PAY.JP 管理画面で発行したシークレットキー（sk_ で始まる） |  # pragma: allowlist secret

本番環境では `sk_live_` 、テスト環境では `sk_test_` で始まるキーを使用します。

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "payjp": {
      "command": "payjp-mcp",
      "env": {
        "PAYJP_SECRET_KEY": "sk_test_your_key_here"  # pragma: allowlist secret
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_charges` | 決済（課金）一覧を取得する |
| `get_charge` | 特定の決済の詳細を取得する |
| `refund_charge` | 決済を返金する |
| `list_customers` | 顧客一覧を取得する |
| `list_subscriptions` | サブスクリプション一覧を取得する |

## 使用例

```
今月の決済一覧を取得して
```

```
課金ID ch_xxx の詳細を確認して
```

```
課金ID ch_xxx を全額返金して
```

```
アクティブなサブスクリプション一覧を見せて
```
