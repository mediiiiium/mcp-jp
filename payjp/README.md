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
| `list_charges` | 決済（課金）一覧を取得する（作成日時の新しい順、limit/offset ページネーション、customer/subscription/since/until で絞り込み） |
| `get_charge` | 特定の決済の詳細を取得する（返金状況の確認に使う） |
| `refund_charge` | 決済を返金する（全額 or 部分返金、refund_reason 任意。**べき等性なし**、下記の限界事項を参照） |
| `list_customers` | 顧客一覧を取得する（limit/offset ページネーション、since/until で絞り込み） |
| `list_subscriptions` | サブスクリプション一覧を取得する（customer/plan/status/since/until で絞り込み） |

## 限界事項・注意点

- **べき等性（Idempotency-Key）非対応**: 本コネクタは PAY.JP の **v1 API**（`https://api.pay.jp/v1`）を利用している。
  `Idempotency-Key` ヘッダーによるべき等リクエストは PAY.JP **v2 API のみ**の機能であり、v1 では利用できない。
  そのため `refund_charge` は真にべき等ではない。全額返金済みの決済に再度返金リクエストを送るとエラー
  （「既に返金済み」HTTP 400）になり金額面の二重返金は避けられるが、`amount` を指定した部分返金を
  繰り返し実行すると、その都度追加の返金が発生し実際に二重（多重）返金となる。通信エラー等で結果が
  確認できない場合は、再実行前に `get_charge` で `refunded` / `amount_refunded` を確認すること。
- **返金は決済作成から180日以内のみ可能**。それ以降は返金APIがエラーを返す。
- **決済（charge）自体の削除APIは存在しない**（取り消しは返金のみ）。PAY.JP API には `charge` の更新
  （`description` / `metadata` のみ）、`customer` の作成・更新・削除、`subscription` の一時停止・再開・
  キャンセル・削除のエンドポイントが存在するが、本コネクタは参照系（一覧・詳細取得）と返金のみを
  ツールとして提供しており、これらの更新・削除系操作は未実装。

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
