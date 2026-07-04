# board-mcp

board（日本向けクラウド業務・経営管理システム）の MCP サーバー。公式 MCP 未提供。

見積書・発注書・納品書・請求書・プロジェクト管理・顧客管理をカバー。

- API ドキュメント: https://developers.the-board.jp/doc/

## セットアップ

```bash
cd board
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `BOARD_API_KEY` | board 管理画面で発行した API キー（x-api-key ヘッダー） |  # pragma: allowlist secret
| `BOARD_API_TOKEN` | board 管理画面で発行した API トークン（Bearer トークン） |  # pragma: allowlist secret

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "board": {
      "command": "board-mcp",
      "env": {
        "BOARD_API_KEY": "your_api_key_here",  # pragma: allowlist secret
        "BOARD_API_TOKEN": "your_api_token_here"  # pragma: allowlist secret
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_clients` | 顧客（取引先）一覧を取得（名前の部分一致で絞り込み可）。読み取り専用 |
| `list_projects` | プロジェクト一覧を取得（顧客・稼働状況で絞り込み可、既定は新しい順）。読み取り専用 |
| `get_project` | プロジェクト1件の詳細を取得。`response_group` で見積書・発注書・請求書等の書類データも合わせて取得可能 |
| `list_invoices` | 請求データ一覧を取得（顧客・プロジェクトで絞り込み可）。請求書ドキュメントそのものの詳細は `get_project`（`response_group=invoice`）の方が確実 |
| `create_project` | 新しいプロジェクトを作成（べき等ではない。呼ぶたびに新規レコードが作成される） |
| `get_client` | 顧客1件の詳細情報を取得（response_group=large ですべての項目を含む） |
| `list_client_branches` | 顧客の支社・支店一覧を取得（顧客IDでの絞り込み対応） |
| `list_contacts` | 顧客の担当者一覧を取得（顧客IDでの絞り込み対応） |
| `list_project_costs` | 案件原価データの一覧を取得（案件横断、請求日・支払日の範囲での絞り込み対応） |
| `list_users` | board 利用ユーザー一覧を取得（メールアドレスでの絞り込み対応） |
| `list_analyses` | 計上データ（経営分析用の集計データ）一覧を取得（計上年月・受注/請求ステータスでの絞り込み対応） |

いずれもページネーションは `page` / `per_page` 方式（board API 側の上限は `per_page=100`）。

## 既知の制約

board API 自体には顧客・プロジェクトの更新（PATCH）・削除（DELETE）エンドポイントや、プロジェクト配下の請求書ドキュメントの更新エンドポイントが存在しますが、本コネクタには以下のツールは実装されていません（必要な場合は board 管理画面から操作してください）。

- 顧客（取引先）・顧客支社・顧客担当者の作成・更新・削除
- プロジェクト・案件原価の更新・削除
- 請求書（見積書・発注書・納品書・領収書含む）の新規作成・更新・削除

また `list_invoices` が返す `id` は請求管理データのIDであり、請求書ドキュメント自体のIDとは別概念です。ドキュメントの中身（明細等）まで確認したい場合は `get_project` を `response_group=invoice` で呼び出してください。

2026-07-05 の深掘りで公式APIドキュメント（`https://developers.the-board.jp/doc/`、OpenAPI 3.0形式）を確認した結果、以下のリソース・エンドポイントも実在するが、本コネクタでは見送った:

- **発注管理ドメイン（発注先 `payees`・発注 `expenditures`・発注支払 `expenditure_payments` とそれぞれの支社/担当者・書類）**: エンドポイント自体は実在するが、既存の本コネクタは受注（顧客・案件・請求）ドメインに特化した設計であり、発注管理ドメインを含めると対象範囲・ツール数が大きく広がるため、今回はスコープ外として見送った。需要が確認できれば発注先一覧・発注一覧など読み取り系から独立して検討する。
- **マスタ末端データ（`groups` グループ、`payment_terms` 支払条件、`project_types` 案件区分、`expenditure_types` 発注区分、`accounting_types` 会計区分、`document_send_channels` カスタム書類送付方法）**: いずれも読み取り専用GETとして実在を確認したが、単体では利用頻度が低い設定値マスタであり、優先度を下げて見送った。
- **書類個別取得API（`GET /documents/estimates/{id}` 等の見積書・発注書・納品書・請求書・領収書の個別詳細）**: 実在は確認したが、`get_project` の `response_group` パラメータで同等の情報を取得できるため、重複を避けて見送った。
- **顧客支社・顧客担当者の個別詳細取得（`GET /client_branches/{id}`、`GET /contacts/{id}`）**: 一覧APIのレスポンス自体に十分な項目が含まれるため、個別取得は優先度を下げて見送った。

## 使用例

```
今月の請求書一覧を見せて
```

```
株式会社ABCのプロジェクト一覧を表示して
```

```
新しいプロジェクト「ウェブサイトリニューアル」を株式会社XYZ向けに作成して、予算は500万円
```
