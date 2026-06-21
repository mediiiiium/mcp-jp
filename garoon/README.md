# garoon-mcp

Garoon（サイボウズ グループウェア）の MCP サーバー。スケジュール・ワークフロー・ユーザー情報を AI から操作できます。

## セットアップ

```bash
cd garoon
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `GAROON_LOGIN_NAME` | Garoon ログイン名 |
| `GAROON_PASSWORD` | Garoon パスワード |
| `GAROON_SUBDOMAIN` | サブドメイン（URLの `xxxx.cybozu.com` の `xxxx` 部分） |

### 接続先URL

`https://{GAROON_SUBDOMAIN}.cybozu.com/g/api/v1`

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "garoon": {
      "command": "garoon-mcp",
      "env": {
        "GAROON_LOGIN_NAME": "your_login_name",
        "GAROON_PASSWORD": "your_password",
        "GAROON_SUBDOMAIN": "your-subdomain"
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_events` | スケジュールの予定一覧を取得（日時範囲・ユーザー指定可） |
| `create_event` | スケジュールに新しい予定を登録 |
| `list_users` | ユーザー一覧を取得（名前での絞り込み可） |
| `list_workflow_requests` | ワークフロー申請一覧を取得（ステータス絞り込み可） |
| `get_presence` | 指定ユーザーの在席情報を取得 |

## 使用例

```
今週の予定を見せて
```

```
明日の14時から15時で「週次ミーティング」の予定を作って
```

```
社員の一覧を見せて
```

```
承認待ちのワークフロー申請をすべて表示して
```

```
ユーザーID 1 の在席状況を確認して
```
