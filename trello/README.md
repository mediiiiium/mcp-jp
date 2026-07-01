# trello-mcp

Trello MCP サーバー。ボード・リスト・カードの管理ができます。公式 MCP 未提供。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `TRELLO_API_KEY` | ✅ | Trello API キー |
| `TRELLO_TOKEN` | ✅ | Trello アクセストークン |

## 認証情報取得方法

1. [Trello Developer Portal](https://trello.com/app-key) にアクセス
2. **API Key** をコピー
3. 同ページの **Token** リンクをクリックして権限を付与し、Token をコピー

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_boards` | 自分が所属するボード一覧を取得（filter で open/closed/all 等の絞り込み可、省略時はAPI既定の all） |
| `list_lists` | ボード内のリスト一覧を取得（filter で open/closed/all の絞り込み可、省略時はAPI既定の open） |
| `list_cards` | リスト内のカード一覧を取得（filter で open/closed/all の絞り込み可、省略時はAPI既定の open） |
| `create_card` | 新しいカードを作成（desc・due・start・idMembers・idLabels・pos は省略可） |
| `move_card` | カードを別のリストに移動する（冪等。別ボードのリストも指定可） |

## インストール

```bash
cd trello
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "trello": {
      "command": "trello-mcp",
      "env": {
        "TRELLO_API_KEY": "your_trello_api_key",  # pragma: allowlist secret
        "TRELLO_TOKEN": "your_trello_token"  # pragma: allowlist secret
      }
    }
  }
}
```

## 既知の制約

Trello API（公式リファレンス: https://developer.atlassian.com/cloud/trello/rest/）には以下の操作も
存在するが、本コネクタには実装していない（必要な場合は Trello の管理画面から操作してください）。

- ボードの作成・更新（名前変更等）・アーカイブ（`PUT /1/boards/{id}` の `closed`）・完全削除
  （`DELETE /1/boards/{id}`。削除は復元不可のため、通常はアーカイブが推奨される）
- リストの作成・更新（名前変更・別ボードへの移動）・アーカイブ（`PUT /1/lists/{id}` の `closed`）。
  なお Trello にはリストの削除エンドポイント自体が存在せず、アーカイブのみ可能
- カードの名前・説明・期限・担当者・ラベル変更やアーカイブ（`PUT /1/cards/{id}` の各種フィールド）、
  完全削除（`DELETE /1/cards/{id}`。アーカイブと異なり元に戻せず、コメント・添付ファイルも含めて
  完全に消去される）。`move_card` は `idList`（所属リスト）のみを更新する
- コメント・チェックリスト・添付ファイル・ラベル・メンバー管理などカード付随情報の作成・取得・更新・削除
- Webhook・検索（`GET /1/search`）・組織（Workspace）管理

`list_boards`・`list_lists`・`list_cards` はいずれもページネーションカーソル（before/since）を
持たず、条件に合致する件数を1回のレスポンスで配列として全件返す。1万件を超えるカードを持つ
リストなど、応答が大きくなりすぎる場合は本コネクタの共通処理により20,000文字を超えた分が切り詰め
られるため、`filter` で絞り込むか対象を分けて呼び出すこと。

`create_card` は呼び出すたびに新規カードを作成し、Trello API 側に重複防止（べき等性）の仕組みは
無い。誤って複数回呼び出すと同名カードが重複作成されるため注意すること。
