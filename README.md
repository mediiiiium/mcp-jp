# mcp-jp — Japanese SMB SaaS connectors

[![Mentioned in Awesome MCP Servers](https://awesome.re/mentioned-badge.svg)](https://github.com/punkpeye/awesome-mcp-servers)

**日本の SMB 向け SaaS に対応した MCP サーバー集**

Claude などの AI エージェントから、日本のクラウドサービスを自然言語で操作できるようにします。
公式 MCP が存在しないサービスへのコネクタを独自実装しています。

> このリポジトリの狙いと収益化の考え方は [戦略メモ](./docs/strategy.md) を参照。
> その他の詳細ドキュメントは [docs/README.md](./docs/README.md) にまとめています。

## メンテナンス状況

**2026-10-27 から保守モードです。** 新しいコネクタの追加は止めていますが、リポジトリは公開したまま維持します。

- **CI（テスト）は動かし続けます。** 依存ライブラリの破壊的変更などで壊れたら直します。
- **各コネクタの実データでの動作確認は、時間のあるときに1本ずつ進めます。** 確認状況は下の一覧の「動作確認」列に書いています。
  「未確認」は、公式ドキュメントに沿って実装し、構造とエラー処理のテストは CI で通しているものの、実際のアカウントではまだ動かしていないという意味です。
  確認は [`tests/test_live_smoke.py`](./tests/test_live_smoke.py) の `LIVE_CASES` に1行足して、読み取り専用のツールで疎通を見る方法で行います。
- Issue・PR は歓迎します。返信はベストエフォートです。

---

## コネクタ一覧

### 日本SMB向け（独自実装）

| コネクタ | サービス | カテゴリ | 動作確認 |
|---------|---------|---------|---------|
| [`lstep/`](./lstep/) | [Lステップ](https://liff.line.me/) | LINE マーケティング | 未確認 |
| [`kingtime/`](./kingtime/) | [KING OF TIME](https://www.kingtime.jp/) | 勤怠管理 | 未確認 |
| [`smarthr/`](./smarthr/) | [SmartHR](https://smarthr.jp/) | 人事・労務 | 未確認 |
| [`kaonavi/`](./kaonavi/) | [カオナビ](https://kaonavi.jp/) | タレントマネジメント | 未確認 |
| [`cydas/`](./cydas/) | [CYDAS](https://www.cydas.com/) | タレントマネジメント | 未確認 |
| [`mazrica/`](./mazrica/) | [Mazrica Sales](https://mazrica.com/) | SFA | 未確認 |
| [`invox/`](./invox/) | [invox](https://invox.jp/) | 受取請求書 | 未確認 |
| [`smaregi/`](./smaregi/) | [スマレジ](https://smaregi.jp/) | POS・店舗管理 | 未確認 |
| [`jobcan-workflow/`](./jobcan-workflow/) | [ジョブカン経費精算/ワークフロー](https://workflow.jobcan.ne.jp/) | 経費・ワークフロー | 未確認 |
| [`base-ec/`](./base-ec/) | [BASE](https://thebase.com/) | EC | 未確認 |
| [`cloudsign/`](./cloudsign/) | [クラウドサイン](https://www.cloudsign.jp/) | 電子契約 | 未確認 |
| [`herp/`](./herp/) | [HERP Hire](https://herp.co/) | 採用管理 | 未確認 |
| [`talentio/`](./talentio/) | [Talentio](https://talentio.com/) | 採用管理 | 未確認 |
| [`lineworks/`](./lineworks/) | [LINE WORKS](https://line-works.com/) | ビジネスチャット | 未確認 |
| [`board/`](./board/) | [board](https://the-board.jp/) | 経営・請求書管理 | 実APIと仕様を突き合わせ済み（2026-08） |
| [`hrmos-kintai/`](./hrmos-kintai/) | [HRMOS勤怠](https://ieyasu.co/) | 勤怠管理 | 未確認 |
| [`misoca/`](./misoca/) | [Misoca](https://www.misoca.jp/) | 見積・請求書 | 未確認 |
| [`makeleaps/`](./makeleaps/) | [MakeLeaps](https://www.makeleaps.jp/) | 請求書・見積書 | 未確認 |
| [`notepm/`](./notepm/) | [NotePM](https://notepm.jp/) | 社内wiki | 未確認 |
| [`relation/`](./relation/) | [Re:lation](https://ingage.jp/relation/) | CS・メール共有 | 未確認 |
| [`karte/`](./karte/) | [KARTE](https://karte.io/) | MA・CDP | 未確認 |
| [`akashi/`](./akashi/) | [AKASHI / MFクラウド勤怠Plus](https://ak4.jp/) | 勤怠管理 | 未確認 |
| [`yappli-crm/`](./yappli-crm/) | [Yappli CRM](https://yapp.li/crm/) | モバイルCRM | 未確認 |
| [`payjp/`](./payjp/) | [PAY.JP](https://pay.jp/) | 決済 | 未確認 |

### グローバルSaaS（独自実装）

| コネクタ | サービス | カテゴリ | 動作確認 |
|---------|---------|---------|---------|
| [`pipedrive/`](./pipedrive/) | [Pipedrive](https://www.pipedrive.com/) | CRM | 未確認 |
| [`freshdesk/`](./freshdesk/) | [Freshdesk](https://freshdesk.com/) | カスタマーサポート | 未確認 |
| [`trello/`](./trello/) | [Trello](https://trello.com/) | プロジェクト管理 | 未確認 |
| [`toggl/`](./toggl/) | [Toggl Track](https://toggl.com/) | 時間計測 | 未確認 |
| [`harvest/`](./harvest/) | [Harvest](https://www.getharvest.com/) | 時間計測・請求書 | 未確認 |
| [`typeform/`](./typeform/) | [Typeform](https://www.typeform.com/) | フォーム作成 | 未確認 |
| [`sendgrid/`](./sendgrid/) | [SendGrid](https://sendgrid.com/) | メール配信 | 未確認 |

### 公式MCPが提供されているサービス

以下は公式 MCP サーバーが提供されているため、そちらを利用してください。

| サービス | 公式MCP |
|---------|---------|
| [freee会計](https://www.freee.co.jp/) | 2026年3月公開（270 API） |
| [マネーフォワードクラウド](https://biz.moneyforward.com/) | 2026年3月全プラン開放 |
| [kintone](https://kintone.cybozu.co.jp/) | 2026年5月公式QSG公開 |
| [Chatwork](https://go.chatwork.com/ja/) | chatwork/chatwork-mcp-server |
| [Backlog](https://backlog.com/ja/) | nulab/backlog-mcp-server |
| [Sansan](https://jp.sansan.com/) | 2025年11月提供開始 |
| [Salesforce](https://www.salesforce.com/jp/) | Salesforce Hosted MCP Server（2026年4月 GA） |
| [MiiTel](https://miitel.com/jp/) | RevComm（2025年12月 Beta） |
| [SALES GO / GoCoo!](https://salesgo.co.jp/) | 日本初MCPサーバー対応SFA（2025年10月 GA） |
| [カラーミーショップ](https://shop-pro.jp/) | リモートMCPサーバー（2026年3月 GA） |
| [zaico](https://www.zaico.co.jp/) | zaico MCP（2026年6月 GA） |
| [Mackerel](https://mackerel.io/) | mackerelio-labs/mcp-server |
| [電子印鑑GMOサイン](https://www.gmosign.com/) | GMO AI Connect（2026年秋 GA予定） |
| [SalesNow](https://salesnow.jp/) | api-data.api.salesnow.jp/v1/mcp |
| [Zendesk](https://www.zendesk.co.jp/) | 2026年夏 GA予定 |
| [HubSpot](https://www.hubspot.jp/) | mcp.hubspot.com（2026年4月 GA） |
| [Notion](https://www.notion.com/) | mcp.notion.com |
| [Stripe](https://stripe.com/jp) | mcp.stripe.com |
| [Twilio](https://www.twilio.com/) | Twilio Alpha MCP（Public Beta） |
| [Airtable](https://www.airtable.com/) | 2026年2月 GA |
| [GitLab](https://about.gitlab.com/) | GitLab Duo MCP（Beta） |
| [Asana](https://asana.com/ja) | mcp.asana.com V2（2026年2月） |
| [Jira](https://www.atlassian.com/ja/software/jira) | Atlassian MCP（2026年2月 GA） |
| [Shopify](https://www.shopify.com/jp) | Storefront/Dev MCP（2026年1月〜） |
| [Mailchimp](https://mailchimp.com/) | Intuit/Anthropic連携（2026年春） |
| [Confluence](https://www.atlassian.com/ja/software/confluence) | Atlassian MCP（2026年2月 GA） |
| [Square](https://squareup.com/jp/ja) | mcp.squareup.com（Beta） |
| [Box](https://www.box.com/ja-jp/home) | mcp.box.com（2025年8月 GA） |
| [Zoom](https://zoom.us/) | Zoom MCP（2026年4月〜） |
| [Dropbox](https://www.dropbox.com/ja/) | mcp.dropbox.com（2026年3月 GA） |
| [PagerDuty](https://www.pagerduty.com/) | PagerDuty/pagerduty-mcp-server |
| [Datadog](https://www.datadoghq.com/) | datadog-labs/mcp-server（2026年3月 GA） |
| [ClickUp](https://clickup.com/) | mcp.clickup.com（Public Beta） |
| [Calendly](https://calendly.com/) | mcp.calendly.com |
| [Brevo](https://www.brevo.com/ja/) | mcp.brevo.com |
| [ActiveCampaign](https://www.activecampaign.com/) | mcp.activecampaign.com |
| [Sentry](https://sentry.io/) | getsentry/sentry-mcp |
| [Heroku](https://www.heroku.com/) | heroku/heroku-mcp-server |
| [Cloudflare](https://www.cloudflare.com/ja-jp/) | cloudflare/mcp-server-cloudflare |
| [Vercel](https://vercel.com/) | mcp.vercel.com（2025年8月〜） |
| [CircleCI](https://circleci.com/ja/) | CircleCI-Public/mcp-server-circleci |
| [Garoon](https://garoon.cybozu.co.jp/) | garoon/garoon-mcp-server（**公式**・2026-08-13 確認） |
| [esa](https://esa.io/) | esaio/esa-mcp-server（**公式**・2026-08-13 確認） |
| [Jooto](https://www.jooto.com/) | PRTIMES/jooto-mcp（提供元 PR TIMES・2026-08-13 確認） |
| [Intercom](https://www.intercom.com/) | intercom/intercom-mcp-server（**公式**・2026-08-13 確認） |

> これらのサービスについては、過去に独自実装したコネクタを [`archive/`](./archive/) に移動し、メンテナンス対象外としています。新規利用では公式 MCP を使ってください。

---

<!-- tools:start -->
## Tools

31 コネクタ・298 ツール。各コネクタのコード（`list_tools()`）から [`scripts/build_index.py`](./scripts/build_index.py) で生成しています（手で編集しないでください）。
同じ内容を機械可読の [`connectors.json`](./connectors.json) と [`llms.txt`](./llms.txt) にも出しています。

### akashi — AKASHI / MFクラウド勤怠Plus（勤怠管理）

- `get_stamps` — 自身、または管理下の従業員1名の指定期間の打刻記録（出勤・退勤・休憩などのイベント履歴）を取得する
- `post_stamp` — トークンに紐づく従業員の打刻を1件記録する（出勤・退勤・直行・直帰・休憩入・休憩戻）
- `list_staffs` — トークンに紐づく従業員本人、および管理下にある従業員の一覧を取得する
- `get_staff` — 従業員ID（従業員番号ではなく Akashi 内部の staff_id）を指定して、その1名の詳細情報（氏名・所属組織・雇用区分・権限グループ・管理対象組織など）を取得する
- `get_alerts` — トークンに紐づく従業員本人の勤怠アラート一覧を取得する
- `get_working_records` — 管理下の複数従業員（最大50名）について、指定期間の勤務実績（実績の出退勤時刻・丸め後時刻・実働時間・休憩実績など）を取得する
- `search_working_statuses` — 指定した従業員ID・日付の組み合わせ（最大1000件）について、その日に設定されている勤務処理ラベル（例: 欠勤・出張・テレワークなど、企業ごとにカスタム設定された文字列）を一括…

### base-ec — BASE（EC）

- `get_shop` — 接続中のBASEショップの基本情報（ショップ名、URL、紹介文、ロゴ画像URL、Twitter/Facebook/Instagram/YouTube/TikTokの各アカウントI…
- `list_items` — BASEショップに登録されている商品の一覧を、価格・在庫数・画像URL・バリエーション（サイズ/色等）まで含めて取得する
- `get_item` — 1件の商品の詳細情報を取得する
- `search_items` — ショップ内の商品をキーワードで検索する
- `list_categories` — BASEショップに登録されているカテゴリの一覧を、階層構造（parent_number による親子関係、最大3階層のcode）を含めて取得する
- `get_item_categories` — 1件の商品に紐づいているカテゴリの一覧（item_category_id, item_id, category_id）を取得する
- `list_savings` — BASEショップの振込申請情報の一覧を、申請額（drawings）・各種手数料（事務手数料/振込手数料/お急ぎ振込手数料）・状態（requested: 申請中 / process…
- `list_delivery_companies` — BASEが対応している配送業者の一覧（delivery_company_id, name）を取得する
- `list_orders` — BASEショップの注文一覧を、注文日・合計金額・発送状況（dispatch_status）等のサマリ情報で取得する
- `get_order` — 1件の注文の詳細情報を、購入者情報・配送先・決済方法・購入商品明細（order_items、各商品行のorder_item_id と個別ステータスを含む）まで展開して取得する
- `update_order_status` — 注文内の商品行（order_item_id で指定する個別の購入明細。注文全体を指す unique_key ではない）のステータスを更新する

### board — board（経営・請求書管理）

- `list_clients` — 顧客（取引先）の一覧を取得する
- `list_projects` — プロジェクト（案件）の一覧を取得する
- `get_project` — 指定した1件のプロジェクト（案件）の詳細情報を取得する
- `list_invoices` — 請求データの一覧を取得する
- `create_project` — 新しいプロジェクト（案件）を1件作成する
- `get_client` — 指定した1件の顧客（取引先）の詳細情報を取得する
- `list_client_branches` — 顧客（取引先）の支社・支店の一覧を取得する
- `list_contacts` — 顧客（取引先）の担当者一覧を取得する
- `list_project_costs` — 案件原価データの一覧を取得する
- `list_users` — board 利用ユーザー（社内アカウント）の一覧を取得する
- `list_analyses` — 計上データ（経営分析用の集計データ）の一覧を取得する

### cloudsign — クラウドサイン（電子契約）

- `list_documents` — 書類（契約書）の一覧を取得する
- `get_document` — 書類1件の詳細情報（タイトル・ステータス・参加者・送信/最終処理日時など）を取得する
- `create_document` — 新しい書類（契約書）を下書き状態で作成する
- `set_participants` — 下書き状態の書類に署名者（宛先）を追加する
- `send_document` — 下書き状態の書類を署名依頼として送信する（ステータスを「先方確認中」に変更する不可逆な操作）
- `get_document_alert` — 書類のアラート情報（契約更新・満了確認などのためにユーザーが設定したリマインド日と有効/無効フラグ、メモ）を取得する
- `get_document_attribute` — 書類の管理用属性情報（契約相手の名称、契約締結日・契約開始日・契約終了日・解約通知期限、自動更新の有無、取引金額、管理番号、ユーザー定義項目など）を取得する
- `get_me` — Web API を実行しているユーザー自身の情報（ID・メールアドレス・氏名・所属組織・所属チーム・保持している権限）を取得する
- `list_team_documents` — チーム内のメンバー全員がやり取りした書類の一覧を取得する
- `list_cabinets` — キャビネット（書類を整理するフォルダ）の一覧を取得する
- `list_cabinet_documents` — 指定したキャビネットに格納されている書類の一覧を取得する

### cydas — CYDAS（タレントマネジメント）

- `get_tenant_context` — 接続先テナントの情報を取得する (GET /people/v1/tenant/context)
- `list_employees` — 社員情報をリストで取得する (GET /people/v1/individual/employees)
- `get_employee` — 社員1名の情報を取得する (GET /people/v1/individual/employees/{id})
- `list_departments` — 部署情報をリストで取得する (GET /people/v1/organization/departments)
- `list_department_managers` — 所属長（部署の責任者）をリストで取得する (GET /people/v1/organization/managers)
- `list_department_histories` — 部署履歴をリストで取得する (GET /people/v1/organization/department-histories)
- `list_reorganizations` — 組織改編をリストで取得する (GET /people/v1/organization/reorganizations)
- `get_reorganization_structures` — 指定した組織改編の構造情報を取得する (GET /people/v1/organization/reorganizations/{id}/structures)
- `list_organization_master_data` — 部署まわりのマスタデータをリストで取得する (GET /people/v1/organization/master-data)
- `list_personnel_changes` — 異動情報（発令）をリストで取得する (GET /people/v2/personnel-change/announcements)
- `list_personnel_change_master_data` — 人事異動まわりのマスタデータをリストで取得する (GET /people/v1/personnel-change/master-data)
- `list_personal_profile_definitions` — パーソナルプロファイルの項目定義を取得する (GET /people/v1/personal-profile/definitions)
- `list_personal_profiles` — パーソナルプロファイル（テナント独自に定義された社員情報）をリストで取得する (GET /people/v1/personal-profile/profiles)
- `list_personal_profile_master_data` — パーソナルプロファイルのマスタデータをリストで取得する (GET /people/v1/personal-profile/master-data)
- `list_projects` — プロジェクト情報をリストで取得する (GET /people/v1/project/projects)
- `list_project_members` — 指定プロジェクトのアサイン状況を取得する (GET /people/v1/project/projects/{projectCode}/employees)
- `list_programs` — プログラム情報をリストで取得する (GET /people/v1/project/programs)
- `list_skillcheck_sheets` — スキルチェックのシート情報をリストで取得する (GET /people/v1/skillcheck/sheets)
- `get_skillcheck_answers` — 指定シートのスキルチェック回答結果を取得する (GET /people/v1/skillcheck/sheets/{id}/answers)
- `list_career_plan_forms` — キャリアプランのフォームをリストで取得する (GET /people/v1/career-plan/forms)
- `list_career_plan_answers` — キャリアプランの回答内容をリストで取得する (GET /people/v1/career-plan/answers)
- `list_job_descriptions` — ジョブディスクリプションを一覧で取得する (GET /people/v1/job/job-descriptions)
- `list_personnel_applications` — 各種人事申請をリストで取得する (GET /people/v1/personnel-application/requests)
- `list_monthly_attendance` — 月別勤怠情報をリストで取得する (GET /people/v1/attendance/monthly-workings)
- `list_daily_attendance` — 日別勤怠情報をリストで取得する (GET /people/v1/attendance/daily-workings)
- `list_accounts` — アカウント情報をリストで取得する (GET /people/v1/user/idp-users)
- `list_access_policies` — 権限設定をリストで取得する (GET /people/v1/access-control/policies)

### freshdesk — Freshdesk（カスタマーサポート）

- `list_tickets` — チケット一覧をページ単位で取得する
- `get_ticket` — チケットIDを指定して1件の詳細を取得する
- `create_ticket` — 新しいチケットを1件作成する（POST）
- `delete_ticket` — チケットを1件削除する（ソフトデリート）
- `list_contacts` — コンタクト（問い合わせ者・顧客）の一覧をページ単位で取得する
- `get_contact` — コンタクトIDを指定して1件の詳細を取得する
- `delete_contact` — コンタクトを1件削除する（ソフトデリート）

### harvest — Harvest（時間計測・請求書）

- `list_projects` — プロジェクト一覧を取得する
- `list_time_entries` — 時間計測エントリー一覧を取得する
- `create_time_entry` — 新しい時間計測エントリーを1件作成する（duration方式：作業時間を hours で直接指定する方法のみ対応。開始/終了時刻を指定するタイムスタンプ方式はHarvest AP…
- `update_time_entry` — 既存の時間計測エントリー1件を部分更新する（PATCH）
- `delete_time_entry` — 時間計測エントリー1件を削除する
- `list_clients` — クライアント（請求先企業）一覧を取得する
- `list_invoices` — 請求書一覧を取得する

### herp — HERP Hire（採用管理）

- `list_candidacies` — 応募者（選考＝candidacy）の一覧を取得する
- `get_candidacy` — 応募者（選考）1件の詳細情報を取得する
- `list_requisitions` — 求人（ポジション＝requisition）の一覧を取得する
- `list_contacts` — 応募者1名分のコンタクト（面談・カジュアル面談・面接などの選考記録）を一覧取得する
- `list_candidacy_files` — 応募者1名に添付されたファイル（履歴書・職務経歴書・その他添付）のメタ情報一覧を取得する
- `list_assignments` — 応募者1名にアサインされている担当者（selecterや面接官などの社内メンバー）の一覧を取得する
- `get_evaluation` — 評価依頼1件（evaluation）の詳細を取得する
- `list_requisition_groups` — 求人グループ（複数の求人＝requisition をまとめる区分）の一覧を取得する
- `get_requisition_group` — 求人グループ1件の詳細情報を取得する
- `list_users` — HERP Hire のユーザー（社内メンバーアカウント）の一覧を取得する
- `list_timeline_comments` — 応募者1名分のタイムラインコメント（選考担当者間のやり取り・メモ）を一覧取得する
- `add_timeline_comment` — 応募者1名のタイムラインにコメントを新規追加する（書き込み系操作。呼び出すたびに新しいコメントが作成され、べき等ではない＝同じ内容で2回呼ぶとコメントが2件になる）

### hrmos-kintai — HRMOS勤怠（勤怠管理）

- `get_monthly_attendance` — 指定月の日次勤怠データ（1日ごとの出退勤・休憩時刻や実働時間などの明細行）を全社員分、1日1行の形式で取得する
- `get_daily_attendance` — 指定日の日次勤怠データ（出退勤・休憩時刻や実働時間などの明細行）を全社員分1行ずつ取得する
- `list_users` — 会社に登録されているユーザー（社員）の一覧を取得する
- `list_departments` — 部署一覧を取得する
- `get_monthly_report` — 指定月の月次集計レポート（社員1人1行、総労働時間・残業時間・遅刻日数・有給残日数などを集計した値）を取得する
- `list_paid_holidays` — 会社に設定されている休暇（有給休暇の種類。例: 一般社員向け年次有給休暇など）の一覧を取得する
- `get_paid_holiday_balance` — 指定した社員・年度・休暇設定について、休暇の付与・取得・残数の履歴（1レコード=1時点のスナップショット。残日数 remaining_days/remaining_hours、付…
- `get_user_stamps` — 指定ユーザー1人分の打刻履歴（出勤・退勤・休憩開始・休憩終了の各イベント）を、最新のものから順に取得する（並び順の変更はできない）

### invox — invox（受取請求書）

- `list_received_invoices` — 受取請求書の一覧を、請求日・計上日・部門・確定状態などの条件で絞り込んで取得する
- `get_received_invoice` — 受取請求書1件の詳細情報（仕入先・金額内訳・支払期日・添付ファイルURL・ワークフローのメッセージ履歴など）を取得する
- `approve_received_invoice` — ワークフロー申請済みの受取請求書を1件承認する（invox 側でワークフロー機能が有効になっており、対象の請求書が既に申請済み＝承認待ち状態である必要がある）
- `list_suppliers` — 仕入先（取引先）マスタの一覧を、コード・名称・登録番号・登録日で絞り込んで取得する
- `get_supplier` — 仕入先コードを指定して仕入先1件の詳細情報（源泉徴収の要否、課税/免税区分、インボイス登録番号、支払方法のリスト、請求処理時の指示、拡張項目など）を取得する
- `list_supplier_trade_conditions` — 指定した仕入先コードに紐づく取引設定（部門・プロジェクトの組み合わせごとの支払方法設定）の一覧を取得する
- `list_upload_settings` — invox 管理画面で設定されているアップロード設定（部門・プロジェクトの選択方法、データ化方法、請求書の区切り方、アップロード用メールアドレス・ページURLなど）の一覧を取得する
- `get_invoice_download_url` — 指定した請求書1件の画像・PDFファイルをダウンロードするための一時URLを取得する（発行されたURLは1分間のみ有効）
- `get_invoices_zip_download_url` — 複数の請求書IDを指定し、それらの請求書ファイルをまとめた zip ファイルをダウンロードするためのURLを取得する（最大100件まで指定可能）
- `confirm_invoice_message` — 受取請求書のワークフローメッセージ（get_received_invoice のレスポンスに含まれる messages[].message_id、confirmed=false …
- `export_journal` — invox 管理画面側の出力設定（会計ソフト向けの出力形式）に従って、費用計上仕訳（journal_type=expense）または支払計上仕訳（journal_type=pay…

### jobcan-workflow — ジョブカン経費精算/ワークフロー（経費・ワークフロー）

- `list_requests` — ジョブカン経費精算/ワークフローの申請書一覧を、ステータス・申請者・グループ・プロジェクト・日付範囲などで絞り込んで取得する（GET /v2/requests/）
- `get_request` — 申請書1件の詳細情報を取得する（GET /v2/requests/{request_id}/）
- `list_users` — ジョブカンに登録されているユーザーの一覧を取得する（GET /v3/users/）
- `list_projects` — ジョブカンに登録されているプロジェクト一覧を取得する（GET /v1/projects/）
- `list_companies` — ジョブカンに登録されている取引先（会社）一覧を取得する（GET /v1/company/）
- `list_forms` — ジョブカンに登録されている申請フォーム（申請書の様式）の一覧を取得する（GET /v1/forms/）
- `list_groups` — ジョブカンに登録されているグループ（部署）の一覧を取得する（GET /v1/groups/）
- `list_positions` — ジョブカンに登録されている役職の一覧を取得する（GET /v1/positions/）
- `get_user` — 指定した1人のユーザーの詳細情報を取得する（GET /v1/users/{user_code}/）
- `get_company` — 指定した1件の取引先（会社）の詳細情報を取得する（GET /v1/company/{company_code}/）
- `get_generic_master` — 汎用マスタ（ユーザーが「汎用マスタ」画面で自由に定義したマスタデータ）の1つを、その登録レコード一覧とともに取得する（GET /v1/generic_master/{generi…
- `validate_token` — APIトークンが有効かどうかを検証する（GET /test/）

### kaonavi — カオナビ（タレントマネジメント）

- `list_members` — 全メンバー（従業員）の基本情報・所属（主務）・兼務情報を取得する
- `get_member` — 社員コードを指定して特定1名のメンバー詳細（基本情報・所属・兼務・カスタム項目）を取得する
- `list_departments` — 所属ツリー（部署階層）の全件を取得する
- `list_layouts` — シートレイアウト（カスタムシートの項目定義。get_sheet で取得するシートの構造）の一覧を取得する
- `get_sheet` — 特定シート（カスタムシート、list_layoutsのidで指定）の全メンバー分のデータを取得する
- `list_member_layouts` — メンバー基本情報側のレイアウト定義（社員コード・氏名・入社日などの基本項目、および基本情報に紐づくカスタム項目の定義）を取得する (GET /member_layouts)
- `list_users` — カオナビのログインユーザー（アカウント）一覧を取得する (GET /users)
- `list_roles` — カオナビのロール（権限セット）一覧を取得する (GET /roles)
- `list_enum_options` — マスター情報（プルダウン・ラジオボタン・チェックボックスなど選択式カスタム項目の選択肢マスタ）を取得する
- `get_advanced_permissions` — 拡張アクセス設定（特定ユーザーに、通常の所属範囲を超えて追加で閲覧・操作を許可する所属コードなどのアクセス制御設定）を取得する (GET /advanced_permission…

### karte — KARTE（MA・CDP）

- `track_event` — KARTE にユーザー行動イベントを送信し、解析対象として記録する（POST /v2/track/event/write）
- `get_user_events` — 指定ユーザー（user_id または visitor_id）のイベント履歴を、イベント名ごとにまとめて取得する（POST /v2beta/track/event/get）
- `track_event_exec_action` — KARTE にイベントを送信すると同時に、あらかじめ設定済みのサーバーサイドアクション（Amazon EventBridge / LINE / SendGrid / ネイティブア…
- `get_campaign` — 接客サービス（キャンペーン。ポップアップ・メール等の配信設定一式）の詳細をIDで1件取得する（POST /v2beta/action/campaign/findById）
- `get_campaign_stats` — 全接客サービス（キャンペーン）の設定と効果測定データをCSV形式で一括取得する（POST /v2beta/action/campaign/getSettingsAndStats）

### kingtime — KING OF TIME（勤怠管理）

- `get_employees` — 従業員マスタの一覧を取得する
- `get_employee` — 従業員コード（code）を指定して従業員1名の情報を取得する
- `get_divisions` — 所属（division）データの一覧を取得する
- `get_working_types` — 雇用区分（正社員・契約社員・アルバイト等）のマスタデータ一覧を取得する
- `get_employee_groups` — 従業員グループのマスタデータ一覧を取得する
- `get_timerecords` — 指定期間の実際の打刻イベント一覧（出勤・退勤・休憩開始/終了・外出・外出から戻りの各打刻時刻そのもの）を取得する
- `get_daily_workings` — 指定期間の日別勤怠集計データ（従業員ごとの所定時間・残業時間・深夜時間・遅刻/早退時間・休憩時間などの分単位の集計値）を取得する
- `get_monthly_workings` — 指定月の月別勤怠集計データ（総労働時間・残業時間・深夜労働・遅刻/早退回数・取得休暇など）を取得する
- `get_daily_schedules` — 指定期間のシフト・スケジュール（出勤予定時刻・退勤予定時刻・休憩予定・休暇予定など）を取得する
- `record_time` — 従業員1名の打刻を1件登録する

### lineworks — LINE WORKS（ビジネスチャット）

- `get_channel` — Bot が参加している特定のトークルーム（チャンネル）1件の情報（タイトル・チャンネル種別SINGLE_USER/MULTI_USERS/ORGUNIT/GROUP など）を取得…
- `send_channel_message` — 指定したトークルーム（チャンネル）にテキストメッセージを Bot から送信する
- `send_user_message` — Bot から特定のユーザー1名にダイレクトメッセージ（テキスト）を送信する
- `list_members` — テナント（ドメイン）に所属するメンバー（ユーザー）一覧を取得する
- `get_member` — 特定メンバー1名の詳細情報（氏名、所属組織・部署・役職、電話番号、雇用状態などのフラグ）を取得する
- `search_users` — テナント内のメンバーを氏名などのキーワードで検索する
- `list_orgunits` — テナントの組織（部署・事業部など）一覧を取得する（GET /orgunits、公式ドキュメントで実在確認済み）
- `get_orgunit` — 特定の組織（部署）1件の詳細情報（組織名・メールアドレス・説明・親組織ID・トーク/ノート/カレンダー等の各機能利用フラグなど）を取得する（GET /orgunits/{orgU…
- `list_orgunit_members` — 特定の組織（部署）に所属するメンバー一覧を取得する（GET /orgunits/{orgUnitId}/members、公式ドキュメントで実在確認済み）
- `list_groups` — テナントのグループ（プロジェクトチーム・委員会など、組織階層とは別に作られる横断的なグループ）一覧を取得する（GET /groups、公式ドキュメントで実在確認済み）
- `get_group` — 特定のグループ1件の詳細情報（グループ名・説明・グループメールアドレス・管理者一覧・メンバー一覧・各機能利用フラグなど）を取得する（GET /groups/{groupId}、公…
- `list_group_members` — 特定のグループに所属するメンバー一覧を取得する（GET /groups/{groupId}/members、公式ドキュメントで実在確認済み）

### lstep — Lステップ（LINE マーケティング）

- `list_friends` — 友だち（LINE公式アカウントを追加したユーザー）の一覧を、付与済みタグ・友だち情報（カスタム属性）・対応マークを展開した状態で取得する
- `add_tag_to_friend` — 友だち1人にタグを1件以上まとめて付与する
- `remove_tag_from_friend` — 友だち1人からタグを1件以上まとめて解除する
- `set_response_mark` — 友だち1人の対応マーク（「対応済み」「未対応」等、問い合わせ対応状況を示す管理画面上のラベル）を1件設定する
- `create_friend_info_folder` — 友だち情報（友だちごとのカスタム属性項目）を整理するためのフォルダを新規作成する
- `create_friend_info` — 友だち情報（例: 誕生日、購入回数など友だちごとに値が異なるカスタム属性項目）の定義を新規作成する
- `list_tag_folders` — タグフォルダの一覧を取得する
- `create_tag_folder` — タグフォルダを新規作成する
- `list_tags` — 登録済みタグの一覧を、タグID・名前・所属フォルダとともに取得する
- `create_tag` — 新しいタグを作成する
- `update_tag` — 既存タグの名前・所属フォルダを部分更新する（name・folder_id とも省略した項目は変更されない）
- `list_friends_by_tag` — 指定タグが付与されている友だちの一覧を取得する
- `bulk_add_tag` — 1件のタグを複数の友だちへ一括付与する
- `bulk_remove_tag` — 1件のタグを複数の友だちから一括解除する
- `list_taiou_marks` — 対応マーク（問い合わせ対応状況を示す管理画面上のラベル。例: 対応済み/未対応）の一覧をIDと名前付きで取得する
- `get_message_history` — 友だちとのLINEメッセージ履歴（受信・送信・システムメッセージ）を検索・取得する
- `list_common_info_folders` — 共通情報フォルダの一覧を取得する（共通情報とは何かは list_common_infos の説明を参照）
- `list_common_infos` — 共通情報（特定の友だちに紐づかず、アカウント全体で共有される固定値。例: 営業時間・定休日・問い合わせ先URLなど）の一覧を取得する
- `update_common_info` — 共通情報（アカウント全体で共有される固定値。list_common_infos 参照）1件の値を更新する
- `list_templates` — 配信テンプレート（あらかじめ管理画面で作成されたメッセージひな形）の一覧をID・名前・所属フォルダとともに取得する
- `upload_media` — 画像ファイルをLステップの登録メディア一覧にアップロードする（現状 API 経由で指定できる種別は image のみ）

### makeleaps — MakeLeaps（請求書・見積書）

- `list_clients` — 取引先（クライアント）一覧を取得する
- `list_documents` — 書類（請求書・見積書・発注書・納品書等）一覧を取得する
- `get_document` — 指定した1件の書類の詳細情報（明細行・金額・送付ステータス等の全フィールド）を取得する
- `list_document_templates` — 指定した書類種別（document_type）で使用できる書類テンプレートの一覧を取得する
- `create_document` — 新しい書類（請求書・見積書等）を1件作成する
- `send_document` — 作成済みの書類をメールで送付する（MakeLeapsの「Secure Send」機能を使用）

### mazrica — Mazrica Sales（SFA）

- `list_customers` — 取引先（顧客企業）の一覧を取得する
- `create_customer` — 新しい取引先を1件登録する
- `list_deals` — 案件（商談）の一覧を取得する
- `create_deal` — 新しい案件（商談）を1件登録する
- `list_deal_types` — 登録済みの案件タイプ（id・name）の一覧を取得する
- `get_deal_type` — 指定した案件タイプ1件の詳細設定（フェーズ・商品・契約確度・チャネル・最終停止理由・詳細項目設定などの一覧、それぞれ id と name を含む）を取得する
- `list_users` — ユーザー（営業担当者）の一覧を取得する

### misoca — Misoca（見積・請求書）

- `list_invoices` — 請求書一覧を取得する
- `get_invoice` — 請求書1件の詳細（明細行・金額内訳・入金/請求ステータス・宛先情報など）を取得する
- `create_invoice` — 新しい請求書を作成する
- `mark_invoice_paid` — 請求書を入金済みにする（PUT /invoice/{id}/paid）
- `mark_invoice_unpaid` — 請求書を未入金の状態に戻す（DELETE /invoice/{id}/paid）
- `mark_invoice_submitted` — 請求書を請求済みステータスにする（PUT /invoice/{id}/submitted）
- `mark_invoice_unsubmitted` — 請求書を未請求ステータスに戻す（DELETE /invoice/{id}/submitted）
- `trash_invoice` — 請求書をごみ箱に移動する（PUT /invoice/{id}/trashed）
- `restore_invoice` — ごみ箱に移動した請求書を元に戻す（DELETE /invoice/{id}/trashed）
- `list_contact_groups` — 取引先（顧客企業単位のマスタ情報）の一覧を取得する
- `list_contacts` — 送り先（取引先ごとに登録できる請求書の宛先。同じ取引先内の複数部署・複数担当者などを表す）の一覧を取得する

### notepm — NotePM（社内wiki）

- `list_notes` — ノート（NotePM上でページをグルーピングする「フォルダ」に近い単位。他コネクタの「スペース」「プロジェクト」に相当）の一覧を取得する
- `search_pages` — ページを検索・一覧取得する（NotePM APIでは検索専用エンドポイントは存在せず、GET /pages が検索とページ一覧取得を兼ねている。条件を何も指定しなければ全ノート横…
- `get_page` — ページコードを指定して1件のページ詳細（本文・タグ・所属ノート・コメント一覧を含む）を取得する
- `create_page` — 指定したノート配下に新しいページを作成する
- `update_page` — 既存ページを部分更新する

### payjp — PAY.JP（決済）

- `list_charges` — 決済（charge）の一覧を取得する
- `get_charge` — 指定した課金ID（ch_ で始まる）の決済詳細を1件取得する
- `refund_charge` — 指定した決済を返金する
- `list_customers` — 顧客の一覧を取得する
- `list_subscriptions` — サブスクリプション（定期課金）の一覧を取得する

### pipedrive — Pipedrive（CRM）

- `list_persons` — 人物（コンタクト）の一覧を取得する
- `search_persons` — 人物（コンタクト）を名前・メール・電話番号・メモ・カスタムフィールドの値で検索する
- `list_deals` — 案件（Deal）の一覧を取得する
- `create_deal` — 新しい案件（Deal）を1件作成する
- `list_activities` — アクティビティ（電話・訪問・タスクなどの商談活動）の一覧を取得する

### relation — Re:lation（CS・メール共有）

- `list_message_boxes` — 受信箱（メールボックス）の一覧を取得する
- `search_tickets` — 指定した受信箱内のチケット（問い合わせ）を条件検索する
- `get_ticket` — チケット1件の詳細情報を取得する
- `create_reply_memo` — 既存チケットに対応履歴（応対メモ、社内向けの対応記録）を1件追加する（POST、呼び出すたびに新規のメモが作成され、重複防止の仕組みはRE:lation側に存在しないためべき等で…
- `list_users` — RE:lationのユーザー（オペレーター）一覧を取得する

### sendgrid — SendGrid（メール配信）

- `send_email` — SendGrid Mail Send API（POST /v3/mail/send）経由でメールを1通送信する
- `get_stats` — アカウント全体のメール送信統計（配信数・開封数・クリック数・バウンス数・配信停止数等）をGET /v3/stats で取得する
- `list_bounces` — バウンス（宛先不明・メールボックス満杯等で配信できなかった）メールアドレスの抑制リストを GET /v3/suppression/bounces で取得する
- `list_unsubscribes` — グローバル配信停止（Global Unsubscribes/Suppressions）リストを GET /v3/suppression/unsubscribes で取得する
- `list_templates` — メールテンプレート一覧を GET /v3/templates で取得する（カーソル方式のページネーション）

### smaregi — スマレジ（POS・店舗管理）

- `list_products` — スマレジに登録されている商品のマスタ情報（商品名・価格・部門ID・商品コード等）の一覧を取得する
- `get_product` — 商品IDを指定して、その商品1件の詳細情報（商品名・価格・部門ID・商品コード等）を取得する
- `list_transactions` — 売上取引（レシート単位の取引ヘッダ）の一覧を取得する
- `list_customers` — スマレジに登録されている会員（顧客）の一覧を取得する
- `list_stock` — 商品・店舗ごとの在庫数（在庫数・取置き在庫数）の一覧を取得する
- `get_stock_changes` — 商品ID・店舗IDを指定して、その組み合わせの在庫変動履歴（いつ・何が原因で・いくつ増減し、結果として在庫がいくつになったか）を取得する
- `get_transaction_details` — 取引ID（list_transactions のレスポンスの transactionHeadId）を指定して、その取引の明細（購入商品行ごとの商品名・数量・単価・値引き・税区分等…
- `list_categories` — スマレジに登録されている部門（商品カテゴリ）の一覧を取得する
- `list_stores` — スマレジに登録されている店舗（および倉庫）の一覧を取得する

### smarthr — SmartHR（人事・労務）

- `list_crews` — 指定した条件に合致する従業員（crew）の一覧を取得する（SmartHR公式APIの GET /v1/crews に対応）
- `get_crew` — 従業員（crew）1名の詳細情報を取得する（GET /v1/crews/{id}）
- `list_departments` — 部署一覧を取得する（GET /v1/departments）
- `list_employment_types` — 雇用形態一覧を取得する（GET /v1/employment_types、正社員・パート・契約社員等）
- `update_crew` — 従業員情報を部分更新する（PATCH /v1/crews/{id}）
- `list_dependents` — 指定した従業員に紐づく家族情報（扶養家族等）の一覧を取得する（GET /v1/crews/{crew_id}/dependents）
- `list_job_titles` — 役職一覧を取得する（GET /v1/job_titles）
- `list_grades` — 等級一覧を取得する（GET /v1/grades）
- `list_job_categories` — 職種一覧を取得する（GET /v1/job_categories）
- `list_recruitment_types` — 採用区分一覧を取得する（GET /v1/recruitment_types）
- `list_dependent_relations` — 続柄（家族情報の続柄区分）の一覧を取得する（GET /v1/dependent_relations）
- `list_biz_establishments` — 事業所一覧を取得する（GET /v1/biz_establishments）
- `list_users` — SmartHRのログインユーザー（管理者・利用者アカウント）一覧を取得する（GET /v1/users）
- `list_companies` — 会社情報の一覧を取得する（GET /v1/companies）
- `list_payment_periods` — 給与支給形態の一覧を取得する（GET /v1/payment_periods）

### talentio — Talentio（採用管理）

- `list_candidates` — 候補者（＝応募者）の一覧を取得する
- `get_candidate` — 候補者1名の詳細情報を取得する
- `list_jobs` — 求人（Talentio API 上は requisition と呼ばれる）の一覧を取得する
- `get_job` — 求人1件の詳細情報を取得する
- `list_job_titles` — 職種（job title）の一覧を取得する
- `list_candidate_channels` — 候補者の応募経路（チャネル。転職サイト・エージェント・社員紹介・自由入力など）の一覧を取得する
- `list_form_templates` — 評価フォームテンプレート（選考時に使う評価項目のひな形）の一覧を取得する
- `list_employees` — Talentio 利用メンバー（社員アカウント）の一覧を取得する
- `list_employee_groups` — メンバーの所属グループ（組織構成）の一覧を取得する
- `list_workspaces` — ワークスペース（テナント）の一覧を取得する
- `list_deleted_candidates` — 削除済み候補者の一覧（候補者IDと削除日時のみ）を削除日時の降順で取得する
- `list_candidate_comments` — 指定した候補者への社内コメント（選考メモ等）一覧を取得する
- `list_candidate_attachments` — 指定した候補者に添付されているファイル（履歴書・職務経歴書等）の一覧（ID・ファイル名のみ）を取得する

### toggl — Toggl Track（時間計測）

- `get_profile` — 現在のユーザー（このAPIトークンの所有者）のプロファイルを取得する
- `list_workspaces` — このユーザーが所属するワークスペース（Toggl Trackの契約・請求単位となる組織）の一覧を取得する
- `list_projects` — 指定ワークスペース内のプロジェクト一覧を取得する
- `list_clients` — 指定ワークスペース内のクライアント（請求先企業）一覧を取得する
- `list_time_entries` — 認証ユーザー自身の時間計測エントリー一覧を取得する
- `create_time_entry` — 新しい時間計測エントリーを1件作成する
- `update_time_entry` — 既存の時間計測エントリー1件を更新する（PUT）
- `stop_time_entry` — 実行中（duration が負の値）の時間計測エントリーを停止し、現在時刻を終了時刻として確定する
- `delete_time_entry` — 時間計測エントリー1件を削除する

### trello — Trello（プロジェクト管理）

- `list_boards` — 自分（このトークンのユーザー）が所属するボード一覧を取得する
- `list_lists` — 指定したボード内のリスト（カンバンの列。例: 未着手/進行中/完了）一覧を取得する
- `list_cards` — 指定したリスト内のカード一覧を取得する
- `create_card` — 指定したリストに新しいカードを1枚作成する
- `move_card` — 既存のカードを別のリストへ移動する（PUT /1/cards/{id} の idList のみを更新する）

### typeform — Typeform（フォーム作成）

- `list_forms` — アカウント内のフォーム（Typeform）一覧を取得する
- `get_form` — 1件のフォームをIDで指定して詳細（タイトル・質問（fields）構成・ロジック分岐・テーマ・settings等）を取得する
- `get_responses` — 指定フォームの回答一覧を取得する（GET /forms/{form_id}/responses）
- `list_workspaces` — アカウント内のワークスペース一覧を取得する（GET /workspaces）
- `get_response_summary` — 指定フォームの回答インサイト（サマリー統計。質問ごとの回答分布・完了率など）を取得する（GET /insights/{form_id}/summary）

### yappli-crm — Yappli CRM（モバイルCRM）

- `list_users` — Yappli CRMに登録されている会員（顧客）の一覧を取得する
- `get_user` — YappliCRMの会員ID（内部ID）を指定して、会員1件の詳細情報（ランク・保有ポイント・カスタムフィールド・ログイン状態など）を取得する
- `get_user_by_unique_id` — 会員登録時に指定した unique_id（お客様側システムでの一意な識別子）で会員1件の詳細情報を検索する
- `get_user_by_external_id` — 外部連携ID（POSシステムやECサイトなど、連携している外部サービス側のID。create_user/update_userの external_ids で保存した値）で会員1…
- `create_user` — 新規会員を登録する
- `update_user` — 既存会員（YappliCRMの会員ID指定）の情報を更新する
- `delete_external_id` — 会員に紐づく外部連携ID（POSシステムやECサイトなどのID）を1件削除し、連携を解除する
- `get_user_points` — 会員に対して行われたポイント付与・減算の履歴を取得する
- `get_points_expired_list` — 会員が保有するポイントのうち、有効期限が近い順に有効期限日ごとの失効予定ポイント数を集計して取得する（個々の付与履歴ではなく、期限日単位のサマリ）
- `add_user_points` — 会員にポイントを付与（正の値）または減算（負の値）する
- `calculate_points` — Yappli CRMの環境設定で定義されたランク別のポイント付与率を使い、指定した計算対象額（amount）から自動算出したポイント数を会員に付与する

<!-- tools:end -->

---

## セットアップ

### 必要なもの

- Python 3.10 以上
- [Claude Desktop](https://claude.ai/download) または MCP 対応クライアント

### インストール

各コネクタは独立したパッケージです。使いたいコネクタのディレクトリで `pip install -e .` を実行します。

```bash
# 例: SmartHR コネクタをインストール
cd smarthr
pip install -e .
```

### Claude Desktop への設定

`~/Library/Application Support/Claude/claude_desktop_config.json`（macOS）を編集します。

```json
{
  "mcpServers": {
    "smarthr": {
      "command": "smarthr-mcp",
      "env": {
        "SMARTHR_ACCESS_TOKEN": "your_access_token", # pragma: allowlist secret
        "SMARTHR_TENANT_ID": "your_tenant_id"
      }
    }
  }
}
```

各コネクタの詳細なセットアップ手順・必要な環境変数は、各ディレクトリの `README.md` を参照してください。

### 公式 MCP Registry

主力コネクタは [公式 MCP Registry](https://registry.modelcontextprotocol.io/) に登録しています。Registry に対応したクライアントからは、次の名前で探せます。
パッケージは GHCR の Docker イメージ（`ghcr.io/mediiiiium/<コネクタ名>-mcp`）です。

| Registry 名 | サービス |
|---|---|
| `io.github.mediiiiium/smarthr` | SmartHR |
| `io.github.mediiiiium/kingtime` | KING OF TIME |
| `io.github.mediiiiium/smaregi` | スマレジ |
| `io.github.mediiiiium/cloudsign` | クラウドサイン |

### Claude Code プラグイン（スキルつき）

主力コネクタは、MCP サーバーと [Claude のスキル](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)（準備・進め方・書き込み時の注意をまとめた SKILL.md）をまとめたプラグインとしても配布しています。
MCP サーバーは Docker イメージで動くので、Docker と各サービスの環境変数が必要です。

```
/plugin install mcp-jp-smarthr --marketplace mediiiiium/mcp-jp
```

| プラグイン | サービス | スキル |
|---|---|---|
| [`plugins/smarthr/`](./plugins/smarthr/) | SmartHR | [SKILL.md](./plugins/smarthr/skills/smarthr/SKILL.md) |
| [`plugins/kingtime/`](./plugins/kingtime/) | KING OF TIME | [SKILL.md](./plugins/kingtime/skills/kingtime/SKILL.md) |
| [`plugins/smaregi/`](./plugins/smaregi/) | スマレジ | [SKILL.md](./plugins/smaregi/skills/smaregi/SKILL.md) |
| [`plugins/cloudsign/`](./plugins/cloudsign/) | クラウドサイン | [SKILL.md](./plugins/cloudsign/skills/cloudsign/SKILL.md) |

スキルだけ使う場合は、`plugins/<コネクタ名>/skills/<コネクタ名>/` を `~/.claude/skills/` にコピーします。

---

## 構造

各コネクタは以下の構成で統一されています。

```
{connector}/
├── pyproject.toml          # パッケージ設定
├── README.md               # セットアップ手順・ツール一覧
└── src/{connector}_mcp/
    ├── __init__.py
    ├── _http.py            # 共通ヘルパー（レスポンス整形・エラー処理）
    └── server.py           # MCP サーバー実装
```

`_http.py` は全コネクタ共通（外部依存を増やさないため各パッケージに同梱）。
API エラーは生のスタックトレースではなく原因と対処を示すメッセージに変換し、
大きすぎるレスポンスは LLM のコンテキストを溢れさせないよう切り詰める。

公式 MCP が提供されたサービスのコネクタは [`archive/`](./archive/) に退避している。

---

## コントリビュート

新しいコネクタのリクエストや PR を歓迎します。

**「このSaaSを繋ぎたい」だけでも歓迎です** — [コネクタのリクエストはこちら](https://github.com/mediiiiium/mcp-jp/issues/new?template=connector-request.yml)。非エンジニアの方は [note](https://note.com/mediiiiium) のコメントからでも構いません。需要として記録し、重なっているものから優先して実装します。

**コネクタ追加の前に:**
- [候補選定マトリクス](./docs/connector-candidates.md)でスコアリングしてから着手してください（公式MCP不在の持続性・需要・検証可能性・日本SMB密着度）
- 対象サービスの公式 MCP が存在しないか確認してください（[公式MCP一覧](#公式mcpが提供されているサービス)を参照）。既にある場合は作らない
- 公開された REST API ドキュメントが存在し、テスト用クレデンシャルを取得できることを確認してください

**実装のガイドライン:**
- 1 コネクタあたり 5 つ前後のツールを実装する
- 認証情報は環境変数で渡す
- レスポンス整形・エラー処理は共通ヘルパー `_http.py`（`format_response` / `error_response`）を使う
- 各コネクタに `README.md`（セットアップ手順・ツール一覧・使用例）を含める
- 既存のコネクタ（例: [`payjp/`](./payjp/)）を参考にパターンを合わせる

---

## ライセンス

[MIT License](./LICENSE)
