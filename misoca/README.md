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
| `list_invoices` | 請求書一覧を取得（取引先・日付で絞り込み可） |
| `get_invoice` | 請求書の詳細情報を取得 |
| `create_invoice` | 新しい請求書を作成 |
| `mark_invoice_paid` | 請求書を入金済みにする |
| `list_contacts` | 取引先一覧を取得 |

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
