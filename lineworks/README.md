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
| `list_channels` | Bot が参加しているトークルーム一覧を取得 |
| `send_channel_message` | トークルームにメッセージを送信 |
| `send_user_message` | ユーザーにDMを送信 |
| `list_members` | テナントのメンバー一覧を取得 |
| `get_member` | 特定メンバーの詳細情報を取得 |

## 認証について

LINE WORKS API v2 は JWT（RS256）を使った Service Account 認証を使用します。  
秘密鍵はDeveloper Console → アプリ → 認証キー から取得・生成できます。

## 使用例

```
全社チャンネルに「本日のメンテナンスは22時から24時です」と通知して
```

```
メンバー一覧を見せて
```
