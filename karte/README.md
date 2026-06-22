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
| `track_event` | KARTE にイベントを送信してユーザー行動を記録する |
| `get_user_events` | 指定ユーザーのイベント履歴を取得する |
| `track_event_exec_action` | イベントを送信してサーバーサイドアクションを実行する |
| `get_campaign` | 接客サービス（キャンペーン）の詳細情報をIDで取得する |
| `get_campaign_stats` | 全接客サービスの設定と効果測定データを取得する |

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
