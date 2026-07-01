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
| `send_email` | メールを1通送信する（宛先1名のみ。CC/BCC・添付・動的テンプレート・送信予約は非対応）。**冪等性なし**：同じ内容で2回呼ぶと2通届く |
| `get_stats` | 送信統計（配信数・開封数・クリック数・バウンス数等）を日別/週別/月別で取得。limit/offsetでページング可 |
| `list_bounces` | バウンス（配信失敗）抑制リストを取得。email・start_time/end_timeで絞り込み、limit/offsetでページング（最大500件） |
| `list_unsubscribes` | グローバル配信停止（Global Suppressions）リストを取得。email・start_time/end_timeで絞り込み、limit/offsetでページング（最大500件） |
| `list_templates` | テンプレート一覧を取得（legacy/dynamic切替、page_tokenでページング） |

### 制限事項

- `send_email` は SendGrid Mail Send API 側に重複排除・冪等性キーの仕組みが無いため、リトライや二重送信に注意が必要です。
- バウンス抑制リストの削除（`DELETE /v3/suppression/bounces`）や配信停止リストへの追加・個別解除（`POST`/`DELETE /v3/suppression/unsubscribes`）に対応する API は SendGrid 側に存在しますが、本コネクタでは未実装（一覧取得のみ）です。
- `send_email` の `from_email` は SendGrid で送信者確認（Single Sender Verification）またはドメイン認証済みである必要があります。

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
