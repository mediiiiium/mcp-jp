# jooto-mcp

Jooto（日本SMB向けタスク・プロジェクト管理ツール）の MCP サーバー。公式 MCP 未提供。

## セットアップ

```bash
cd jooto
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `JOOTO_API_KEY` | Jooto 管理画面で発行した API キー |  # pragma: allowlist secret

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "jooto": {
      "command": "jooto-mcp",
      "env": {
        "JOOTO_API_KEY": "your_api_key_here"  # pragma: allowlist secret
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `get_organization` | この API キーが紐づく組織1件の情報を取得（Jooto の API キーは組織ごとに発行されるため常に1件のみ） |
| `list_boards` | 組織内のプロジェクト（ボード）一覧を取得（archived・並び順で絞り込み可） |
| `list_lists` | プロジェクト内のリスト（カンバンの列）一覧を取得。create_task に渡す list_id を調べる目的で使う |
| `list_tasks` | プロジェクト内のタスク一覧を取得（担当者・ラベル・ステータス・締め切り期間・フォロー状態・アーカイブ状態で絞り込み可） |
| `create_task` | 新しいタスクを作成（list_id が必須） |
| `get_task` | タスクの詳細情報を取得 |

## 使用例

```
営業チームのボードにあるタスク一覧を見せて
```

```
「Webサイト改善」ボードの「未着手」リストに「ランディングページ修正」というタスクを作成して、期限は2026-07-31
```

```
進行中（in_progress）のタスクの一覧を表示して
```

## 既知の制約

Jooto API（公式リファレンス: https://www.jooto.com/api/reference/request/）には以下のエンドポイントも
存在するが、本コネクタには実装していない（必要な場合は Jooto の管理画面、または Jooto API を直接呼び
出して操作してください）。

- 組織情報の更新（`PATCH /v1/organization`）
- プロジェクト・リスト・タスクの更新、アーカイブ／復元、削除（削除はいずれもアーカイブ済みのものが対象）
- タスクのフリーワード検索（`GET /v1/boards/{id}/search`）— `list_tasks` は担当者・ラベル・ステータス等の
  条件絞り込みのみで、名前の部分一致検索はできない
- コメント・チェックリスト・添付ファイル・ラベル（カテゴリー）・メンバー管理などタスク付随情報の
  作成・取得・更新・削除
- ユーザー一覧・お知らせ一覧・レート制限情報の取得

なお、Jooto の API キーは組織ごとに発行されるため「所属組織の一覧」という概念自体が API に存在せず、
`get_organization` は常にキーに紐づく組織1件のみを返す。

## API 利用条件

Jooto API の利用には対応プランへの加入が必要（詳細は https://www.jooto.com/api/ を参照）。組織の設定
ページから API キーを発行できる。リクエスト数にはプランごとの分単位レート制限があり、上限に達すると
HTTP 429 が返る。
