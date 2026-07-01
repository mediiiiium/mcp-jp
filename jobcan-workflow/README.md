# jobcan-workflow-mcp

ジョブカン経費精算/ワークフローの MCP サーバー。申請書の確認・ユーザー・プロジェクト・取引先情報を AI から操作できます。

## セットアップ

```bash
cd jobcan-workflow
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `JOBCAN_API_TOKEN` | ジョブカン APIトークン（管理画面の「共通ID連携・API管理」から発行） |

### APIトークンの取得

1. ジョブカン経費精算/ワークフローにログイン
2. 管理者画面 → 「共通ID連携・API管理」タブ
3. 「認証コード発行」画面で「発行する」をクリック

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "jobcan-workflow": {
      "command": "jobcan-workflow-mcp",
      "env": {
        "JOBCAN_API_TOKEN": "your_api_token_here"
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_requests` | 申請書一覧を取得（ステータス・申請者・グループ・プロジェクト・日付範囲・並び順などで絞り込み可、GET /v2/requests/） |
| `get_request` | 申請書1件の詳細情報を取得（GET /v2/requests/{id}/） |
| `list_users` | ユーザー一覧を取得（GET /v3/users/） |
| `list_projects` | プロジェクト一覧を取得（GET /v1/projects/） |
| `list_companies` | 取引先一覧を取得（GET /v1/company/） |

すべて読み取り専用（GET）のツールのみを実装しています。

## 既知の制約

- **承認・却下・差し戻し操作なし**: ジョブカン経費精算/ワークフローAPIには申請の承認・却下・差し戻しを行うエンドポイントが存在しない（承認操作はWeb画面上でのみ可能）。本コネクタは申請の閲覧のみに対応する。
- **ユーザー・プロジェクト・取引先の作成/更新/削除は未実装**: API自体には `POST` / `PUT` / `DELETE` のエンドポイントが存在するが（例: `POST /v1/projects/` でプロジェクト作成、`DELETE /v1/users/{user_code}/` でユーザー無効化）、本コネクタでは書き込みによる副作用のリスクを避けるため一覧・詳細取得（GET）のみを実装している。
- **日付パラメータの形式**: `list_requests` の日付系パラメータ（`applied_after` / `applied_before` / `completed_after` / `completed_before`）は `yyyy/mm/dd` または `yyyy/mm/dd hh:mm:ss` 形式で指定する必要がある（ハイフン区切りの `YYYY-MM-DD` は不可）。
- **ページネーション**: `list_requests` は1ページ100件固定・レスポンスに `next`/`previous`/`count` を含む。`list_users` / `list_projects` / `list_companies` も同様にページ番号方式だが、1ページあたりの件数や既定の並び順はAPIドキュメントに明記されておらず未検証。
- **絞り込みパラメータの非対称性**: `list_requests` はAPI側で豊富な絞り込みパラメータ（`id` / `status` / `form_id` / `title` / `applicant_code` / `group_code` / `project_code` / 日付範囲 / `include_canceled` / `sort_by`）に対応しているが、`list_users` / `list_projects` / `list_companies` はAPIドキュメント上 `page` 以外の絞り込みパラメータが確認できない。

## 使用例

```
今月の申請書をすべて見せて
```

```
進行中の申請書一覧を表示して
```

```
申請書ID 12345 の詳細を見せて
```

```
ユーザー一覧を取得して
```

```
登録されているプロジェクト一覧を教えて
```
