# twilio-mcp

Twilio（SMS・音声通話）の MCP サーバー。SMS送信・メッセージ確認・電話番号管理を AI から操作できます。

## セットアップ

```bash
cd twilio
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `TWILIO_ACCOUNT_SID` | Twilio アカウント SID（AC で始まるID） |
| `TWILIO_AUTH_TOKEN` | Twilio 認証トークン |

### 認証情報の取得

1. [Twilio Console](https://console.twilio.com) にログイン
2. ダッシュボードの「Account Info」セクションから取得

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "twilio": {
      "command": "twilio-mcp",
      "env": {
        "TWILIO_ACCOUNT_SID": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "TWILIO_AUTH_TOKEN": "your_auth_token_here"
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `send_sms` | SMS メッセージを送信する |
| `list_messages` | 送受信メッセージ一覧を取得 |
| `get_message` | メッセージSIDを指定して詳細を取得 |
| `list_phone_numbers` | アカウントの電話番号一覧を取得 |
| `get_account` | アカウント情報を取得 |

## 使用例

```
+819012345678 へ「ご注文を承りました」とSMSを送って
```

```
今日送信したメッセージ一覧を見せて
```

```
メッセージ SM_xxxxx の配信状況を確認して
```

```
アカウントに登録されている電話番号を教えて
```
