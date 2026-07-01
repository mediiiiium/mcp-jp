# intercom-mcp

Intercom MCP サーバー。コンタクト・カンバセーションの管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `INTERCOM_ACCESS_TOKEN` | ✅ | Intercom アクセストークン |

## トークン取得方法

1. Intercom 管理画面にログイン
2. **Settings** → **Integrations** → **Developer Hub**
3. アプリを選択（または新規作成）
4. **Authentication** → **Access Token** をコピー

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_contacts` | コンタクト一覧を取得する（絞り込みなし、カーソルページネーション） |
| `search_contacts` | メール・名前の部分一致（OR）でコンタクトを検索する |
| `get_contact` | コンタクトの詳細を1件取得する |
| `create_contact` | 新しいコンタクトを作成する（べき等ではない。同一メールで409になる場合あり） |
| `delete_contact` | コンタクトを1件削除する（取り消し不可） |
| `list_conversations` | カンバセーション一覧を取得する（`open`指定でオープンのみ/全件を切替） |

## 既知の制約

- **ページネーション**: 一覧・検索系はすべてIntercomのカーソル方式（`starting_after`）。
  レスポンスの `pages.next.starting_after` を次回呼び出しに渡すことで続きを取得する。
  `pages.next` が無ければ最終ページ。既定の並び順はIntercom公式ドキュメントに明記されておらず未確認。
- **`list_conversations` の絞り込み**: Intercomの `GET /conversations` エンドポイント自体には
  状態（open/closed/snoozed）でフィルタするクエリパラメータが存在しない。そのため本コネクタは
  `open=true`（既定）時のみ `POST /conversations/search` を使って `open` フィールドで絞り込み、
  `open=false` 時はフィルタなしの `GET /conversations` で全件を取得する。
- **会話の削除・詳細取得・返信**: Intercom APIには会話を削除するエンドポイントは存在しない
  （`PUT /conversations/{id}` によるclose/snooze/assign等の状態変更のみ可能）。また会話1件の詳細取得・
  返信投稿に対応するツールも本コネクタには未実装。
- **コンタクトの更新**: `PUT /contacts/{id}`（更新）に対応するツールは本コネクタには未実装。
  作成・詳細取得・検索・削除のみ提供する。
- **検索の対応フィールド**: `search_contacts` はメール・名前の部分一致のみを公開している。
  Intercomの `POST /contacts/search` は他に `role`/`owner_id`/`created_at`/`tag_id` など30以上の
  フィールドと `=, !=, IN, NIN, >, <, ~, !~, ^, $` 等の演算子をサポートするが、本コネクタでは未対応。

## インストール

```bash
cd intercom
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "intercom": {
      "command": "intercom-mcp",
      "env": {
        "INTERCOM_ACCESS_TOKEN": "your_intercom_access_token"
      }
    }
  }
}
```
