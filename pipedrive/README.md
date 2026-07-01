# pipedrive-mcp

Pipedrive MCP サーバー。コンタクト・案件・アクティビティの管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `PIPEDRIVE_API_TOKEN` | ✅ | Pipedrive API トークン |
| `PIPEDRIVE_COMPANY_DOMAIN` | ✅ | 会社ドメイン（`https://your-company.pipedrive.com` の `your-company` 部分。API v2 はエンドポイントが会社ごとのサブドメインになる） |

## API トークン取得方法

1. Pipedrive にログイン
2. 右上のアバター → **Personal preferences**
3. **API** タブを選択
4. **Your personal API token** をコピー
5. ログイン中の URL（`https://your-company.pipedrive.com/...`）から会社ドメイン部分を控える

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_persons` | 人物（コンタクト）一覧を取得する（読み取り専用、cursor ページネーション） |
| `search_persons` | 名前・メール・電話番号・メモ・カスタムフィールドで人物を検索する（exact_match / organization_id 対応） |
| `list_deals` | 案件（Deal）一覧を取得する（status 省略時は API 既定で全ステータス） |
| `create_deal` | 新しい案件を作成する（べき等性なし。重複作成に注意） |
| `list_activities` | アクティビティ（商談活動）一覧を取得する（done で完了状態を絞り込み可） |

各ツールの詳細な挙動（ページネーション方式・既定値・API側の制限）はツールの description を参照してください。

## 制限事項

- 読み取り専用ツールが中心で、更新・削除系のエンドポイント（案件・人物・アクティビティの update/delete、人物やアクティビティの create 等）は Pipedrive API 側には存在するが、本コネクタには未実装です。必要な場合は Pipedrive の管理画面から操作してください。
- `create_deal` は呼び出すたびに新規レコードを作成し、重複防止（べき等性）の仕組みはありません。誤って複数回呼び出すと同名の案件が重複作成されます。
- **v1 → v2 移行済み（2026-07）**: Pipedrive は2025-04-14にv1エンドポイント（`GET /persons`, `GET /persons/search`, `GET /deals`, `POST /deals`, `GET /activities`）の非推奨化を発表し、2025-12-31をもって動作保証を終了しました。本コネクタは v2（`https://{company}.pipedrive.com/api/v2/...`、ヘッダ認証 `x-api-token`、cursor ページネーション）へ移行済みです。`list_deals` の `status` に v1 にあった `all_not_deleted` は v2 に存在しないため、削除済みを除く全件が必要な場合は `status=open,won,lost` を明示してください。

## インストール

```bash
cd pipedrive
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "pipedrive": {
      "command": "pipedrive-mcp",
      "env": {
        "PIPEDRIVE_API_TOKEN": "your_pipedrive_api_token",
        "PIPEDRIVE_COMPANY_DOMAIN": "your-company"
      }
    }
  }
}
```
