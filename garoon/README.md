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
| `list_events` | スケジュールの予定一覧を取得（日時範囲・ユーザー/組織/施設指定可。target/target_type省略時は実行ユーザー自身の予定のみ） |
| `create_event` | スケジュールに新しい予定を1件登録（参加者指定のみ対応、施設指定は未対応。冪等ではない） |
| `list_users` | ユーザー一覧を取得（名前での部分一致絞り込み可。並び順はユーザーIDの昇順固定） |
| `list_workflow_requests` | ワークフロー申請一覧を取得（管理者権限が前提のエンドポイント。ステータス絞り込み可） |
| `get_presence` | 指定ユーザー1人の在席情報を取得（一括取得APIはなし） |

## 既知の制約

- **予定の更新・削除は未実装**: Garoon REST API には `PATCH /schedule/events/{id}`（更新）・`DELETE /schedule/events/{id}`（削除）が存在するが、本コネクタには対応するツールがない。予定の修正・取り消しは Garoon の画面から行う必要がある。
- **予定登録時の施設指定は未対応**: Garoon API の仕様上、予定作成時は参加者（attendees）または施設（facilities）のどちらかの指定が必須だが、本コネクタは参加者指定のみに対応。会議室などの施設を予定に紐づけたい場合は画面側で追加する必要がある。
- **予定登録は冪等ではない**: `create_event` を同じ内容で複数回呼び出すと、Garoon API 側に重複防止の仕組みがないため予定が重複登録される。
- **ワークフロー申請一覧は管理者専用**: `list_workflow_requests` が使う `/workflow/admin/requests` は cybozu.com 共通管理者権限またはワークフローアプリケーション管理者権限が前提。一般ユーザーが自分の申請だけを取得するツールは用意していない。
- **在席情報は1人ずつのみ**: `get_presence` は Garoon API の仕様上ユーザー単位の個別取得のみで、複数ユーザーをまとめて取得する一括APIはGaroon側に存在しない。また在席状態の更新（PATCH）も本コネクタには未実装。
- **ページネーションは offset/limit 方式**: 各一覧系ツールはレスポンスの `hasNext` が `true` の場合、`offset` に「現在のoffset + limit」を入れて再取得することで続きを取得できる。Garoon API 上の1回あたり取得件数の上限は1000件。

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
