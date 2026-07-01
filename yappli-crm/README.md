# yappli-crm-mcp

Yappli CRM（モバイルアプリ向けノーコードCRM・会員管理）の MCP サーバー。公式 MCP 未提供。

## セットアップ

```bash
cd yappli-crm
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `YAPPLI_CRM_APP_URL` | Yappli CRM のアプリURL（例: `https://your-app.yappli.co`） |
| `YAPPLI_CRM_CLIENT_ID` | 管理画面で発行したOAuth クライアントID |
| `YAPPLI_CRM_CLIENT_SECRET` | 管理画面で発行したOAuth クライアントシークレット |  # pragma: allowlist secret

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "yappli-crm": {
      "command": "yappli-crm-mcp",
      "env": {
        "YAPPLI_CRM_APP_URL": "https://your-app.yappli.co",
        "YAPPLI_CRM_CLIENT_ID": "your_client_id",
        "YAPPLI_CRM_CLIENT_SECRET": "your_client_secret_here"  # pragma: allowlist secret
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_users` | 会員一覧を取得する（ページネーション: page/per_page、最大1000件・既定50件） |
| `get_user` | YappliCRM会員IDで会員1件の詳細を取得する |
| `get_user_by_unique_id` | お客様側システムの一意な識別子（unique_id）で会員を検索する |
| `get_user_by_external_id` | 外部連携キー・外部連携IDで会員を検索する |
| `create_user` | 新規会員を登録する（会員の削除APIは提供されていない） |
| `update_user` | 既存会員の情報を更新する |
| `delete_external_id` | 会員の外部連携IDを1件削除する（べき等ではない） |
| `get_user_points` | 会員のポイント付与・減算履歴を取得する（登録日の新しい順） |
| `get_points_expired_list` | 会員のポイントを有効期限日ごとに集計して取得する |
| `add_user_points` | 会員にポイントを付与または減算する（べき等ではない） |
| `calculate_points` | ランク別付与率で自動計算したポイントを会員に付与する（減算不可・べき等ではない） |

## API上の注意点・制限事項

- Yappli CRM Open APIには氏名・メールアドレス・生年月日・性別のような固定の個人情報フィールドは存在しない。
  これらは `column01`〜`column50`（または管理画面で設定したキー名）のカスタムフィールドとして
  `create_user`/`update_user` の `columns` パラメータ経由で設定する。
- 会員そのものを削除するAPIは提供されていない（削除できるのは外部連携IDのみ）。
- ポイント付与系API（`add_user_points`/`calculate_points`）はべき等ではなく、呼び出すたびに新しい
  付与・減算レコードが追加される。
- ページネーションはすべてオフセット方式（`page`/`per_page`）。カーソル方式は使用されていない。
- アクセストークンの有効期間は発行から24時間（`expires_in: 86400`）。

## 使用例

```
会員一覧を取得して
```

```
会員ID user_001 のポイント履歴を見せて
```

```
会員ID user_001 に500ポイントを付与して、理由は「誕生日ポイント」
```

```
ログインID test@example.com、パスワードpass1234で新規会員を登録して
```
