# karte-mcp

KARTE（顧客データプラットフォーム・MA・パーソナライゼーション）の MCP サーバー。公式 MCP 未提供。

## セットアップ

```bash
cd karte
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `KARTE_API_KEY` | KARTE 管理画面でアプリを作成して発行した API v2 アクセストークン |  # pragma: allowlist secret

事前に KARTE 管理画面 > 設定 > アプリ管理でアプリを作成し、必要なスコープを付与してください。

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "karte": {
      "command": "karte-mcp",
      "env": {
        "KARTE_API_KEY": "your_api_key_here"  # pragma: allowlist secret
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `track_event` | KARTE にイベントを送信してユーザー行動を記録する（非同期・配信トリガーとしては使用不可） |
| `get_user_events` | 指定ユーザーのイベント履歴をイベント名ごとに取得する（時刻昇順、期間・件数の絞り込み可） |
| `track_event_exec_action` | イベントを送信し、設定済みのサーバーサイドアクションを実行する |
| `get_campaign` | 接客サービス（キャンペーン）の詳細情報をIDで取得する（読み取り専用） |
| `get_campaign_stats` | 全接客サービスの設定と効果測定データをCSV形式で取得する |

## 既知の制約

KARTE の Action API / Track API には以下のエンドポイントも存在するが、本コネクタでは読み取り中心の構成としており未実装。管理画面から操作するか、将来のバージョンでの追加を検討してください。

- 接客サービス（キャンペーン）の一覧取得・新規作成(create)・更新(update)・公開/非公開切替(toggleEnabled)
- 接客アクション（メッセージ）の作成(action/create)・更新(action/update)・単体取得(action/findById)
- アクションテーブルのレコード追加・変更(actionTable/records/upsert)・削除(actionTable/records/delete)
- ユーザー統計情報・セグメント所属状況の取得（POST /v2beta/track/user/get）
- refTable（参照テーブル）行の追加・削除（POST /v2beta/track/refTable/row/upsert・delete）

また `track_event` / `track_event_exec_action` の `event_name` には次の予約語が使用できない（API側の制約）：
`page`, `req`, `enter_group`, `leave_group`, `view`, `group`, `message_send`, `date`, `message_open`, `message_click`, `message_clicked`, `message_close`

## 使用例

```
ユーザー user_001 の購買イベントを記録して（商品ID: abc-123、金額: 5000円）
```

```
ユーザー user_001 の直近のページ閲覧・購買イベントを見せて
```

```
接客サービス cam_xxx の内容を教えて
```

```
直近30日間の全接客サービスの効果測定データを取得して
```
