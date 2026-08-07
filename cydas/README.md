# cydas-mcp

CYDAS（サイダス）タレントマネジメントシステムの MCP サーバー。CTM 2.0 API を使う。

**読み取り専用**です。CYDAS API には登録・更新系のエンドポイントもありますが、本コネクタは実装していません。

## セットアップ

```bash
cd cydas
pip install -e .
```

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|:---:|------|
| `CYDAS_ACCESS_TOKEN` | ○ | CTM 2.0 API のアクセストークン（Bearer 認証） |
| `CYDAS_BASE_URL` | | 接続先の上書き。既定は本番 `https://people-api.cydas.com`。ステージングを使う場合は `https://api-stg.cydas.com` |

トークンはテナントごとに発行されます。接続先が意図したテナントかどうかは `get_tenant_context` で確認できます。

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "cydas": {
      "command": "cydas-mcp",
      "env": {
        "CYDAS_ACCESS_TOKEN": "your_access_token"
      }
    }
  }
}
```

## 利用可能なツール

### 基本

| ツール名 | 説明 |
|---------|------|
| `get_tenant_context` | 接続先テナント情報を取得（疎通確認にも使える最も軽いツール） |
| `list_employees` | 社員情報リスト。`embed` で異動・兼務・住所・給与などを同時取得、`enrollmentStatus` で在籍区分を絞り込み |
| `get_employee` | 社員1名の情報（社員番号または内部ID指定） |
| `list_accounts` | ログインアカウント（IdP ユーザー）一覧。社員とは別概念 |
| `list_access_policies` | 権限設定一覧（`status` で有効/無効を絞り込み） |

### 組織

| ツール名 | 説明 |
|---------|------|
| `list_departments` | 部署情報（現在有効なもの、フラットなリスト） |
| `list_department_managers` | 所属長の一覧。部署コードで `list_departments` と結合して使う |
| `list_department_histories` | 部署履歴。`target_effective_date` で過去時点の組織を取得 |
| `list_reorganizations` | 組織改編の一覧（`current` で現在有効な1件のみ） |
| `get_reorganization_structures` | 指定した組織改編の構造情報 |
| `list_organization_master_data` | 部署まわりのマスタ（コード → 名称の対応表） |

### 人事異動・申請

| ツール名 | 説明 |
|---------|------|
| `list_personnel_changes` | 異動情報（発令）。v2 エンドポイントを使用。期間・社員番号で絞り込み |
| `list_personnel_change_master_data` | 人事異動まわりのマスタ |
| `list_personnel_applications` | 各種人事申請（`status`: inProgress / approved / remand） |

### 評価・育成

| ツール名 | 説明 |
|---------|------|
| `list_personal_profile_definitions` | パーソナルプロファイルの項目定義。`list_personal_profiles` の `category_id` はここで確認 |
| `list_personal_profiles` | パーソナルプロファイル（テナント独自定義の社員情報）。`category_id` 必須 |
| `list_personal_profile_master_data` | パーソナルプロファイルの選択肢マスタ |
| `list_skillcheck_sheets` | スキルチェックのシート一覧 |
| `get_skillcheck_answers` | 指定シートの回答結果（承認日で絞り込み可） |
| `list_career_plan_forms` | キャリアプランのフォーム一覧 |
| `list_career_plan_answers` | キャリアプランの回答内容。`form_id` 必須 |
| `list_job_descriptions` | ジョブディスクリプション一覧 |

### プロジェクト・勤怠

| ツール名 | 説明 |
|---------|------|
| `list_projects` | プロジェクト一覧 |
| `list_project_members` | 指定プロジェクトのアサイン状況 |
| `list_programs` | プログラム（複数プロジェクトを束ねる上位概念）一覧 |
| `list_monthly_attendance` | 月別勤怠情報 |
| `list_daily_attendance` | 日別勤怠情報（件数が増えやすいので期間は短く区切る） |

## 使う上での注意

- **ページネーション**: `page` / `pageSize`（既定100・上限100）。上限を超える `pageSize` は API が 400 を返すため、本コネクタ側で100に丸めています。
- **件数が多いと 504**: CYDAS API は 1 リクエストの対象が多すぎると `GatewayTimeout` を返します。API ドキュメントの目安は 1,200 件です。日別勤怠や全社員の取得では、期間・部署・在籍区分で分割してください。
- **機微情報**: `list_employees` の `embed` には給与（`salaries`）・自宅住所（`addresses`）・戸籍（`familyRegisters`）が含まれます。キャリアプランの回答も本人の異動希望などが入ります。必要なカテゴリだけを指定してください。

## 未実装のエンドポイント

CYDAS API の GET は 57 本あり、本コネクタはそのうち主要な 27 本を実装しています。以下は意図的に未実装です。

- 登録・更新・削除系すべて（本コネクタは読み取り専用）
- 一括登録のステータス確認（`.../batch-status/{operationId}`）— 書き込みとセットでしか使わないため
- スキルチェックのサマリー / レベルレンジ設定、キャリアプランのフォーム項目定義、申請フォームの一覧・詳細、プロジェクトのマネージャー / 評価者 / ステージ / 活動計画、ジョブファミリー・レベルのマスタ、社員のプロフィール画像
