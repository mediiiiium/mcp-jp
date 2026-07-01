# harvest-mcp

Harvest MCP サーバー。プロジェクト・時間計測・クライアント・請求書の管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `HARVEST_ACCESS_TOKEN` | ✅ | Harvest Personal Access Token |
| `HARVEST_ACCOUNT_ID` | ✅ | Harvest Account ID |

## 認証情報取得方法

1. Harvest にログイン
2. 右上のアバター → **Developers**
3. **Create new personal access token** をクリック
4. Token name を入力して **Create personal access token** をクリック
5. 発行された Token と Account ID をコピー

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_projects` | プロジェクト一覧を取得する（is_active・client_id・updated_since で絞り込み、page/per_page でページネーション） |
| `list_time_entries` | 時間計測エントリー一覧を取得する（project_id・client_id・task_id・user_id・is_billed・is_running・approval_status・期間・updated_since で絞り込み） |
| `create_time_entry` | 新しい時間計測エントリーを作成する（duration方式のみ対応。呼ぶたびに新規作成されるため冪等ではない） |
| `update_time_entry` | 既存の時間計測エントリーを部分更新する（PATCH） |
| `delete_time_entry` | 時間計測エントリーを削除する（close済み・アーカイブ済みプロジェクトのエントリーは削除不可の場合あり） |
| `list_clients` | クライアント一覧を取得する（is_active・updated_since で絞り込み） |
| `list_invoices` | 請求書一覧を取得する（client_id・project_id・state・期間・updated_since で絞り込み） |

## 既知の制約

- **ページネーション**: Harvest API v2 はページ番号方式（`page` / `per_page`）。`per_page` は省略時・上限とも2000件。
- **時間計測エントリーの作成**: duration方式（`hours` を直接指定）のみ対応。開始/終了時刻を指定するタイムスタンプ方式はHarvest API側には存在するが本コネクタは未実装。
- **プロジェクト・クライアント・請求書の作成/更新/削除**: Harvest API側にはいずれもエンドポイントが存在する（例: プロジェクト削除は紐づく時間計測・経費も削除される、クライアント削除は紐づくプロジェクト・請求書・見積が0件の場合のみ可能）が、請求データや稼働実績に対する誤操作を避けるため、本コネクタでは参照（list）のみを提供している。作成・更新・削除が必要な場合はHarvestの管理画面を使うこと。
- **時間計測エントリーの削除**: `delete_time_entry` は close済み（請求確定済み等）や、関連プロジェクト/タスクがアーカイブ済みの場合は失敗することがある（Admin権限があればclose済みでも削除可能）。削除は取り消せず、同じIDに対する再削除はエラーになる（冪等ではない）。

## インストール

```bash
cd harvest
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "harvest": {
      "command": "harvest-mcp",
      "env": {
        "HARVEST_ACCESS_TOKEN": "your_harvest_access_token",
        "HARVEST_ACCOUNT_ID": "your_harvest_account_id"
      }
    }
  }
}
```
