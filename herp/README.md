# herp-mcp

HERP Hire（日本向け採用管理システム）の MCP サーバー。公式 MCP 未提供。

- API ドキュメント: https://public-api.herp.cloud/hire/public/doc
- 利用ガイド: https://help.herp.cloud/ja/articles/HERP-Hire-API-86ba917e

## セットアップ

```bash
cd herp
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `HERP_API_KEY` | HERP Hire の API キー（管理画面 → API設定から取得） |  # pragma: allowlist secret

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "herp": {
      "command": "herp-mcp",
      "env": {
        "HERP_API_KEY": "your_api_key_here"  # pragma: allowlist secret
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_candidacies` | 応募者（選考）一覧を取得。求人ID・選考状況(status)・選考ステップ(step)・終了理由・応募日時/ステップ更新日時の範囲で絞り込み可。1ページ100件固定のページネーション（page指定）。読み取り専用 |
| `get_candidacy` | 応募者1件の詳細情報を取得。読み取り専用 |
| `list_contacts` | 応募者1名分のコンタクト（面談・面接などの選考記録）一覧を取得（ページネーションなし、全件返却）。読み取り専用 |
| `list_candidacy_files` | 応募者に添付されたファイル（履歴書・職務経歴書等）のメタ情報一覧を取得（バイナリ実体は非対応）。読み取り専用 |
| `list_assignments` | 応募者にアサインされた担当者（userId・role）一覧を取得。実名は `list_users` で突き合わせ。読み取り専用 |
| `get_evaluation` | 評価依頼1件の設問・回答内容を取得（評価IDは `get_candidacy`/`list_contacts` から入手）。読み取り専用 |
| `list_requisitions` | 求人（ポジション）一覧を取得。募集状況・採用ページ掲載状況で絞り込み可。1ページ100件固定のページネーション（page指定）。読み取り専用 |
| `list_requisition_groups` | 求人グループ（求人をまとめる区分）一覧を取得（ページネーションなし、全件返却）。読み取り専用 |
| `get_requisition_group` | 求人グループ1件の詳細情報を取得。読み取り専用 |
| `list_users` | HERP Hire ユーザー（社内メンバー）一覧を取得。在籍状況(status)・権限(role)で絞り込み可。1ページ100件固定のページネーション（page指定）。読み取り専用 |
| `list_timeline_comments` | 応募者1名分のタイムラインコメント一覧を取得（ページネーションなし、全件返却）。読み取り専用 |
| `add_timeline_comment` | 応募者のタイムラインにコメントを追加（書式・メンション指定可、べき等ではない。唯一の書き込み系ツール） |

## 既知の制約

HERP Hire API のページネーションは `page`（ページ番号、1ページ100件固定）方式であり、`limit`/`offset` は指定できません（`list_candidacies` / `list_requisitions` / `list_users` が対象。`hasNextPage` が true の間 `page` を +1 して取得します）。認証は Bearer トークン、テナントあたり毎分100リクエストのレート制限があります（超過時は HTTP 429）。

以下のエンドポイントは HERP Hire API に存在しないため、本コネクタにも対応するツールはありません（HERP Hire 管理画面から操作してください）。

- 応募者（candidacy）・求人（requisition）・求人グループ・ユーザー・タイムラインコメントいずれの削除
- 求人（requisition）・求人グループ・ユーザー自体の作成・更新
- タイムラインコメントの編集・削除
- 評価(evaluation)の一覧取得（評価IDは `get_candidacy` / `list_contacts` のレスポンス経由でのみ入手可能）

### 2026-07-13 の深掘りで確認した内容

公式APIドキュメント（`https://public-api.herp.cloud/hire/public/doc`。2026年2月に正式提供開始）を確認し、未実装だった読み取り系エンドポイントを以下のとおり追加実装しました。

- `list_contacts`（GET /candidacies/{id}/contacts）、`list_candidacy_files`（GET /candidacies/{id}/files）、`list_assignments`（GET /candidacies/{id}/assignments）、`get_evaluation`（GET /evaluations/{id}）、`list_requisition_groups`（GET /requisition-groups）、`get_requisition_group`（GET /requisition-groups/{id}）、`list_users`（GET /users）

一方、以下は実在を確認したうえで、既存の「読み取り中心・応募（candidacy）閲覧＋コメント」設計から外れるため今回は見送りました（必要になれば追加実装を検討）。

- **応募ファイルのバイナリ取得（GET /candidacies/{id}/files/{fileId}）**: 実体はバイナリ（履歴書PDF等）を返す仕様であり、テキストベースの本コネクタ（レスポンスをJSON整形して返す設計）では扱えないため見送った。メタ情報の確認は `list_candidacy_files` で可能。
- **書き込み系（POST/PATCH/PUT/DELETE）**: `add_timeline_comment` を除き見送った。具体的には、応募作成（POST /candidacies）、選考ステップ更新（PATCH /candidacies/{id}/step）、選考終了（PATCH /candidacies/{id}/termination）、応募ファイル追加（POST /candidacies/{id}/files）、コンタクト作成（POST /candidacies/{id}/contacts）、評価提出・更新（PUT /evaluations/{id}）、担当者アサインの追加・解除（POST/DELETE /candidacies/{id}/assignments）。いずれも選考状態を実際に変更する破壊的操作であり、本コネクタの読み取り中心の設計方針から外れるため見送った。これらの操作は HERP Hire 管理画面から行ってください。

## 使用例

```
エンジニア採用の応募者を全員リストアップして
```

```
田中さんの選考にコメント「一次面接通過、二次面接調整中」を追加して
```
