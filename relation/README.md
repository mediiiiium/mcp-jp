# relation-mcp

Re:lation（日本SMB向けメール共有・カスタマーサポートシステム）の MCP サーバー。公式 MCP 未提供。

## セットアップ

```bash
cd relation
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `RELATION_SUBDOMAIN` | Re:lation のサブドメイン（例: `mycompany` → `mycompany.relationapp.jp` の場合） |
| `RELATION_ACCESS_TOKEN` | API設定画面で発行したアクセストークン |  # pragma: allowlist secret

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "relation": {
      "command": "relation-mcp",
      "env": {
        "RELATION_SUBDOMAIN": "your_subdomain",
        "RELATION_ACCESS_TOKEN": "your_access_token_here"  # pragma: allowlist secret
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_message_boxes` | 受信箱（メールボックス）一覧を取得（ページネーションなし） |
| `search_tickets` | チケット（問い合わせ）を検索（ステータス・ラベル・色・担当者・添付有無・期間で絞り込み可、最大50件/ページ） |
| `get_ticket` | チケットの詳細情報（本文・添付・コメントを含む全メッセージ）を取得 |
| `create_reply_memo` | チケットに対応履歴（応対メモ）を追加。既定でチケットが「対応完了」になる点に注意 |
| `list_users` | オペレーター一覧を取得（最大100件/ページ） |

## 制限事項・注意点

- **キーワード（全文）検索は非対応**: RE:lation API の `tickets/search` はキーワード検索パラメータを提供していないため、`search_tickets` でも件名・本文のキーワード検索はできない。ステータス・ラベル・色・担当者・期間などでの絞り込みのみ可能。
- **メール返信・新規送信は未実装**: `create_reply_memo` はあくまで内部向けの「対応履歴（応対メモ）」を追加するツールであり、顧客へのメール返信・新規送信API（`/mails`, `/mails/reply`, `/mails/draft`）は本コネクタでは未実装。
- **応対メモ追加の副作用**: `create_reply_memo` で `status_cd` を省略すると、RE:lation側の既定値によりチケットが自動的に「対応完了（closed）」になる。対応中のまま記録だけ残したい場合は `status_cd` に `open` または `ongoing` を明示的に指定すること。また `operated_at` は過去日時のみ指定可能。
- **チケットの更新・削除は未実装**: RE:lation API にはチケットのステータス・担当者・ラベル・色などを変更する `PUT /{message_box_id}/tickets/{ticket_id}` が存在するが、本コネクタには実装していない（参照系の `search_tickets` / `get_ticket` と、対応履歴追加の `create_reply_memo` のみ）。
- **アドレス帳（顧客/コンタクト）操作は未実装**: 顧客情報の検索・作成・更新・削除API（`/customer_groups/*`）は本コネクタでは未実装。
- **ラベル・案件分類・保留理由・テンプレートの一覧取得は未実装**: `search_tickets` の `label_ids` 等に渡すIDを確認する専用ツールは無いため、必要な場合は管理画面でIDを確認すること。
- レート制限は 60 リクエスト/分（RE:lation API仕様）。

## 使用例

```
未対応の問い合わせ一覧を見せて
```

```
受信箱1の対応完了チケットのうち、直近1週間に更新されたものを見せて
```

```
チケット ID 456 に「折り返し電話確認済み」という対応履歴を残して。ステータスは対応中のままにして
```
