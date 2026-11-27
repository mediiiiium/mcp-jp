---
name: smaregi
description: スマレジ（POS・店舗管理）の商品・売上取引と明細・会員・在庫・部門・店舗を、mcp-jp の smaregi MCP サーバーで調べる（閲覧のみ）。「今日の売上を一覧にして」「先月の売上合計は」「この商品の在庫と増減の履歴は」のように、スマレジのデータを扱う依頼で使う。
---

# スマレジ（mcp-jp / smaregi）

スマレジ・プラットフォームAPI（POS）のデータを、MCP サーバー `smaregi-mcp` 経由で読む。
**すべて閲覧のみ**で、商品・在庫・会員などを書き換えるツールはない。

> 動作確認の状況: 公式ドキュメントに沿って実装し、構造とエラー処理のテストは CI で通しているが、実際のスマレジ契約ではまだ動かしていない（README の「動作確認」列を参照）。

## 準備

1. スマレジ・デベロッパーズでアプリを登録し、OAuth2（認可コードフロー）でアクセストークンを取得する。最低限のスコープ: `pos.products:read` `pos.transactions:read` `pos.customers:read` `pos.stores:read` `pos.stock:read`
2. 契約ID（管理画面で確認できる）を控える

> プラグイン `mcp-jp-smaregi` で入れた場合は MCP サーバーが同梱されている（Docker が必要）。下の表の環境変数を設定して Claude Code を起動し直せばよく、次の「インストールして登録する」は要らない。

3. インストールして登録する

```bash
pip install "git+https://github.com/mediiiiium/mcp-jp#subdirectory=smaregi"
claude mcp add smaregi -e SMAREGI_ACCESS_TOKEN=<トークン> -e SMAREGI_CONTRACT_ID=<契約ID> -- smaregi-mcp
```

Claude Desktop の場合は `claude_desktop_config.json` の `mcpServers` に `"command": "smaregi-mcp"` と同じ2つの環境変数を書く。

| 環境変数 | 内容 |
|---|---|
| `SMAREGI_ACCESS_TOKEN` | OAuth2 で取得したアクセストークン |
| `SMAREGI_CONTRACT_ID` | スマレジの契約ID |

## 進め方

- **売上は期間が必須**: `list_transactions` は `transaction_date_time_from` / `transaction_date_time_to` を指定しないとエラーになる。形式は `YYYY-MM-DDThh:mm:ssTZD`（例: `2026-11-01T00:00:00+09:00`）、範囲は最大31日。1か月を超える集計は31日以内に区切って複数回呼ぶ。
- **何が売れたか**: 取引ヘッダは `list_transactions`、購入商品の行は `get_transaction_details`（`transaction_id` に、取引ヘッダの `transactionHeadId` を渡す）。
- **名前では検索できない**: 商品名・部門名・会員名・会員ランクで絞るパラメータは API にない。一覧を取ってから名前で絞り込む。
- **会員で絞るとき**: 取引の会員絞り込みは会員ID ではなく会員コード（`customer_code`）で行う。
- **ページ送り**: `page` 方式（1始まり）で、総件数は返らない。全件が要るときは空配列が返るまで `page` を進める。
- **在庫**: `list_stock` には、一度でも在庫が動いた商品×店舗の組み合わせしか出ない。登録直後で動きのない商品が見当たらないのは仕様。増減の理由は `get_stock_changes`。
- **店舗・部門の ID**: 絞り込みに使う ID は `list_stores` / `list_categories` で確かめる。

## できないこと

商品・部門・会員・店舗・取引・在庫の作成・更新・削除、取引明細CSVの作成、POS 以外の仕様書（在庫管理・受注・ウェイター・タイムカード）の API。

## ツール

`list_products` `get_product` `list_categories` `list_transactions` `get_transaction_details` `list_customers` `list_stock` `get_stock_changes` `list_stores`

詳しい引数は [smaregi/README.md](https://github.com/mediiiiium/mcp-jp/blob/main/smaregi/README.md) を参照。
