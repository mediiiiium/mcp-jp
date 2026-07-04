# base-ec-mcp

BASE（ECプラットフォーム）の MCP サーバー。ショップの商品管理・注文管理を AI から操作できます。

## セットアップ

```bash
cd base-ec
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `BASE_ACCESS_TOKEN` | BASE APIアクセストークン（OAuth2.0で取得） |

### アクセストークンの取得

1. [BASE Developers](https://developers.thebase.com/) でアプリ登録・審査申請
2. 承認後、OAuth2.0認証フローでアクセストークンを取得
   - 認証URL: `https://api.thebase.in/1/oauth/authorize`
   - トークンURL: `https://api.thebase.in/1/oauth/token`
3. 取得したアクセストークンを環境変数に設定

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "base-ec": {
      "command": "base-ec-mcp",
      "env": {
        "BASE_ACCESS_TOKEN": "your_access_token_here"
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `get_shop` | ショップ情報（名前・URL・説明等）を取得。読み取り専用 |
| `list_items` | 商品一覧を取得（件数・ソート・公開状態・カテゴリで絞り込み可、offsetページネーション） |
| `get_item` | 商品1件の詳細（画像各サイズURL・バリエーション・商品オプション含む）を取得 |
| `search_items` | 商品をキーワードで全文検索（title/detail/categories/shop_nameが対象） |
| `list_categories` | カテゴリ一覧を階層構造込みで取得 |
| `get_item_categories` | 商品1件に紐づくカテゴリの一覧を取得 |
| `list_savings` | 振込申請情報の一覧を取得（申請額・手数料・状態・入金期日等） |
| `list_delivery_companies` | BASE対応の配送業者一覧を取得 |
| `list_orders` | 注文一覧をサマリ取得（注文日時で絞り込み可、offsetページネーション） |
| `get_order` | 注文1件の詳細（購入者情報・商品明細・order_item_id 含む）を取得 |
| `update_order_status` | 注文内の商品行（order_item_id）を発送済み/キャンセルに更新 |

## 既知の制約

BASE API（公式ドキュメント: https://docs.thebase.in/api/ ）を調査のうえ確認した制約は以下の通り。

- **ページネーションはoffset方式のみ**（カーソル方式ではない）。レスポンスに総件数は含まれないため、
  空配列が返るまで offset を増やして取得を続ける必要がある。
- **`update_order_status` は注文単位ではなく商品行（order_item_id）単位で操作する。** 注文全体を表す
  `unique_key` とは別の識別子であり、`get_order` のレスポンスから取得する必要がある。
- **ステータス遷移は `ordered → dispatched` または `ordered → cancelled` のみ許可**されており、
  それ以外の遷移（再変更等）はAPI側の業務ルールにより失敗する。べき等ではない。
- **注文一覧に発送状況（dispatch_status）での絞り込みは対応していない。** 注文日時（`start_ordered`/
  `end_ordered`）での絞り込みのみ可能で、更新日時での絞り込みはできない。
- **注文自体の新規作成・削除に対応するAPIはBASEに存在しない**（注文は購入者のチェックアウトによっての
  み作成される）。後払い決済の入金確認・配送会社/追跡番号の登録（`atobarai_status` 等）も本コネクタでは
  未実装。
- BASE APIには商品の新規作成・編集・削除・画像登録・在庫更新（`items/add` `items/edit` `items/delete`
  `items/add_image` `items/delete_image` `items/edit_stock` `items/delete_variation`）、カテゴリの
  新規登録・更新・削除（`categories/add` `categories/edit` `categories/delete`）、商品カテゴリの
  新規登録・削除（`item_categories/add` `item_categories/delete`）等の**書き込み系エンドポイントも
  存在するが、本コネクタでは未実装**（実在は確認済みだが、業務データを直接改変する操作であり、
  戦略上「書き込み系は監査・確認前提で慎重に扱う」方針に照らして今回は見送った。読み取り系を
  優先して拡充している）。
- `search/`（グローバル商品検索）は2022年2月で新規受付を終了しているとドキュメントに明記されており、
  新規トークンでは利用できない可能性が高いため未実装。ショップ内検索が必要な場合は `search_items`
  （`items/search`）を使うこと。
- 2026-07-05の深掘りで `list_savings`（`GET /1/savings/`）を追加したが、**`read_savings` という
  専用スコープが必要**（他ツールが前提とする `read_items` 等では権限不足になる）。既存の
  `BASE_ACCESS_TOKEN` に `read_savings` スコープが含まれていない場合は 403 になるため、必要な場合は
  BASE Developers 側でスコープを追加したトークンを再取得すること。
- 友だち情報のような「単体取得」系で実在が確認できず見送った他コネクタの前例（lstep の `get_friend`）
  と同様の考え方で、本コネクタでも「ドキュメントに明記されたエンドポイントのみ」を実装対象にしている。
  今回の調査範囲では、ドキュメントに一覧されているエンドポイントは全て実在が確認でき、読み取り系は
  本README記載の10種で網羅した（未実装は上記の書き込み系および終了済みの `search/` のみ）。

## 使用例

```
ショップの情報を見せて
```

```
登録されている商品の一覧を表示して
```

```
今月の注文をすべて見せて
```

```
未発送の注文一覧を教えて
```

```
注文 abc123 の詳細を見せて
```

```
注文 abc123 を発送済みに更新して
```

```
「Tシャツ」で商品を検索して
```

```
今月の振込申請の状況を教えて
```
