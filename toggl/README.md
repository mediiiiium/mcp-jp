# toggl-mcp

Toggl Track MCP サーバー。時間計測・プロジェクト・工数管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `TOGGL_API_TOKEN` | ✅ | Toggl Track API トークン |

## API トークン取得方法

1. Toggl Track にログイン
2. 右上のアバター → **Profile Settings**
3. 下部の **API Token** セクションに表示される

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `get_profile` | 現在のユーザープロファイルを取得する（with_related_data で関連データも一括取得可） |
| `list_workspaces` | 所属ワークスペース一覧を取得する |
| `list_projects` | ワークスペース内のプロジェクト一覧を取得する（ページネーション・絞り込み対応） |
| `list_clients` | ワークスペース内のクライアント（請求先企業）一覧を取得する |
| `list_time_entries` | 自分の時間計測エントリー一覧を取得する |
| `create_time_entry` | 新しい時間計測エントリーを作成する（実行中タイマーとしても作成可） |
| `update_time_entry` | 既存の時間計測エントリーを更新する |
| `stop_time_entry` | 実行中の時間計測エントリーを停止する |
| `delete_time_entry` | 時間計測エントリーを削除する |

### 制限事項

- プロジェクト・クライアントの作成・更新・削除・アーカイブAPIはToggl Track側に存在するが、稼働中データや請求データへの誤操作を避けるため本コネクタでは参照のみ提供している。
- `list_time_entries` は専用のページ番号/カーソル方式のページネーションを持たない。`start_date`/`end_date`/`before` で範囲を絞るか、`since`（UNIXタイムスタンプ、削除済みも含む）で差分取得する。範囲を指定しない場合、直近日数分・上限件数までしか返らない場合がある（Toggl公式ドキュメントには明記されていないためサポート情報に基づく）。
- `update_time_entry` はPUT方式で更新するが、リクエストに含めなかった項目が更新後どう扱われるかはToggl公式ドキュメントに明記されていない。安全のため変更しない項目も含めて明示的に指定することを推奨する。

## インストール

```bash
cd toggl
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "toggl": {
      "command": "toggl-mcp",
      "env": {
        "TOGGL_API_TOKEN": "your_toggl_api_token"
      }
    }
  }
}
```
