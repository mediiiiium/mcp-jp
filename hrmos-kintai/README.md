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
| `get_monthly_report` | 指定月の月次集計レポート（社員1人1行、総労働時間・残業時間・月締め状態などの集計値）を取得。`get_monthly_attendance` の1日1行明細とは別エンドポイント（`work_output_months`） |
| `list_paid_holidays` | 会社に設定されている休暇（有給休暇の種類）の一覧を取得。`get_paid_holiday_balance` に渡す休暇設定IDの取得に使う |
| `get_paid_holiday_balance` | 指定社員・年度・休暇設定について、付与・取得・残数の履歴を取得。現在の残日数は最新レコードを参照 |
| `get_user_stamps` | 指定社員の打刻履歴を新しい順に取得。`stamp_type` で出勤/退勤/休憩開始/休憩終了を絞り込み可能 |

すべて読み取り専用（GET）。ページネーションは `page`/`limit`（最大100件、既定50件）。各ツールの `from`/`to` は
勤怠日・打刻日そのものではなく「レコードの更新日時」による絞り込みである点に注意（HRMOS勤怠APIの仕様）。

## 既知の制約

- **総ページ数が確認できない**: HRMOS勤怠APIはレスポンスヘッダー（`X-Total-Count`/`X-Total-Page`）にページネーション情報を返すが、本コネクタはレスポンスボディ（JSON配列）のみをLLMに渡している。次ページの有無は、取得件数が0件になるまで `page` を増やして確認する必要がある。
- **打刻の修正・削除ができない**: HRMOS勤怠APIには打刻登録（`POST /stamp_logs`）はあるが更新・削除のAPIが存在しない。誤った打刻の修正は管理画面から行う必要がある。また、打刻登録APIは本コネクタでは未実装（読み取り専用）。書き込み系ツールは事故時に取り消せない操作（打刻の追加は取り消しAPIがない）ため、公式ドキュメント（`https://ieyasu.co/docs/openapi.json`）でリクエスト/レスポンス形は確認できたが、今回は見送った。
- **部署・社員のCRUDは読み取りのみ**: 部署（`/departments`）には作成・更新・削除APIがHRMOS勤怠側にも存在しない（GETのみ）。社員（`POST /users`、ユーザー登録・更新兼用）はHRMOS勤怠側に存在するが、既存社員データの上書き事故リスクが高く（更新か新規作成かがリクエスト内容で決まる仕様のため誤操作時の影響範囲が広い）、本コネクタでは未実装。
- **`get_daily_attendance` は社員IDで絞り込めない**: `get_monthly_attendance` にはある `user_id` フィルタが、日次エンドポイント（`/work_outputs/daily/{day}`）には提供されていない（API仕様上の非対称）。特定社員のみ必要な場合も全社員分を取得してからクライアント側で絞り込む必要がある。
- **勤怠データの更新系は見送り**: `PUT /work`（勤怠データの更新）、`POST /work/other_systems`（他勤怠データ登録・更新）はドキュメント上確認できるが、承認済み勤怠を書き換える操作であり事故時の影響が大きいため未実装。管理画面から行う運用を推奨。
- **月次集計の差分・オリジナル集計は見送り**: `work_output_diffs`（日次/月次の勤怠データ差分）、`work_output_original_aggregates`（オリジナル時間帯集計）は存在するが、`get_monthly_attendance`/`get_monthly_report` で通常の用途はカバーできるため、利用頻度が低いと判断し今回は見送り。需要があれば追加を検討。
- **取引先・契約・年末調整系は対象外**: `business_partners`（取引先）、`deal_contracts`（契約）、`nnc/reports`（年末調整の各種CSV出力）はHRMOS勤怠APIに存在するが、いずれも本コネクタが対象とする「勤怠管理」の範囲外（他モジュールの機能）と判断し見送り。
- **雇用形態・拠点・勤務区分のマスタ系は見送り**: `employments`（雇用形態一覧）、`lodgments`（拠点一覧）、`segments`（勤務区分一覧）、`prefecturals`（都道府県一覧）はいずれも読み取り専用でドキュメントも明確だが、単体では利用頻度が低い設定マスタのため今回は見送り。将来 `list_users`/`get_monthly_report` 等の関連IDを解釈する用途で需要が出れば追加を検討。

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
