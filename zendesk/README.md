# zendesk-mcp

Zendesk（カスタマーサポート）の MCP サーバー。サポートチケットの管理・検索・作成を AI から操作できます。

## セットアップ

```bash
cd zendesk
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `ZENDESK_EMAIL` | Zendesk アカウントのメールアドレス |
| `ZENDESK_API_TOKEN` | Zendesk APIトークン（管理者設定から発行） |
| `ZENDESK_SUBDOMAIN` | サブドメイン（`yourcompany.zendesk.com` の `yourcompany` 部分） |

### APIトークンの取得

1. Zendesk 管理者画面にログイン
2. 「管理センター」→「アプリとインテグレーション」→「API」→「Zendesk API」
3. 「APIトークンを追加する」でトークンを発行

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "zendesk": {
      "command": "zendesk-mcp",
      "env": {
        "ZENDESK_EMAIL": "your@email.com",
        "ZENDESK_API_TOKEN": "your_api_token_here",
        "ZENDESK_SUBDOMAIN": "your-subdomain"
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_tickets` | チケット一覧を取得（ソート条件指定可） |
| `get_ticket` | チケットIDを指定して詳細を取得 |
| `create_ticket` | 新しいサポートチケットを作成 |
| `search_tickets` | キーワードやステータス・優先度でチケットを検索 |
| `list_users` | ユーザー一覧を取得（エージェント・エンドユーザー） |

## 使用例

```
未解決のチケット一覧を見せて
```

```
緊急のチケットをすべて検索して
```

```
チケット #12345 の詳細を教えて
```

```
「ログインできない」というタイトルで優先度高のチケットを作成して
```

```
エージェント一覧を表示して
```
