# chatwork-mcp

Chatwork（ビジネスチャット）の MCP サーバー。チャットルームのメッセージ送受信・タスク管理を AI から操作できます。

## セットアップ

```bash
cd chatwork
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `CHATWORK_API_TOKEN` | Chatwork API トークン（個人設定から取得） |

### APIトークンの取得

1. Chatwork にログイン
2. 右上のプロフィールメニュー → 「サービス連携」
3. 「API トークン」セクションでトークンを発行

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "chatwork": {
      "command": "chatwork-mcp",
      "env": {
        "CHATWORK_API_TOKEN": "your_api_token_here"
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `get_me` | 自分のアカウント情報を取得 |
| `list_rooms` | 参加しているチャットルーム一覧を取得 |
| `get_room_messages` | チャットルームのメッセージ一覧を取得 |
| `send_message` | チャットルームにメッセージを送信 |
| `list_room_tasks` | チャットルームのタスク一覧を取得 |

## 使用例

```
参加しているチャットルームの一覧を見せて
```

```
ルームID 12345 の未読メッセージを確認して
```

```
「開発チーム」のルームに「定例会議は15時からです」と送って
```

```
プロジェクトルームのオープンタスクを一覧表示して
```
