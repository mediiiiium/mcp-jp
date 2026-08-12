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
| `get_workflow_request` | ワークフロー申請を1件、申請ID指定で詳細取得（管理者権限不要。申請者本人や処理経路上の承認者など、そのリクエストへのアクセス権があれば取得可） |
| `get_presence` | 指定ユーザー1人の在席情報を取得（一括取得APIはなし） |
| `get_organizations` | 組織（部署）一覧を取得（組織名の部分一致絞り込み可、管理者権限不要） |
| `get_organization_users` | 指定した組織に所属するユーザー一覧を取得（管理者権限不要） |
| `get_facilities` | スケジュールに紐づけ可能な施設（会議室等）の一覧を取得（施設名の部分一致絞り込み可、管理者権限不要） |

## 既知の制約

- **予定の更新・削除は未実装**: Garoon REST API には `PATCH /schedule/events/{id}`（更新）・`DELETE /schedule/events/{id}`（削除）が存在するが、本コネクタには対応するツールがない。予定の修正・取り消しは Garoon の画面から行う必要がある。
- **予定登録時の施設指定は未対応**: Garoon API の仕様上、予定作成時は参加者（attendees）または施設（facilities）のどちらかの指定が必須だが、本コネクタは参加者指定のみに対応。会議室などの施設を予定に紐づけたい場合は画面側で追加する必要がある（`get_facilities` で施設IDの確認は可能になったが、予定登録時の紐付け自体は未対応）。
- **予定登録は冪等ではない**: `create_event` を同じ内容で複数回呼び出すと、Garoon API 側に重複防止の仕組みがないため予定が重複登録される。
- **ワークフロー申請一覧は管理者専用**: `list_workflow_requests` が使う `/workflow/admin/requests` は cybozu.com 共通管理者権限またはワークフローアプリケーション管理者権限が前提。一般ユーザーが自分の申請一覧だけを取得するエンドポイントは Garoon API 自体に存在しない（`get_workflow_request` はID指定の単体取得のみ対応）。
- **在席情報は1人ずつのみ**: `get_presence` は Garoon API の仕様上ユーザー単位の個別取得のみで、複数ユーザーをまとめて取得する一括APIはGaroon側に存在しない。また在席状態の更新（PATCH）も本コネクタには未実装。
- **ページネーションは offset/limit 方式**: 各一覧系ツールはレスポンスの `hasNext` が `true` の場合、`offset` に「現在のoffset + limit」を入れて再取得することで続きを取得できる。Garoon API 上の1回あたり取得件数の上限は1000件。
- **ToDoリストは未実装**: Garoon API には `GET /todo/todos/{id}`（ID指定の単体取得のみ、一覧APIなし）・`POST /todo/todos`（登録）・`GET /todo/categories`（カテゴリ一覧）が存在するが、本コネクタには実装していない。単体取得しかできず「今日のToDo一覧を見せて」のような一覧確認ができないため、AIエージェント経由での実用性が低いと判断した。
- **掲示板・メッセージ・スペース（ディスカッション）・通知は未実装**: Garoon API にはそれぞれ一覧/取得/作成/更新/削除のエンドポイントが存在するが（例: 掲示板の `GET /bulletin/categories/{id}` カテゴリ内一覧、メッセージの `GET /message/messages` 一覧・`POST /message/messages` 作成、スペースの `GET /space/spaces` 一覧、通知の `GET・POST /notification/items`）、本コネクタでは未実装。理由は主に2点。(1) 社内SNS的な情報流通が中心で、スケジュール・ワークフロー・組織/ユーザーという業務コア領域からは外れる。(2) 作成系（メッセージ送信・掲示書き込み・ディスカッション投稿）は「載せたものは全部ちゃんと動く」を本数より優先する方針の下、書き込み系は特に慎重に扱うべき対象であり、今回の深掘りでは読み取り系も含めて対象外とした。将来ニーズが確認できれば改めて検討する。

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

```
営業部の組織IDを教えて
```

```
組織ID 5 に所属するメンバーを一覧表示して
```

```
申請ID 123 の承認状況を確認して
```

```
使える会議室の一覧を教えて
```
