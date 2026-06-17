# kintone MCP

kintone の MCP サーバー。

Claude 等のAIエージェントから kintone のアプリ・レコードを操作できます。

## 利用可能なツール

- `list_apps` — アプリ一覧取得
- `get_app` — アプリ詳細取得
- `list_fields` — フィールド一覧取得（レコード操作前の確認に）
- `get_record` — レコード1件取得
- `search_records` — レコード検索・一覧取得（クエリ指定可、最大500件）
- `create_record` — レコード作成
- `update_record` — レコード更新
- `delete_records` — レコード削除（複数件対応）

## セットアップ

```bash
cd kintone
pip install -e .
```

環境変数を設定：

```bash
export KINTONE_SUBDOMAIN=mycompany   # https://mycompany.cybozu.com の subdomain 部分
export KINTONE_API_TOKEN=your_api_token
```

APIトークンはアプリごとに発行します（kintone 管理画面 → アプリ設定 → APIトークン）。

複数アプリをまたぐ場合は、カンマ区切りで複数トークンを設定することも可能です。

## クエリ例（search_records の query パラメータ）

```
# 文字列一致
社名 = "株式会社〇〇"

# 日付範囲
作成日時 > "2026-01-01T00:00:00+0900"

# ソート付き
ステータス = "未対応" order by 作成日時 desc
```

## 前提

- kintone のアカウントと操作対象アプリへのアクセス権が必要
- APIトークンの権限（閲覧/追加/編集/削除）はアプリ設定で制御
- API ドキュメント: https://cybozu.dev/ja/kintone/docs/rest-api/

## Claude Desktop への登録例

```json
{
  "mcpServers": {
    "kintone": {
      "command": "kintone-mcp",
      "env": {
        "KINTONE_SUBDOMAIN": "mycompany",
        "KINTONE_API_TOKEN": "your_token"
      }
    }
  }
}
```
