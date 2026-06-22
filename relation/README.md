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
| `list_message_boxes` | 受信箱（メールボックス）一覧を取得 |
| `search_tickets` | チケット（問い合わせ）を検索（ステータス・キーワード・担当者で絞り込み可） |
| `get_ticket` | チケットの詳細情報を取得 |
| `create_reply_memo` | チケットに内部対応メモを作成 |
| `list_users` | オペレーター一覧を取得 |

## 使用例

```
未対応の問い合わせ一覧を見せて
```

```
「返金」というキーワードで問い合わせを検索して
```

```
チケット ID 456 に「折り返し電話確認済み」というメモを追加して
```
