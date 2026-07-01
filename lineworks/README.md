# lineworks-mcp

LINE WORKS（日本SMB向けビジネスチャット・グループウェア）の MCP サーバー。公式 MCP 未提供（コミュニティ開発中）。

## セットアップ

```bash
cd lineworks
pip install -e .
```

## 前提条件

LINE WORKS Developer Console でアプリを作成し、以下を取得してください：
- OAuth App の `Client ID` / `Client Secret`
- `Service Account ID`
- `Private Key`（RSA秘密鍵、PEM形式）
- Bot ID

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `LINEWORKS_CLIENT_ID` | OAuth App の Client ID |
| `LINEWORKS_CLIENT_SECRET` | OAuth App の Client Secret |  # pragma: allowlist secret
| `LINEWORKS_SERVICE_ACCOUNT_ID` | Service Account ID |
| `LINEWORKS_PRIVATE_KEY` | RSA 秘密鍵（PEM形式、改行は `\n` に置換して1行で設定） |
| `LINEWORKS_BOT_ID` | Bot ID（メッセージ送信に必要） |

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "lineworks": {
      "command": "lineworks-mcp",
      "env": {
        "LINEWORKS_CLIENT_ID": "your_client_id",
        "LINEWORKS_CLIENT_SECRET": "your_client_secret",  # pragma: allowlist secret
        "LINEWORKS_SERVICE_ACCOUNT_ID": "your_service_account_id",
        "LINEWORKS_PRIVATE_KEY": "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----",  # pragma: allowlist secret
        "LINEWORKS_BOT_ID": "your_bot_id"
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `get_channel` | 指定した channel_id のトークルーム1件の情報を取得 |
| `send_channel_message` | トークルームにテキストメッセージを送信（べき等ではない） |
| `send_user_message` | ユーザーにテキストDMを送信（べき等ではない） |
| `list_members` | テナントのメンバー一覧を取得（カーソルページネーション、count/order_by/sort_order/search_filter_type 対応） |
| `get_member` | 特定メンバー（ユーザーID/ログインID/externalKey）の詳細情報を取得 |

## API の既知の制限事項

- **トークルーム一覧取得APIは存在しない**: LINE WORKS Bot API には「Bot が参加している全トークルームの一覧」を
  返すエンドポイントが存在しません（公式ドキュメント・コミュニティフォーラムで確認済み）。取得できるのは
  `GET /bots/{botId}/channels/{channelId}` による特定チャンネル1件の情報のみで、channel_id は Bot への着信
  webhook イベントなどから事前に把握しておく必要があります（`get_channel` ツール）。
- **メッセージの取消・編集は不可**: 送信済みメッセージを取り消す・編集するAPIはLINE WORKS Bot APIに存在しません。
  送信はべき等ではないため、同じ内容で複数回呼び出すと重複送信されます。
- **トークルーム作成APIは未実装**: `POST /bots/{botId}/channels`（メンバー1〜100名を指定して新規トークルーム
  を作成）は LINE WORKS 側に存在しますが、本コネクタでは実装していません。
- **ユーザーの作成・更新・削除APIは未実装**: 本コネクタは読み取り専用（`list_members`/`get_member`）です。

## 認証について

LINE WORKS API v1.0 は JWT（RS256）を使った Service Account 認証を使用します。  
秘密鍵はDeveloper Console → アプリ → 認証キー から取得・生成できます。

## 使用例

```
全社チャンネルに「本日のメンテナンスは22時から24時です」と通知して
```

```
メンバー一覧を見せて
```
