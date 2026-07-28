# jobcan-workflow-mcp

ジョブカン経費精算/ワークフローの MCP サーバー。申請書・フォーム・ユーザー・グループ（部署）・役職・プロジェクト・取引先・汎用マスタといったマスタ情報を AI から読み取れます。

- API ドキュメント（β版）: https://ssl.wf.jobcan.jp/api_doc
- ベースURL: `https://ssl.wf.jobcan.jp/wf_api`
- レート制限: 1アクセストークンあたり1時間5,000リクエスト

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
| `get_request` | 申請書1件の詳細情報を取得（GET /v2/requests/{id}/。※下記「既知の制約」参照） |
| `list_forms` | 申請フォーム（様式）一覧を取得（種別・精算種別・名前・公開範囲などで絞り込み可、GET /v1/forms/）。`list_requests` の `form_id` を調べる起点 |
| `list_users` | ユーザー一覧を取得（GET /v3/users/。memo 欄を含む） |
| `get_user` | ユーザー1人の詳細を取得（承認権限・所属・役職・振込口座など、GET /v1/users/{user_code}/） |
| `list_groups` | グループ（部署）一覧を取得（GET /v1/groups/）。`list_requests` の `group_code` を調べる起点 |
| `list_positions` | 役職一覧を取得（GET /v1/positions/） |
| `list_projects` | プロジェクト一覧を取得（GET /v1/projects/） |
| `list_companies` | 取引先一覧を取得（GET /v1/company/） |
| `get_company` | 取引先1件の詳細を取得（振込先口座・適格請求書登録番号・住所など、GET /v1/company/{company_code}/） |
| `get_generic_master` | 汎用マスタ1件のレコード一覧を取得（GET /v1/generic_master/{code}/）。費目・勘定科目など独自マスタの中身確認用 |
| `validate_token` | APIトークンの有効性を検証する接続テスト（GET /test/） |

すべて読み取り専用（GET）のツールのみを実装しています。ページネーションは全エンドポイント共通でページ番号方式（1ページ100件固定、レスポンスの `next` が `null` でなければ次ページあり）。

## 既知の制約

- **β版API**: 本コネクタが利用するのはジョブカン経費精算/ワークフローAPIの**β版**（https://ssl.wf.jobcan.jp/api_doc ）であり、仕様が予告なく変更される可能性がある。
- **承認・却下・差し戻し・申請作成の操作なし（書き込み系の見送り）**: ジョブカン経費精算/ワークフローAPIには申請の承認・却下・差し戻し、および申請書そのものを作成するエンドポイントが存在しない（承認・申請操作はWeb画面上でのみ可能）。本コネクタは申請の閲覧のみに対応する。
- **マスタの作成/更新/削除は未実装（書き込み系の見送り）**: API自体には各マスタに対する `POST` / `PUT` / `DELETE` エンドポイントが存在するが（例: `POST /v1/projects/` でプロジェクト作成、`PUT /v1/groups/{group_code}/` でグループ更新、`DELETE /v1/users/{user_code}/` でユーザー無効化、`POST/PUT/DELETE /v1/company/`・`/v1/positions/`・`/v1/generic_master/...` など）、本コネクタでは書き込みによる副作用（データの上書き・削除、べき等でない新規作成）のリスクを避けるため、一覧・詳細取得（GET）のみを実装している。マスタの編集が必要な場合はジョブカンのWeb管理画面から操作すること。
- **`get_request`（申請書詳細）の注意**: 本コネクタは `GET /v2/requests/{request_id}/` で申請書1件の詳細を取得するが、β版APIドキュメントには単体取得エンドポイントが明示されていない（明記されているのは一覧の `GET /v1/requests/`・`GET /v2/requests/`）。既存実装として維持しているが、β版のため将来利用できなくなる可能性がある。単体詳細が取得できない場合は `list_requests` を `id` 指定で呼び出して代替できる。
- **日付パラメータの形式**: `list_requests` の日付系パラメータ（`applied_after` / `applied_before` / `completed_after` / `completed_before`）は `yyyy/mm/dd` または `yyyy/mm/dd hh:mm:ss` 形式で指定する必要がある（ハイフン区切りの `YYYY-MM-DD` は不可）。
- **ページネーション**: 全GETエンドポイントで共通のページ番号方式。1ページ100件固定で、レスポンスに `count`/`next`/`previous`/`results` を含む。`next` が `null` でなければ `page` を1つ増やして次ページを取得する（`next` には次ページの完全なURLが入るが、本コネクタの各ツールは `page` 番号のみを受け付ける）。
- **絞り込みパラメータの非対称性**: `list_requests` と `list_forms` はAPI側で豊富な絞り込みパラメータに対応している（`list_requests`: `id` / `status` / `form_id` / `title` / `applicant_code` / `group_code` / `project_code` / 日付範囲 / `include_canceled` / `sort_by`。`list_forms`: `form_type` / `settlement_type` / `category_code` / `name` / `view_type` / `description`）。一方 `list_users` / `list_groups` / `list_positions` / `list_projects` / `list_companies` はAPIドキュメント上 `page` 以外の絞り込みパラメータが確認できない。
- **レート制限**: 1アクセストークンあたり1時間5,000リクエストが上限。超過分はエラー（HTTP 429 相当）になる。

### 2026-07-13 の深掘りで確認した内容

β版APIドキュメント（https://ssl.wf.jobcan.jp/api_doc ）を精読し、以下を反映・整理した。

**今回追加した読み取り系ツール**: `list_forms`（フォーム一覧）/ `get_user`（ユーザー詳細）/ `list_groups`（グループ一覧）/ `list_positions`（役職一覧）/ `get_company`（取引先詳細）/ `get_generic_master`（汎用マスタ）/ `validate_token`（トークン検証）。

**実在を確認したが見送ったエンドポイント**:

- **グループ・役職・プロジェクトの個別詳細取得（`GET /v1/groups/{group_code}/`・`GET /v1/positions/{position_code}/`・`GET /v1/projects/{project_code}/`）**: いずれも実在するが、レスポンス項目が対応する一覧APIと同一（例: プロジェクト詳細は `project_code`・`project_name` のみ）で追加情報がないため、一覧ツールで代替できると判断し見送った。詳細に固有の項目がある `users` と `company` については `get_user` / `get_company` として個別詳細を実装している。
- **全マスタの書き込み系（`POST` / `PUT` / `DELETE`）**: 上記のとおり副作用リスクを避けて一律見送り。特に `DELETE` はユーザー無効化・マスタ削除など復旧困難な操作、`POST` はべき等でない新規作成のため、誤操作の影響が大きいと判断した。
- **申請書の承認/却下/差し戻し/新規申請**: そもそもAPIエンドポイントが存在しないため実装不可（Web画面専用）。
- **汎用マスタのコード一覧取得**: 個別の `GET /v1/generic_master/{code}/` は実装したが、「どんな汎用マスタコードが存在するか」を列挙するエンドポイントはAPIに存在しない。コードはジョブカンの「汎用マスタ」画面で確認する必要がある。

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

```
経費精算で使えるフォーム（様式）の一覧を見せて
```

```
部署（グループ）の一覧を表示して
```

```
取引先コード ABC001 の振込先口座情報を教えて
```

```
APIトークンがちゃんと使えるか確認して
```
