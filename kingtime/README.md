# kingtime-mcp

KING OF TIME 勤怠管理 の MCP サーバー。

## セットアップ

```bash
cd kingtime
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `KINGTIME_ACCESS_TOKEN` | KING OF TIME 管理画面で発行したアクセストークン |

アクセストークンは KING OF TIME 管理画面 → 設定 → API連携 から取得してください。

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "kingtime": {
      "command": "kingtime-mcp",
      "env": {
        "KINGTIME_ACCESS_TOKEN": "your_token_here"
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `get_employees` | 従業員マスタ一覧を取得（在籍状況の基準日・所属コードで絞込可、record_time 等で使う従業員識別キー `key` もここで確認） |
| `get_employee` | 従業員コード（`code`）を指定して従業員1名の情報を取得（`get_employees` の絞り込み版） |
| `get_divisions` | 所属（division）データ一覧を取得。`division` 絞り込みに使う有効な所属コードの確認用 |
| `get_working_types` | 雇用区分（正社員・契約社員等）のマスタデータ一覧を取得 |
| `get_employee_groups` | 従業員グループのマスタデータ一覧を取得（機能未利用の企業では空になりうる） |
| `get_daily_workings` | 指定期間の日別勤怠集計データ取得（所定/残業/深夜/遅刻/早退時間などの分単位の集計値。実際の打刻時刻そのものは含まない） |
| `get_timerecords` | 指定期間の実際の打刻イベント一覧を取得（出勤・退勤等の打刻時刻そのもの・打刻種別・位置情報） |
| `get_monthly_workings` | 指定月の月別勤怠集計データ取得（総労働時間・残業時間・有休等） |
| `get_daily_schedules` | シフト・スケジュール取得（登録・更新・削除は未実装） |
| `record_time` | 打刻を1件登録（出勤・退勤・休憩開始/終了・外出・外出から戻り） |

## 既知の制約

KING OF TIME WebAPI の仕様上、本コネクタには以下の制約があります。

- **従業員単位の絞り込み不可**: `get_daily_workings` / `get_monthly_workings` / `get_daily_schedules` / `get_timerecords` はAPI側に従業員コード等での絞り込みパラメータが存在しないため、`division`（所属コード）で絞り込んだ上でレスポンス内の `employeeKey` で判別する必要があります（`get_timerecords` のみ `employeeKeys` による絞り込みが可能ですが `division` とは同時指定できません）。有効な所属コードは `get_divisions` で確認できます。
- **打刻の一括登録は未実装**: KING OF TIME側には `POST /daily-workings/timerecord`（1リクエストで最大1,000件の打刻を一括登録するAPI）が存在しますが、実データの打刻を複数件まとめて書き換える操作でありリスクが高いため、本コネクタでは1件ずつ登録する `record_time`（`POST /daily-workings/timerecord/{employeeKey}`）のみ実装しています。
- **申請・承認ワークフローは未実装**: KING OF TIME側にはスケジュール申請・時間外勤務申請・打刻申請・残業上限申請の取得（`GET /schedule-requests/{date}` 等）および承認・棄却（`PUT /requests/{requestId}`）のAPIが存在することをドキュメントで確認していますが、承認・棄却が実データの勤怠を確定させる操作であり本コネクタの読み取り中心の方針に照らしリスクが高いため、申請取得も含め今回は見送りました。
- **費用（人件費）系データは未実装**: `GET /daily-workings/cost` / `GET /monthly-workings/cost/{date}` / `GET /daily-schedules/cost` 等、人件費に関わるデータ取得APIが存在することを確認していますが、給与・人件費という機微性の高い情報のため今回のスコープでは見送りました。
- **休暇残数・年間休暇データは未実装**: `GET /monthly-workings/holiday-remained/{typeCode}/{date}`（月別残休暇）・`GET /yearly-workings/holidays/{typeCode}/{year}`（年別休暇）・`GET /holiday-classifications`（休暇区分マスタ）が存在することを確認していますが、今回のスコープでは見送りました。
- **企業・管理者・トークン管理系は未実装**: `GET /company`（企業情報）・`GET /administrators`（管理者一覧）・トークンの再発行/失効/有効確認（`/tokens/{token}` 系）が存在することを確認していますが、勤怠管理という本コネクタの用途から外れる管理系機能のため見送りました。
- **スケジュールの登録・更新・削除は未実装**: KING OF TIME側には `PUT /daily-schedules/{employeeKey}/{date}`（登録・更新）・`DELETE` 同エンドポイント（削除）のAPIが存在しますが、本コネクタでは取得のみ実装しています。シフトの変更は管理画面から行ってください。
- **従業員マスタの登録・更新・削除は未実装**: KING OF TIME側には `POST /employees`（登録）・`PUT /employees/{employeeKey}`（更新）・`DELETE /employees/{employeeKey}`（削除）およびそれぞれの一括版APIが存在しますが、本コネクタには実装していません。
- **ページネーションなし**: いずれの一覧系ツールも `limit`/`offset` は提供されておらず、条件に合致する全件を1回のレスポンスで返します（`get_daily_workings`/`get_daily_schedules`/`get_timerecords` の期間は最大62日という制約があります）。
- **利用禁止時間帯**: 毎日 8:30〜10:00 と 17:30〜18:30（JST）は、`record_time`（打刻登録）以外のほとんどのAPIが利用できません。
- **打刻はべき等ではない**: `record_time` は呼び出すたびに新しい打刻イベントが1件追加されます。同じ内容で複数回呼んでも1回にまとまらないため、二重打刻に注意してください。
- **`record_time` の `employee_key`**: 従業員コード（`code`）ではなく、`get_employees` のレスポンスに含まれる不変の識別子 `key`（従業員識別キー）を指定する必要があります。`get_employee`（単体取得）は逆に `employee_code`（従業員コード）で指定する点に注意してください。
- **`get_employee_groups` は機能未利用企業では空になりうる**: 対象企業が従業員グループ機能を利用していない場合、データを取得できません（ドキュメント記載の仕様）。

## 使用例

```
今月の全従業員の残業時間を確認して、20時間を超えている人をリストアップして
```

```
山田太郎さんの今週の勤怠集計を教えて
```

```
来週月曜日のシフトを確認して
```
