# smarthr-mcp

SmartHR 人事・労務管理の MCP サーバー。

## セットアップ

```bash
cd smarthr
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `SMARTHR_ACCESS_TOKEN` | SmartHR 管理画面で発行したアクセストークン |
| `SMARTHR_TENANT_ID` | SmartHR のテナントID（URLの `{tenant}.smarthr.jp` 部分） |

アクセストークンは SmartHR 管理画面 → アプリ連携 → アクセストークン から取得してください。

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "smarthr": {
      "command": "smarthr-mcp",
      "env": {
        "SMARTHR_ACCESS_TOKEN": "your_token_here",  # pragma: allowlist secret
        "SMARTHR_TENANT_ID": "your_tenant_id"
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_crews` | 従業員一覧を取得（在籍状況・部署・雇用形態・役職・入社日/退職日の範囲・フリーワード等で絞り込み可。読み取り専用） |
| `get_crew` | 特定の従業員の詳細情報を取得（id は社員番号ではなく SmartHR 内部の従業員ID。読み取り専用） |
| `list_departments` | 部署一覧を取得（フラットなリストで parent/children を辿って階層を組み立てる。読み取り専用） |
| `list_employment_types` | 雇用形態一覧を取得（正社員・パート等。絞り込みパラメータなし。読み取り専用） |
| `update_crew` | 従業員情報を部分更新（部署異動・雇用形態変更・氏名・メールアドレス） |
| `list_dependents` | 指定した従業員（crew_id）の家族情報（扶養家族等）一覧を取得（読み取り専用） |
| `list_job_titles` | 役職一覧を取得（id・name・rank・code等。読み取り専用） |
| `list_grades` | 等級一覧を取得（id・name・rank・code等。読み取り専用） |
| `list_job_categories` | 職種一覧を取得（読み取り専用） |
| `list_recruitment_types` | 採用区分一覧を取得（読み取り専用） |
| `list_dependent_relations` | 続柄（家族情報の続柄区分）一覧を取得（読み取り専用） |
| `list_biz_establishments` | 事業所一覧を取得（社会保険・労働保険の適用事業所単位の情報。読み取り専用） |
| `list_users` | SmartHRログインユーザー（管理者・利用者アカウント）一覧を取得（従業員ではなくログインアカウント。読み取り専用） |
| `list_companies` | 会社情報一覧を取得（通常はテナントに紐づく1社分。読み取り専用） |
| `list_payment_periods` | 給与支給形態（締め日・支払日等）一覧を取得（読み取り専用） |

## API の制限・注意点

- ページネーションは `page`/`per_page` 方式（1始まり）。SmartHR API 側の既定値は `per_page=10`。1回のリクエストで取得できる最大件数は公式ドキュメントに明記されていません。
- `list_crews` の既定の並び順は公式ドキュメントに明記されていません。`sort` パラメータで指定できますが、指定可能な値の形式は非公開です。
- `update_crew` の部署異動は `department_ids`（配列）で指定します。単一の部署IDを渡す場合も配列にしてください。
- 従業員の削除（`DELETE /v1/crews/{id}`）や招待メール送信（`PUT /v1/crews/{id}/invite`）、部署・雇用形態・役職・等級・職種・採用区分等の作成/更新/削除など、SmartHR API 自体にはより広範な書き込みAPIが存在しますが、誤操作時の影響が大きいため本コネクタでは未実装です。
- 社会保険・給与・カスタム項目など、従業員データには非常に多くの項目があります。必要な項目だけに絞りたい場合は `fields` パラメータ（カンマ区切り）を使ってください。
- `list_dependent_relations` の `filter` パラメータは、公式ドキュメント上で指定可能な値として `spouse` のみが確認できました。他の値が使えるかは未検証です。
- 以下は公式ドキュメント（`developer.smarthr.jp/api`）上でエンドポイントの実在は確認できたものの、今回のカバレッジ深掘りでは実装を見送りました。理由とあわせて記載します（実在確認済みなので、将来的に需要が明確になれば再検討の余地あり）。
  - **給与明細グループ / 給与明細**（`GET /v1/payrolls`、`GET /v1/payrolls/{id}/payslips` 等）・**源泉徴収票グループ / 源泉徴収票**（`GET /v1/tax_withholdings` 等）: 個人の給与・税務情報という機微性の高いデータであり、読み取り専用であっても本コネクタの対象外としました。
  - **口座情報**（`GET /v1/bank_account_settings`）: 会社の給与振込用口座情報という機密性の高いデータのため見送りました。
  - **産休育休情報**（`GET /v1/crews/{crew_id}/maternity_childcare_leaves`）: 機微な個人情報（医療・家族状況）であるため見送りました。
  - **Webhook**（`GET/POST/PUT/PATCH/DELETE /v1/webhooks`）: 業務データではなくアプリ連携の設定情報であり、誤って削除・変更すると外部連携が壊れるため、AIエージェント経由での操作に適さないと判断し見送りました。
  - **バックグラウンド処理 / 添付ファイル**（`GET /v1/batch_jobs` 等）: 非同期ジョブの管理APIで、対応する書き込みAPI（`crew_export`/`crew_import`/`dependent_import`の登録）とセットでないと実用性が低く、読み取り専用方針の本コネクタでは優先度が低いため見送りました。
  - **従業員情報収集フォーム**（`GET /v1/crew_input_forms`）・**メールフォーマット**（`GET /v1/mail_formats`）: 内部管理用の設定情報で、AIエージェントとの自然言語でのやり取りにおける優先度が低いため見送りました。
  - **カスタム従業員項目グループ / テンプレート**（`GET /v1/crew_custom_field_template_groups`、`GET /v1/crew_custom_field_templates`）・**カスタム家族項目テンプレート**（`GET /v1/dependent_custom_field_templates`）: これらはカスタム項目の「定義（スキーマ）」であり、項目の値そのものは `list_crews` / `get_crew` / `list_dependents` のレスポンスに含まれるため、業務利用上の優先度が低いと判断し見送りました。
  - **ユーザーのSAML SSOアカウント**（`GET/POST/PATCH/DELETE /v1/users/{id}/saml_user` 等）: SSO設定はセキュリティに直結する設定情報であり、AIエージェント経由での参照・操作に適さないと判断し見送りました。

## 使用例

```
営業部の従業員を全員リストアップして
```

```
田中さんを開発部に異動させて
```

```
現在の雇用形態の種類を教えて
```
