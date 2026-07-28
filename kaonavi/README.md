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
| `list_member_layouts` | メンバー基本情報側のレイアウト定義（基本項目＋基本情報カスタム項目の型・選択肢）を取得 |
| `list_users` | カオナビのログインユーザー（アカウント）一覧を取得（紐づく社員コード・ロール・最終ログイン等） |
| `list_roles` | ロール（権限セット）一覧を取得（`list_users` の `role.id` を引くための参照マスタ） |
| `list_enum_options` | マスター情報（選択式カスタム項目の選択肢マスタ）を取得（`custom_field_id` 指定で1件も可） |
| `get_advanced_permissions` | 拡張アクセス設定を取得（`advanced_type` に `member` / `department` を指定） |

いずれのツールも読み取り専用（GET）で、書き込みは行わない。

## 既知の制約

- API ドキュメント: 管理者メニュー → 公開API v2情報 → APIドキュメント（`https://developer.kaonavi.jp/api/v2.0/index.html`、
  認証情報の Consumer Key / Consumer Secret から Basic 認証でアクセストークンを取得し、`Kaonavi-Token`
  ヘッダーで各APIを呼ぶ方式）。
- **操作対象の事前有効化が必要**: カオナビ公開API v2は既定では全操作が無効。管理者メニュー →
  公開API v2情報 → 操作対象管理 で、利用するリソース（メンバー・シート・ユーザー等）を有効化しておかないと、
  該当ツールが権限エラーになる。
- **ページネーションなし**: カオナビ公開API v2の読み取りAPI（`GET /members`・`GET /sheets/{sheet_id}`・
  `GET /users`・`GET /roles`・`GET /departments`・`GET /enum_options` など）にはページネーションが存在せず、
  1回の呼び出しで全件がまとめて返る。`GET /members` と `GET /sheets/{sheet_id}` のみ `updated_since`
  （YYYY-MM-DD形式、更新日以降のみ）で件数を絞れるが、それ以外は常に全件が返る（board コネクタのような
  `page`/`per_page` 方式のページングはカオナビ側に無いため、本コネクタでも提供していない）。
- **単体メンバー取得APIがない**: 社員コード指定で1名だけを取得するエンドポイントはカオナビ側に
  存在しないため、`get_member` は一括取得APIの結果をこちら側でフィルタして返している。
- **書き込み系APIは未実装（原則見送り）**: カオナビ公開API v2にはメンバー情報の登録・一括更新・部分更新・
  全入れ替え・削除（`POST/PUT/PATCH /members`, `PUT /members/overwrite`, `POST /members/delete`）、シート情報の
  一括更新・部分更新（`PUT/PATCH /sheets/{sheet_id}`）、所属ツリーの一括更新（`PUT /departments`、
  Request Bodyに含まれない所属は削除される全置換方式）、ユーザーの登録・更新・削除（`POST /users`,
  `PATCH/DELETE /users/{user_id}`）、選択肢マスタの全置換更新（`PUT /enum_options/{custom_field_id}`）、
  拡張アクセス設定の更新（`PUT /advanced_permissions/{advanced_type}`）などが存在する。しかしこれらは
  人事マスタ・権限設定への副作用が非常に大きく（全置換方式のものは Request Body に含めなかったデータが
  削除・無効化される）、誤操作時の影響が甚大なため、本コネクタは読み取り中心の設計方針に従い一律で
  見送っている。人事データの更新は管理画面またはCSVインポート、専用の連携基盤で行うこと。
- **タスク（実行結果）確認APIは見送り**: 書き込み系APIは非同期実行で `task_id` を返し、`GET /tasks/{task_id}` で
  実行状況を確認する設計だが、本コネクタは書き込みを行わず `task_id` を生成しないため `GET /tasks/{task_id}` は
  実装していない。
- **Webhook設定APIは見送り**: メンバー情報変更をトリガーに外部へ通知する Webhook 設定の取得・更新APIが
  存在するが、MCP（同期的な読み取り）の用途とは目的が異なるため対象外とした。
- **登用状況（enrollment_statuses）は未確認のため未実装**: 「登用状況」に相当する独立した読み取り
  エンドポイントは、確認できた公開情報（公式ドキュメント案内・CData / TROCCO / HULFT などの連携ツールが
  公開しているオブジェクト一覧）では実在を裏取りできなかったため、推測実装はしていない。実在が確認でき
  次第、読み取り系として追加を検討する。
- **並び順**: メンバー・シート・ユーザー・ロール等の並び順はAPI仕様上明記されていない。所属ツリーのみ
  同一階層内の表示順を示す `order` フィールドを持つ。
- **リクエスト制限**: 1社につき毎時3,000回（リクエストサイズ250MBまで）。書き込み系API（本コネクタでは
  未実装）はさらに毎分5回までの制限がある。アクセストークンの有効期限は1時間（本コネクタは自動再取得
  してキャッシュする）。

### 深掘りメモ（2026-07-13）

公式APIドキュメント（`https://developer.kaonavi.jp/api/v2.0/index.html`。JS描画のため直接パースは不可）に加え、
実運用でカオナビAPIを叩いている連携ツールの公開オブジェクト一覧（CData API Profile、TROCCO 転送元、HULFT Square）で
裏取りを行い、読み取り系として `list_member_layouts`（`GET /member_layouts`）・`list_users`（`GET /users`）・
`list_roles`（`GET /roles`）・`list_enum_options`（`GET /enum_options[/{custom_field_id}]`）・
`get_advanced_permissions`（`GET /advanced_permissions/{advanced_type}`）を追加した。これにより従来「未対応」だった
メンバー基本情報側のレイアウト定義（`GET /member_layouts`）にも対応済みとなった。裏取りできなかった
enrollment_statuses は上記のとおり未実装のまま残している。

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
