---
name: kingtime
description: KING OF TIME（勤怠管理）の従業員・打刻・日別/月別の勤怠集計・シフトを、mcp-jp の kingtime MCP サーバーで調べる、打刻を1件登録する。「今月の残業が20時間を超えている人は」「山田さんの今週の勤怠は」「来週月曜のシフトを確認して」のように、KING OF TIME の勤怠データを扱う依頼で使う。
---

# KING OF TIME（mcp-jp / kingtime）

KING OF TIME WebAPI の勤怠データを、MCP サーバー `kingtime-mcp` 経由で読む。
書き込みは打刻1件の登録（`record_time`）だけで、それ以外はすべて読み取り。

> 動作確認の状況: 公式ドキュメントに沿って実装し、構造とエラー処理のテストは CI で通しているが、実際の KING OF TIME アカウントではまだ動かしていない（README の「動作確認」列を参照）。

## 準備

1. KING OF TIME 管理画面 → 設定 → API連携 で、アクセストークンを発行する
2. インストールして登録する

```bash
pip install "git+https://github.com/mediiiiium/mcp-jp#subdirectory=kingtime"
claude mcp add kingtime -e KINGTIME_ACCESS_TOKEN=<トークン> -- kingtime-mcp
```

Claude Desktop の場合は `claude_desktop_config.json` の `mcpServers` に `"command": "kingtime-mcp"` と環境変数を書く。

| 環境変数 | 内容 |
|---|---|
| `KINGTIME_ACCESS_TOKEN` | 管理画面で発行したアクセストークン |

## 進め方

- **使えない時間帯がある**: 毎日 8:30〜10:00 と 17:30〜18:30（JST）は、`record_time` 以外のほとんどの API が使えない。この時間帯にエラーが出たら、時間をおくよう伝える。
- **従業員の2種類のID**: `get_employee` は従業員コード（`code`）で引く。`record_time` や集計データの突き合わせには、`get_employees` の結果に含まれる従業員識別キー（`key`）を使う。最初に `get_employees` で両方を手に入れておく。
- **従業員単位では絞れない**: `get_daily_workings` / `get_monthly_workings` / `get_daily_schedules` / `get_timerecords` は従業員で絞り込めない。`get_divisions` で所属コードを確かめて `division` で絞り、結果の `employeeKey` で目的の人を拾う（`get_timerecords` だけは `employee_keys`（従業員識別キー）で絞れるが、`division` とは同時に使えない）。
- **集計と打刻の使い分け**: 残業・深夜・遅刻などの集計値は `get_daily_workings`（日別）か `get_monthly_workings`（月別）。実際に何時に打刻したかは `get_timerecords`。
- **期間の上限**: 日別・打刻・スケジュールの取得期間は最大62日。ページ送りはなく、条件に合う全件が1回で返る。

## 打刻するとき（record_time）

- **べき等ではない**。呼ぶたびに打刻が1件増える。同じ内容で呼び直すと二重打刻になる。
- 対象者（従業員識別キー `key`）・種別・時刻を利用者に見せて確認を取ってから1回だけ呼ぶ。
- 一括打刻、申請・承認、スケジュールや従業員マスタの登録・変更は実装していない。管理画面で行うよう案内する。

## できないこと

申請・承認ワークフロー、人件費データ、休暇残数、企業・管理者・トークン管理、スケジュールと従業員マスタの書き込み。

## ツール

`get_employees` `get_employee` `get_divisions` `get_working_types` `get_employee_groups` `get_timerecords` `get_daily_workings` `get_monthly_workings` `get_daily_schedules` `record_time`

詳しい引数は [kingtime/README.md](https://github.com/mediiiiium/mcp-jp/blob/main/kingtime/README.md) を参照。
