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
  `items/edit_stock` 等）、カテゴリ管理（`categories/*` `item_categories/*`）、振込申請情報
  （`savings`）、配送会社一覧（`delivery_companies`）等のエンドポイントも存在するが、本コネクタでは
  未実装（商品・注文の閲覧と発送ステータス更新のみに対応）。

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
