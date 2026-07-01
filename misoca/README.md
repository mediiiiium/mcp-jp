# misoca-mcp

Misoca（弥生が提供する日本SMB向け見積・納品・請求書サービス）の MCP サーバー。公式 MCP 未提供。

## セットアップ

```bash
cd misoca
pip install -e .
```

## アクセストークンの取得

1. Misoca の管理画面 → アプリ連携 → API連携 より OAuth2 アプリを登録
2. 認可コードフローで `https://app.misoca.jp/oauth2/authorize` にアクセス
3. 取得した認可コードを `https://app.misoca.jp/oauth2/token` に POST してアクセストークンを取得

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `MISOCA_ACCESS_TOKEN` | OAuth2 で取得したアクセストークン |  # pragma: allowlist secret

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "misoca": {
      "command": "misoca-mcp",
      "env": {
        "MISOCA_ACCESS_TOKEN": "your_access_token_here"  # pragma: allowlist secret
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_invoices` | 請求書一覧を取得（取引先・日付・入金/請求ステータス・キーワードで絞り込み可、ページング対応） |
| `get_invoice` | 請求書の詳細情報を取得 |
| `create_invoice` | 新しい請求書を作成（作成のみ。請求済み・入金済みへの変更は別ツールで行う） |
| `mark_invoice_paid` | 請求書を入金済みにする |
| `mark_invoice_unpaid` | 請求書を未入金に戻す |
| `mark_invoice_submitted` | 請求書を請求済みにする（メール送信は行わない） |
| `mark_invoice_unsubmitted` | 請求書を未請求に戻す |
| `trash_invoice` | 請求書をごみ箱に移動する（実質的な削除。完全削除APIはない） |
| `restore_invoice` | ごみ箱の請求書を元に戻す |
| `list_contact_groups` | 取引先（顧客企業）一覧を取得 |
| `list_contacts` | 送り先（請求書の宛先。取引先ごとの部署・担当者単位）一覧を取得 |

### 制限事項

- 取引先・送り先そのものの作成・更新・非表示化API（`POST /contact_group`、`POST /contact` 等）は本コネクタには未実装（読み取りのみ）。
- 請求書をメールで取引先に送付するAPIはMisoca API v3に存在しない（郵送で送付する `send_by_postal_mail` は存在するが、実行すると郵送費用が実際に発生するため本コネクタには実装していない）。
- 請求書の完全削除APIは存在せず、`trash_invoice`（ごみ箱への移動）が実質的な削除操作にあたる。
- `create_invoice` の `contact_id` は「送り先」ID（`list_contacts` で取得）であり、`list_invoices` の絞り込みに使う `contact_group_id`（取引先ID、`list_contact_groups` で取得）とは別の概念なので注意。

## 使用例

```
今月発行した請求書一覧を見せて
```

```
株式会社ABCへの請求書を作成して。件名「Webサイト制作費」、発行日2026-07-01、金額50万円（10%課税）
```

```
請求書ID 12345 を入金済みにして
```
