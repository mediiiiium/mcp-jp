# hrmos-kintai-mcp

HRMOS勤怠（旧IEYASU、日本SMB向けクラウド勤怠管理システム）の MCP サーバー。公式 MCP 未提供。

## セットアップ

```bash
cd hrmos-kintai
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `HRMOS_COMPANY_URL` | ログインURLに含まれる会社識別子（例: `mycompany` → `https://ieyasu.co/mycompany/` のとき） |
| `HRMOS_API_KEY` | 管理画面 → API設定 で発行したシークレットキー |  # pragma: allowlist secret

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "hrmos-kintai": {
      "command": "hrmos-kintai-mcp",
      "env": {
        "HRMOS_COMPANY_URL": "your_company_url",
        "HRMOS_API_KEY": "your_api_key_here"  # pragma: allowlist secret
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `get_monthly_attendance` | 指定月の日次勤怠明細（1日1行）を全社員分取得。`user_id` で社員を絞り込み可能。月合計の集計レポートではない |
| `get_daily_attendance` | 指定日の日次勤怠明細を全社員分取得。社員IDでの絞り込みには非対応（API側に該当パラメータがない） |
| `list_users` | 社員一覧を取得。他ツールに渡す `user_id` はここで返る `id`（社員番号 `number` ではない） |
| `list_departments` | 部署一覧を取得（ページネーション対応）。作成・更新・削除APIはHRMOS勤怠側に存在せず常に読み取り専用 |
| `get_user_stamps` | 指定社員の打刻履歴を新しい順に取得。`stamp_type` で出勤/退勤/休憩開始/休憩終了を絞り込み可能 |

すべて読み取り専用（GET）。ページネーションは `page`/`limit`（最大100件、既定50件）。各ツールの `from`/`to` は
勤怠日・打刻日そのものではなく「レコードの更新日時」による絞り込みである点に注意（HRMOS勤怠APIの仕様）。

## 既知の制約

- **総ページ数が確認できない**: HRMOS勤怠APIはレスポンスヘッダー（`X-Total-Count`/`X-Total-Page`）にページネーション情報を返すが、本コネクタはレスポンスボディ（JSON配列）のみをLLMに渡している。次ページの有無は、取得件数が0件になるまで `page` を増やして確認する必要がある。
- **打刻の修正・削除ができない**: HRMOS勤怠APIには打刻登録（`POST /stamp_logs`）はあるが更新・削除のAPIが存在しない。誤った打刻の修正は管理画面から行う必要がある。また、打刻登録APIは本コネクタでは未実装（読み取り専用）。
- **部署・社員のCRUDは読み取りのみ**: 部署（`/departments`）には作成・更新・削除APIがHRMOS勤怠側にも存在しない。社員（`/users`）には登録・更新用のPOST APIがHRMOS勤怠側に存在するが、本コネクタでは未実装。
- **`get_daily_attendance` は社員IDで絞り込めない**: `get_monthly_attendance` にはある `user_id` フィルタが、日次エンドポイント（`/work_outputs/daily/{day}`）には提供されていない（API仕様上の非対称）。特定社員のみ必要な場合も全社員分を取得してからクライアント側で絞り込む必要がある。
- **月次集計レポート（社員1人1行の合計値）は未実装**: HRMOS勤怠APIには `work_output_months`（月締め状態や合計労働時間などを社員ごとに集計したレポート）というエンドポイントが別途存在するが、本コネクタでは未実装。`get_monthly_attendance` が返すのはあくまで1日1行の明細データ。

## 使用例

```
今月（2026年6月）の勤怠データを見せて
```

```
社員一覧を表示して
```

```
田中さん（user_id: 123）の先月の打刻履歴を確認して
```
