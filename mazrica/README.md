# mazrica-mcp

Mazrica Sales（Senses）SFA の MCP サーバー。取引先・案件・ユーザーを AI から操作できます。

## セットアップ

```bash
cd mazrica
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `MAZRICA_API_KEY` | Mazrica 管理画面 → 設定 → API設定 から発行 |

API キーの発行には growth プラン以上の契約が必要です。

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "mazrica": {
      "command": "mazrica-mcp",
      "env": {
        "MAZRICA_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_customers` | 取引先一覧を取得（名前・更新日時で絞り込み可、page/limit ページネーション） |
| `create_customer` | 新規取引先を登録 |
| `list_deals` | 案件（商談）一覧を取得（取引先名/案件名・案件タイプ・更新日時で絞り込み可） |
| `create_deal` | 新規案件を登録（案件タイプ・取引先・フェーズ・商品・契約確度・チャネル・担当者が必須） |
| `list_deal_types` | 案件タイプ一覧を取得（create_deal の deal_type_id 確認用） |
| `get_deal_type` | 案件タイプ1件の詳細（フェーズ・商品・契約確度・チャネル等のID一覧）を取得 |
| `list_users` | 営業担当者（ユーザー）一覧を取得 |

## API の制約・未実装の操作

- **取引先・案件の更新／削除**: Mazrica Open API には `PATCH`/`DELETE` エンドポイントが存在するが、本コネクタには実装されていない。必要な場合は Mazrica 管理画面から操作する。
- **案件を取引先IDで直接絞り込み検索**: `GET /deals` に取引先ID（customer_id）で絞り込むクエリパラメータは存在しない。`list_deals` の `search_word` は取引先名／案件名の部分一致でのみ絞り込める。厳密に取引先IDで絞り込みたい場合、Mazrica API には複合条件検索 `POST /deals/search` があるが本コネクタには未実装。
- **案件の memo（メモ）欄**: Mazrica API の案件オブジェクトに汎用の memo フィールドは存在しない（アカウント固有の詳細項目 `dealCustoms` 経由でのみ設定可能。本コネクタには未実装）。
- **案件作成時の必須ID**: `deal_type_id`・`phase_id`・`product_id`・`probability_id`・`channel_id` はアカウントごとに設定されたマスタ値のため決め打ちできない。`list_deal_types` → `get_deal_type` の順に確認してから `create_deal` を呼ぶこと。

## 使用例

```
今月クローズ予定の案件を全部リストアップして
```

```
株式会社サンプルを新規取引先として登録して
```

```
田中さんが担当している案件を見せて
```
