# sendgrid-mcp

SendGrid（メール送信・マーケティング）の MCP サーバー。メール送信・統計確認・バウンス管理を AI から操作できます。

## セットアップ

```bash
cd sendgrid
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `SENDGRID_API_KEY` | SendGrid APIキー（`SG.` で始まるキー） |

### APIキーの取得

1. SendGrid にログイン
2. 「Settings」→「API Keys」→「Create API Key」
3. 必要なスコープ: `Mail Send`, `Stats`, `Suppressions`, `Templates`

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "sendgrid": {
      "command": "sendgrid-mcp",
      "env": {
        "SENDGRID_API_KEY": "SG.your_api_key_here"
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `send_email` | メールを送信する |
| `get_stats` | 送信統計（配信数・開封率・クリック率等）を取得 |
| `list_bounces` | バウンス（送信失敗）アドレス一覧を取得 |
| `list_unsubscribes` | 配信停止アドレス一覧を取得 |
| `list_templates` | 動的テンプレート一覧を取得 |

## 使用例

```
support@example.com から user@example.com へ「お問い合わせありがとうございます」とメールを送って
```

```
今週のメール送信統計を見せて
```

```
バウンスしているメールアドレス一覧を教えて
```

```
配信停止リストを確認して
```

```
登録されているメールテンプレート一覧を見せて
```
