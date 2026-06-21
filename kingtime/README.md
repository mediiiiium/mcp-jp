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
| `get_employees` | 従業員一覧を取得 |
| `get_daily_workings` | 指定期間の日次勤怠データ取得（出退勤時刻・残業時間等） |
| `get_monthly_workings` | 指定月の月次集計データ取得（総労働時間・有休等） |
| `get_daily_schedules` | シフト・スケジュール取得 |
| `record_time` | 打刻記録（出勤・退勤・外出・戻り） |

## 使用例

```
今月の全従業員の残業時間を確認して、20時間を超えている人をリストアップして
```

```
山田太郎さんの今週の出退勤時刻を教えて
```

```
来週月曜日のシフトを確認して
```
