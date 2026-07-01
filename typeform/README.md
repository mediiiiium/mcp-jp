# typeform-mcp

Typeform MCP サーバー。フォーム・アンケートの管理・回答取得ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `TYPEFORM_ACCESS_TOKEN` | ✅ | Typeform Personal Access Token |

## トークン取得方法

1. Typeform にログイン
2. 右上のアバター → **Settings** → **Personal tokens**
3. **Generate a new token** をクリック
4. Token name を入力して **Generate token** をクリック

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_forms` | フォーム一覧を取得する（page/page_size、search、workspace_id、sort_by/order_by で絞り込み・並び替え可） |
| `get_form` | フォームの詳細（質問構成・ロジック・テーマ等）を取得する |
| `get_responses` | フォームの回答一覧を取得する（page_size、since/until、before/after カーソル、query、response_type で絞り込み） |
| `list_workspaces` | ワークスペース一覧を取得する（page/page_size、search で絞り込み） |
| `get_response_summary` | 回答インサイト（サマリー統計）を取得する。**Typeformビジネスプラン以上限定**、集計期間は全期間固定（日付範囲指定不可） |

## 制限事項・未実装の操作

- フォーム・ワークスペースの作成/更新/削除に対応するAPIはTypeformに存在するが、本コネクタでは未実装（読み取り専用）。
- 回答の削除（`DELETE /forms/{form_id}/responses`）に対応するAPIはTypeformに存在するが、本コネクタでは未実装。
- `get_responses` は既定で `response_type=completed`（送信完了済み）のみを返す。未完了の回答（started/partial）を見るには `response_type` を明示的に指定する必要がある。
- `get_responses` の `before`/`after` カーソルは、Typeform APIの仕様上 `sort` パラメータと併用できない（本コネクタは `sort` を公開していない）。
- `get_response_summary` はTypeform APIの仕様上、日付範囲を絞り込むクエリパラメータが存在せず、常に全期間の集計結果になる。

## インストール

```bash
cd typeform
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "typeform": {
      "command": "typeform-mcp",
      "env": {
        "TYPEFORM_ACCESS_TOKEN": "your_typeform_access_token"
      }
    }
  }
}
```
