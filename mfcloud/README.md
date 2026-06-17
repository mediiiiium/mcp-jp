# mfcloud MCP

マネーフォワードクラウド請求書 の MCP サーバー。

Claude 等のAIエージェントからMFクラウド請求書を操作できます。

## 利用可能なツール

- `get_office` — 事業者（自社）情報取得
- `list_partners` — 取引先一覧取得
- `create_partner` — 取引先作成
- `list_items` — 品目一覧取得
- `create_item` — 品目作成
- `list_billings` — 請求書一覧取得
- `get_billing` — 請求書詳細取得
- `create_billing` — 請求書作成
- `update_billing` — 請求書更新（下書きのみ）

## セットアップ

```bash
cd mfcloud
pip install -e .
```

環境変数を設定：

```bash
export MFCLOUD_ACCESS_TOKEN=your_oauth_access_token
```

## 前提

- マネーフォワードクラウド請求書 のアカウントが必要
- OAuth2 アクセストークンが必要（MFクラウド Developers Console でアプリ登録）
- API ドキュメント: https://invoice.moneyforward.com/docs/api/v3/index.html

## Claude Desktop への登録例

```json
{
  "mcpServers": {
    "mfcloud": {
      "command": "mfcloud-mcp",
      "env": {
        "MFCLOUD_ACCESS_TOKEN": "your_token"
      }
    }
  }
}
```
