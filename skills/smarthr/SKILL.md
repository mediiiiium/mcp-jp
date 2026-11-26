---
name: smarthr
description: SmartHR（人事・労務）の従業員・部署・雇用形態・役職などを、mcp-jp の smarthr MCP サーバーで調べる・更新する。「営業部の在籍者を一覧にして」「この人の雇用形態を確認して」「〇〇さんを開発部に異動させて」のように、SmartHR の従業員データを扱う依頼で使う。
---

# SmartHR（mcp-jp / smarthr）

SmartHR の従業員（crew）・部署・雇用形態・役職などのマスタを、MCP サーバー `smarthr-mcp` 経由で読み書きする。
書き込みは従業員情報の部分更新（`update_crew`）だけで、それ以外はすべて読み取り専用。

> 動作確認の状況: 公式ドキュメントに沿って実装し、構造とエラー処理のテストは CI で通しているが、実際の SmartHR アカウントではまだ動かしていない（README の「動作確認」列を参照）。

## 準備

1. SmartHR 管理画面 → アプリ連携 → アクセストークン で、アクセストークンを発行する
2. テナントID（`https://{テナントID}.smarthr.jp` の部分）を控える
3. インストールして登録する

```bash
pip install "git+https://github.com/mediiiiium/mcp-jp#subdirectory=smarthr"
claude mcp add smarthr -e SMARTHR_ACCESS_TOKEN=<トークン> -e SMARTHR_TENANT_ID=<テナントID> -- smarthr-mcp
```

Claude Desktop の場合は `claude_desktop_config.json` の `mcpServers` に `"command": "smarthr-mcp"` と同じ2つの環境変数を書く。

| 環境変数 | 内容 |
|---|---|
| `SMARTHR_ACCESS_TOKEN` | 管理画面で発行したアクセストークン |
| `SMARTHR_TENANT_ID` | テナントID |

## 進め方

- **人を探す**: まず `list_crews` で絞り込む。`emp_status`（employed / absent / retired）、`department_id`、`employment_type_id`、入社日・退職日の範囲、`q`（氏名・部署名のフリーワード）を組み合わせられる。
- **ID を先に引く**: 部署・雇用形態・役職で絞るときは、`list_departments` / `list_employment_types` / `list_job_titles` で ID を確かめてから `list_crews` に渡す。
- **1人の詳細**: `get_crew` に渡す `id` は社員番号ではなく SmartHR 内部の従業員ID。社員番号しか分からなければ `list_crews` の結果から ID を拾う。複数人ならまとめて `list_crews` の `id`（カンマ区切り）で取るほうが速い。
- **項目が多すぎるとき**: 従業員1人あたりの項目が非常に多い。必要な項目だけを `fields`（カンマ区切り）で指定すると、出力の切り詰めを避けやすい。
- **ページ送り**: `page` / `per_page` 方式（1始まり）。全件が要るときは空になるまで `page` を進める。
- **部署の階層**: `list_departments` はフラットなリストで返る。親子関係は各部署の parent / children から組み立てる。

## 更新するとき（update_crew）

- 部署異動・雇用形態の変更・氏名・メールアドレスの部分更新ができる。
- 部署は `department_ids`（配列）で渡す。1部署でも配列にする。
- **実データを書き換える操作なので、対象者・変更前・変更後を利用者に見せて確認を取ってから呼ぶ。** 対象者は `get_crew` で事前に確かめる。

## できないこと

従業員の削除・招待メール送信、給与明細・源泉徴収票・口座情報・産休育休情報、Webhook や SSO の設定は、影響の大きさや機微性から実装していない。必要なら SmartHR の管理画面で行うよう案内する。

## ツール

`list_crews` `get_crew` `update_crew` `list_departments` `list_employment_types` `list_job_titles` `list_grades` `list_job_categories` `list_recruitment_types` `list_dependents` `list_dependent_relations` `list_biz_establishments` `list_users` `list_companies` `list_payment_periods`

詳しい引数は [smarthr/README.md](https://github.com/mediiiiium/mcp-jp/blob/main/smarthr/README.md) を参照。
