# freee MCP

freee会計 の MCP サーバー。

Claude 等のAIエージェントから freee会計を操作できます。

## 利用可能なツール

- `list_companies` — 事業所一覧取得（FREEE_COMPANY_ID 確認に使う）
- `list_deals` — 取引（収入・支出）一覧取得
- `get_deal` — 取引詳細取得
- `create_deal` — 取引作成
- `list_invoices` — 請求書一覧取得
- `create_invoice` — 請求書作成
- `list_partners` — 取引先一覧取得
- `create_partner` — 取引先作成
- `list_account_items` — 勘定科目一覧取得

## セットアップ

```bash
cd freee
pip install -e .
```

環境変数を設定：

```bash
export FREEE_ACCESS_TOKEN=your_oauth_access_token
export FREEE_COMPANY_ID=your_company_id  # list_companies で確認
```

## 前提

- freee会計 のアカウントが必要
- OAuth2 アクセストークンが必要（freee Developers Console でアプリ登録）
- API ドキュメント: https://developer.freee.co.jp/reference/accounting/reference

## Claude Desktop への登録例

```json
{
  "mcpServers": {
    "freee": {
      "command": "freee-mcp",
      "env": {
        "FREEE_ACCESS_TOKEN": "your_token",
        "FREEE_COMPANY_ID": "123456"
      }
    }
  }
}
```
