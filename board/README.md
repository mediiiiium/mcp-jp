# board-mcp

board（日本向けクラウド業務・経営管理システム）の MCP サーバー。公式 MCP 未提供。

見積書・発注書・納品書・請求書・プロジェクト管理・顧客管理をカバー。

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

いずれもページネーションは `page` / `per_page` 方式（board API 側の上限は `per_page=100`）。

## 既知の制約

board API 自体には顧客・プロジェクトの更新（PATCH）・削除（DELETE）エンドポイントや、プロジェクト配下の請求書ドキュメントの更新エンドポイントが存在しますが、本コネクタには以下のツールは実装されていません（必要な場合は board 管理画面から操作してください）。

- 顧客（取引先）の作成・更新・削除
- プロジェクトの更新・削除
- 請求書（見積書・発注書・納品書・領収書含む）の新規作成・更新・削除

また `list_invoices` が返す `id` は請求管理データのIDであり、請求書ドキュメント自体のIDとは別概念です。ドキュメントの中身（明細等）まで確認したい場合は `get_project` を `response_group=invoice` で呼び出してください。

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
