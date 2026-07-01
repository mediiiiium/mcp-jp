# freshdesk-mcp

Freshdesk MCP サーバー。チケット・コンタクトの管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `FRESHDESK_API_KEY` | ✅ | Freshdesk API キー |
| `FRESHDESK_SUBDOMAIN` | ✅ | サブドメイン（例: `mycompany` → `mycompany.freshdesk.com`） |

## API キー取得方法

1. Freshdesk にログイン
2. 右上のプロフィールアイコン → **Profile Settings**
3. ページ右側に **Your API Key** が表示される

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_tickets` | チケット一覧をページ単位で取得する（既定は直近30日以内・作成日時の新しい順）。filter・requester_id・email・company_id・updated_since・order_by・order_type で絞り込み・並び替え可能 |
| `get_ticket` | チケット1件の詳細を取得する。include で会話・問い合わせ者・会社・統計情報を追加取得可能（APIクレジット消費に注意） |
| `create_ticket` | 新しいチケットを作成する（べき等ではない。添付ファイル未対応） |
| `delete_ticket` | チケットを1件ソフトデリートする（復元APIは存在するが本コネクタ未実装） |
| `list_contacts` | コンタクト一覧をページ単位で取得する。email・mobile・phone・company_id・state・updated_since で絞り込み可能 |
| `get_contact` | コンタクト1件の詳細を取得する |
| `delete_contact` | コンタクトを1件ソフトデリートする（完全削除APIは存在するが本コネクタ未実装） |

## ステータス・優先度の値

**ステータス**: 2=Open, 3=Pending, 4=Resolved, 5=Closed（チケット作成省略時は2=Open）

**優先度**: 1=Low, 2=Medium, 3=High, 4=Urgent（チケット作成省略時は1=Low）

## 既知の制約

- `list_tickets` の `status`・`priority` 引数はクエリパラメータとして送信されるが、Freshdesk公式ドキュメントの
  一覧APIパラメータ一覧には含まれておらず、API側で無視され結果に反映されない可能性がある。確実に絞り込みたい
  場合は取得後にクライアント側でフィルタするか、Freshdeskの検索API（`/api/v2/search/tickets`。本コネクタ未実装）
  を利用する必要がある。
- `list_tickets` は既定で直近30日以内に作成されたチケットのみが対象（Freshdesk API の仕様）。それより古い
  チケットを取得するには `updated_since` を指定する。
- `list_tickets` は全体で最大300ページ（30000件）までしか取得できない（Freshdesk API の上限）。
- `delete_ticket`・`delete_contact` はいずれもソフトデリート。Freshdeskにはチケットの復元エンドポイント
  （`/api/v2/tickets/{id}/restore`）とコンタクトの完全削除エンドポイント（`/api/v2/contacts/{id}/hard_delete`）
  が別途存在するが、誤操作時のリスクを踏まえ本コネクタには実装していない。
- `create_ticket` はチケット添付ファイルのアップロードに対応していない（Freshdesk側が
  `multipart/form-data` を要求するため）。

## インストール

```bash
cd freshdesk
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "freshdesk": {
      "command": "freshdesk-mcp",
      "env": {
        "FRESHDESK_API_KEY": "your_freshdesk_api_key",  # pragma: allowlist secret
        "FRESHDESK_SUBDOMAIN": "mycompany"
      }
    }
  }
}
```
