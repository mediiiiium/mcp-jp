# kaonavi-mcp

カオナビ タレントマネジメントシステムの MCP サーバー。

## セットアップ

```bash
cd kaonavi
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `KAONAVI_CONSUMER_KEY` | カオナビ管理画面 → 公開API v2情報 → 認証情報 から取得 |
| `KAONAVI_CONSUMER_SECRET` | 同上 |

管理画面 → 設定 → 公開API v2情報 → 認証情報タブ でConsumer KeyとConsumer Secretを確認してください。

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "kaonavi": {
      "command": "kaonavi-mcp",
      "env": {
        "KAONAVI_CONSUMER_KEY": "your_consumer_key",
        "KAONAVI_CONSUMER_SECRET": "your_consumer_secret" 
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_members` | 全メンバー（従業員）の基本情報・所属・兼務情報を一括取得（`updated_since` で更新日絞り込み可） |
| `get_member` | 特定メンバーの詳細情報を取得（社員コード指定。内部的には一括取得APIをフィルタして実現） |
| `list_departments` | 所属ツリー（部署階層）をフラットなリストで取得 |
| `list_layouts` | シートレイアウト（カスタムシート項目定義）の一覧、または `sheet_id` 指定で1件を取得 |
| `get_sheet` | 特定シート（`sheet_id` 指定）の全メンバー分データを取得（`updated_since` で更新日絞り込み可） |

いずれのツールも読み取り専用（GET）で、書き込みは行わない。

## 既知の制約

- **ページネーションなし**: カオナビ公開API v2の `GET /members`・`GET /sheets/{sheet_id}` には
  ページネーションが存在せず、1回の呼び出しで全件がまとめて返る。件数を絞りたい場合は
  `updated_since`（YYYY-MM-DD形式、更新日以降のみ）で絞り込むしかない。
- **単体メンバー取得APIがない**: 社員コード指定で1名だけを取得するエンドポイントはカオナビ側に
  存在しないため、`get_member` は一括取得APIの結果をこちら側でフィルタして返している。
- **書き込み系APIは未実装**: カオナビ公開API v2にはメンバー情報の登録・一括更新・部分更新・全入れ替え・
  削除（`POST/PUT/PATCH /members`, `PUT /members/overwrite`, `POST /members/delete`）、シート情報の
  一括更新・部分更新（`PUT/PATCH /sheets/{sheet_id}`）、所属ツリーの一括更新（`PUT /departments`、
  Request Bodyに含まれない所属は削除される全置換方式）などが存在するが、本コネクタは読み取り専用の
  ため未実装。
- **メンバーレイアウト定義は未対応**: `GET /member_layouts`（氏名・入社日など基本情報側の項目定義）は
  `list_layouts` の対象外（`list_layouts` はシートレイアウト `GET /sheet_layouts` のみを扱う）。
- **並び順**: メンバー・シートデータの並び順はAPI仕様上明記されていない。所属ツリーのみ同一階層内の
  表示順を示す `order` フィールドを持つ。
- **リクエスト制限**: 1社につき毎時3,000回（リクエストサイズ250MBまで）。書き込み系API（本コネクタでは
  未実装）はさらに毎分5回までの制限がある。アクセストークンの有効期限は1時間（本コネクタは自動再取得
  してキャッシュする）。

## 使用例

```
全メンバーの一覧を見せて
```

```
営業部の部署IDを教えて
```

```
シートレイアウト一覧を確認して、スキルシートのデータを取得して
```
