# invox-mcp

invox（受取請求書・発行請求書・経費精算）の MCP サーバー。受取請求書の一覧取得・承認・仕訳エクスポートを AI から操作できます。

## セットアップ

```bash
cd invox
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `INVOX_ACCESS_TOKEN` | OAuth2 フローで取得したアクセストークン（有効期限10時間） |
| `INVOX_COMPANY_CODE` | invox 会社コード（管理画面 URL に含まれる識別子） |

### アクセストークンの取得

invox は OAuth2 認証（認可コードフロー）を採用しています。Professional プランでクライアント ID とクライアントシークレットを取得後、以下の手順でアクセストークンを発行してください。

1. `https://api.invox.jp/oauth2/authorize/` にブラウザでアクセス
2. 認可コードを取得
3. `https://api.invox.jp/oauth2/token/` に POST してアクセストークンを取得

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "invox": {
      "command": "invox-mcp",
      "env": {
        "INVOX_ACCESS_TOKEN": "your_access_token_here",
        "INVOX_COMPANY_CODE": "your_company_code"
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_received_invoices` | 受取請求書の一覧を取得（ステータス・日付・仕入先で絞り込み可） |
| `get_received_invoice` | 受取請求書の詳細情報を取得 |
| `approve_received_invoice` | 受取請求書のワークフロー申請を承認する |
| `list_suppliers` | 仕入先一覧を取得 |
| `export_journal` | 受取請求書の仕訳データをエクスポート |

## 使用例

```
今月受け取った未確認の請求書を一覧表示して
```

```
請求書ID xxx の詳細を見せて
```

```
株式会社サンプルからの請求書をすべて承認して
```

```
今月の確定済み請求書の仕訳をfreee形式でエクスポートして
```
