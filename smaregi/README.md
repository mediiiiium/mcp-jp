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
- `pos.products:read` - 商品参照（`list_categories` の部門参照もこのスコープ）
- `pos.transactions:read` - 売上取引参照（`get_transaction_details` の明細参照もこのスコープ）
- `pos.customers:read` - 会員参照
- `pos.stores:read` - 店舗参照
- `pos.stock:read` - 在庫参照

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
| `list_products` | 商品一覧を取得（部門ID・商品コード・グループコードで絞り込み可、page方式ページネーション） |
| `get_product` | 商品IDを指定して商品1件の詳細情報を取得 |
| `list_transactions` | 売上取引一覧を取得（取引日時・店舗・会員コードで絞り込み可、期間パラメータ1つ以上が必須） |
| `list_customers` | 会員一覧を取得（会員コード・会員番号・会員ID範囲で絞り込み可） |
| `list_stock` | 商品・店舗ごとの在庫数一覧を取得（商品ID・店舗ID・更新日時で絞り込み可） |
| `get_stock_changes` | 商品ID・店舗IDを指定して在庫変動履歴（増減の原因・日時・結果在庫数）を取得 |
| `get_transaction_details` | 取引IDを指定して取引明細（購入商品行）を取得（値引き・商品属性の付加情報オプション有） |
| `list_categories` | 部門（商品カテゴリ）一覧を取得（部門コード・階層レベルで絞り込み可） |
| `list_stores` | 店舗一覧を取得（店舗コードで絞り込み可） |

## 既知の制約

スマレジ・プラットフォームAPI（公式ドキュメント: https://developers.smaregi.dev/platform-api-reference/ ）を
調査のうえ確認した制約は以下の通り。

- **商品名・部門名・会員名・会員ランクでの絞り込みはAPI非対応。** `list_products` に商品名検索パラメータは
  存在せず、`list_categories` にも部門名検索パラメータ、`list_customers` にも会員名やランク（rank）で
  絞り込むパラメータは存在しない。呼び出し側で一覧取得後にフィルタする必要がある。
- **`list_transactions` は期間系パラメータ（取引日時・端末取引日時・締め日・更新日時のいずれか）を最低1つ
  指定しないとAPIがエラーを返す。** 本コネクタでは `transaction_date_time_from` / `transaction_date_time_to`
  のみ対応（形式は `YYYY-MM-DDThh:mm:ssTZD`、最大31日間の範囲）。
- **会員での絞り込みは会員ID（customer_id）ではなく会員コード（customer_code）でのみ可能。** `customer_id`
  という汎用フィルタはAPIに存在しない。
- **ページネーションはpage方式（1始まり）。** レスポンスに総件数は含まれないため、空配列が返るまでpageを
  増やして取得を続ける必要がある。各一覧の既定の並び順はAPI仕様上明記されていない（ドキュメントで確認できず）。
- **`list_stock` は、販売・入出荷等で在庫数が一度でも変動した商品・店舗の組み合わせでなければ結果に
  現れない。** スマレジ・プラットフォームAPIの仕様上の制約で、登録直後で動きの無い商品は在庫一覧に出ない。
- スマレジ・プラットフォームAPIには商品・部門・会員・店舗・取引・在庫それぞれについて新規作成（POST）・
  更新（PATCH）・削除（DELETE）に対応するエンドポイントも存在するが、本コネクタでは未実装（すべて閲覧のみ）。
  特に在庫の更新・相対値更新・一括更新はPOSの実在庫を直接書き換える操作であり、書き込み系の中でも
  リスクが高いため見送った。
- **取引明細一覧CSV作成（`POST /transactions/details/out_file_async`）は未実装。** 同期的なGETで完結せず、
  非同期ジョブを起票してファイル完成を別途ポーリングする方式のエンドポイントであり、他ツールと設計が
  非対称になる（かつ書き込み系に近い挙動）ため見送った。明細1件単位の参照は `get_transaction_details` で
  代替できる。
- **スマレジ・プラットフォームAPIには POS仕様書のほかに、在庫管理仕様書・受注管理仕様書・ウェイター仕様書・
  タイムカード仕様書という別系統の仕様書が存在する。** 本コネクタはPOS仕様書（`/pos` 配下）のみを対象と
  しており、それら別仕様書（発注・入荷・出荷・棚卸、受注、テーブル管理、勤怠等）のエンドポイントは
  調査対象外・未実装。

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
