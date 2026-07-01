# pipedrive-mcp

Pipedrive MCP サーバー。コンタクト・案件・アクティビティの管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `PIPEDRIVE_API_TOKEN` | ✅ | Pipedrive API トークン |

## API トークン取得方法

1. Pipedrive にログイン
2. 右上のアバター → **Personal preferences**
3. **API** タブを選択
4. **Your personal API token** をコピー

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_persons` | 人物（コンタクト）一覧を取得する（読み取り専用、start/limit ページネーション） |
| `search_persons` | 名前・メール・電話番号・メモ・カスタムフィールドで人物を検索する（exact_match / organization_id 対応） |
| `list_deals` | 案件（Deal）一覧を取得する（status 省略時は API 既定の all_not_deleted） |
| `create_deal` | 新しい案件を作成する（べき等性なし。重複作成に注意） |
| `list_activities` | アクティビティ（商談活動）一覧を取得する（done で完了状態を絞り込み可） |

各ツールの詳細な挙動（ページネーション方式・既定値・API側の制限）はツールの description を参照してください。

## 制限事項

- 読み取り専用ツールが中心で、更新・削除系のエンドポイント（案件・人物・アクティビティの update/delete、人物やアクティビティの create 等）は Pipedrive API 側には存在するが、本コネクタには未実装です。必要な場合は Pipedrive の管理画面から操作してください。
- `create_deal` は呼び出すたびに新規レコードを作成し、重複防止（べき等性）の仕組みはありません。誤って複数回呼び出すと同名の案件が重複作成されます。
- **v1 API の非推奨化について**: 本コネクタが使用する Pipedrive API v1 のエンドポイント（`GET /persons`, `GET /persons/search`, `GET /deals`, `POST /deals`, `GET /activities`）は、Pipedrive が2025-04-14に非推奨化を発表し、2025-12-31をもって動作保証を終了したものです。現時点でこれらの v1 エンドポイントがエラーを返す可能性があります。後継の API v2 はベース URL・認証方式（クエリパラメータ `api_token` ではなくヘッダ `x-api-token`）・ページネーション方式（`start`/`limit` ではなく `limit`/`cursor`）が異なるため、単純なパス置換では移行できず、本コネクタは未移行のままです。動作しない場合は v2 への移行（クライアント認証方式・ページネーション処理・レスポンス整形の見直しを含む）が必要です。

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
        "PIPEDRIVE_API_TOKEN": "your_pipedrive_api_token"
      }
    }
  }
}
```
