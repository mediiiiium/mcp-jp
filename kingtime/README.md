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
| `get_daily_workings` | 指定期間の日別勤怠集計データ取得（所定/残業/深夜/遅刻/早退時間などの分単位の集計値。実際の打刻時刻そのものは含まない） |
| `get_monthly_workings` | 指定月の月別勤怠集計データ取得（総労働時間・残業時間・有休等） |
| `get_daily_schedules` | シフト・スケジュール取得（登録・更新・削除は未実装） |
| `record_time` | 打刻を1件登録（出勤・退勤・休憩開始/終了・外出・外出から戻り） |

## 既知の制約

KING OF TIME WebAPI の仕様上、本コネクタには以下の制約があります。

- **従業員単位の絞り込み不可**: `get_daily_workings` / `get_monthly_workings` / `get_daily_schedules` はAPI側に従業員コード等での絞り込みパラメータが存在しないため、`division`（所属コード）で絞り込んだ上でレスポンス内の `employeeKey` で判別する必要があります。
- **打刻時刻そのものは取得不可**: `get_daily_workings` が返すのは分単位の集計値（所定/残業/深夜/遅刻/早退時間など）であり、実際の出勤・退勤の打刻時刻一覧（KING OF TIME側の `daily-workings/timerecord` GET）は本コネクタには未実装です。
- **スケジュールの登録・更新・削除は未実装**: KING OF TIME側には `PUT /daily-schedules/{employeeKey}/{date}`（登録・更新）・`DELETE` 同エンドポイント（削除）のAPIが存在しますが、本コネクタでは取得のみ実装しています。シフトの変更は管理画面から行ってください。
- **従業員マスタの登録・更新・削除は未実装**: KING OF TIME側にはAPIが存在しますが、本コネクタには実装していません。
- **ページネーションなし**: いずれの一覧系ツールも `limit`/`offset` は提供されておらず、条件に合致する全件を1回のレスポンスで返します（`get_daily_workings`/`get_daily_schedules` の期間は最大62日という制約があります）。
- **利用禁止時間帯**: 毎日 8:30〜10:00 と 17:30〜18:30（JST）は、`record_time`（打刻登録）以外のほとんどのAPIが利用できません。
- **打刻はべき等ではない**: `record_time` は呼び出すたびに新しい打刻イベントが1件追加されます。同じ内容で複数回呼んでも1回にまとまらないため、二重打刻に注意してください。
- **`record_time` の `employee_key`**: 従業員コード（`code`）ではなく、`get_employees` のレスポンスに含まれる不変の識別子 `key`（従業員識別キー）を指定する必要があります。

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
