# trello-mcp

Trello MCP サーバー。ボード・リスト・カードの管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `TRELLO_API_KEY` | ✅ | Trello API キー |
| `TRELLO_TOKEN` | ✅ | Trello アクセストークン |

## 認証情報取得方法

1. [Trello Developer Portal](https://trello.com/app-key) にアクセス
2. **API Key** をコピー
3. 同ページの **Token** リンクをクリックして権限を付与し、Token をコピー

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_boards` | ボード一覧を取得する |
| `list_lists` | ボード内のリスト一覧を取得する |
| `list_cards` | リスト内のカード一覧を取得する |
| `create_card` | 新しいカードを作成する |
| `move_card` | カードを別のリストに移動する |

## インストール

```bash
cd trello
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "trello": {
      "command": "trello-mcp",
      "env": {
        "TRELLO_API_KEY": "your_trello_api_key",  # pragma: allowlist secret
        "TRELLO_TOKEN": "your_trello_token"  # pragma: allowlist secret
      }
    }
  }
}
```
