# base-ec-mcp

BASE（ECプラットフォーム）の MCP サーバー。ショップの商品管理・注文管理を AI から操作できます。

## セットアップ

```bash
cd base-ec
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `BASE_ACCESS_TOKEN` | BASE APIアクセストークン（OAuth2.0で取得） |

### アクセストークンの取得

1. [BASE Developers](https://developers.thebase.com/) でアプリ登録・審査申請
2. 承認後、OAuth2.0認証フローでアクセストークンを取得
   - 認証URL: `https://api.thebase.in/1/oauth/authorize`
   - トークンURL: `https://api.thebase.in/1/oauth/token`
3. 取得したアクセストークンを環境変数に設定

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "base-ec": {
      "command": "base-ec-mcp",
      "env": {
        "BASE_ACCESS_TOKEN": "your_access_token_here"
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `get_shop` | ショップ情報（名前・URL・説明等）を取得 |
| `list_items` | 商品一覧を取得（件数・ソート条件指定可） |
| `list_orders` | 注文一覧を取得（日付・ステータスで絞り込み可） |
| `get_order` | 注文の詳細情報を取得 |
| `update_order_status` | 注文を発送済みに更新 |

## 使用例

```
ショップの情報を見せて
```

```
登録されている商品の一覧を表示して
```

```
今月の注文をすべて見せて
```

```
未発送の注文一覧を教えて
```

```
注文 abc123 の詳細を見せて
```

```
注文 abc123 を発送済みに更新して
```
