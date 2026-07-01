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

## API の制限・注意点

- ページネーションは `page`/`per_page` 方式（1始まり）。SmartHR API 側の既定値は `per_page=10`。1回のリクエストで取得できる最大件数は公式ドキュメントに明記されていません。
- `list_crews` の既定の並び順は公式ドキュメントに明記されていません。`sort` パラメータで指定できますが、指定可能な値の形式は非公開です。
- `update_crew` の部署異動は `department_ids`（配列）で指定します。単一の部署IDを渡す場合も配列にしてください。
- 従業員の削除（`DELETE /v1/crews/{id}`）や招待メール送信（`PUT /v1/crews/{id}/invite`）、部署・雇用形態の作成/更新/削除など、SmartHR API 自体にはより広範な書き込みAPIが存在しますが、誤操作時の影響が大きいため本コネクタでは未実装です。
- 社会保険・給与・カスタム項目など、従業員データには非常に多くの項目があります。必要な項目だけに絞りたい場合は `fields` パラメータ（カンマ区切り）を使ってください。

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
