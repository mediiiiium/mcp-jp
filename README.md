# mcp-jp — Japanese SMB SaaS connectors

**日本の SMB 向け SaaS に対応した MCP サーバー集**

Claude などの AI エージェントから、日本のクラウドサービスを自然言語で操作できるようにします。
公式 MCP が存在しないサービスへのコネクタを独自実装しています。

> このリポジトリの狙いと収益化の考え方は [戦略メモ](./docs/strategy.md) を参照。

---

## コネクタ一覧

### 日本SMB向け（独自実装）

| コネクタ | サービス | カテゴリ |
|---------|---------|---------|
| [`lstep/`](./lstep/) | [Lステップ](https://liff.line.me/) | LINE マーケティング |
| [`kingtime/`](./kingtime/) | [KING OF TIME](https://www.kingtime.jp/) | 勤怠管理 |
| [`smarthr/`](./smarthr/) | [SmartHR](https://smarthr.jp/) | 人事・労務 |
| [`kaonavi/`](./kaonavi/) | [カオナビ](https://kaonavi.jp/) | タレントマネジメント |
| [`mazrica/`](./mazrica/) | [Mazrica Sales](https://mazrica.com/) | SFA |
| [`invox/`](./invox/) | [invox](https://invox.jp/) | 受取請求書 |
| [`smaregi/`](./smaregi/) | [スマレジ](https://smaregi.jp/) | POS・店舗管理 |
| [`garoon/`](./garoon/) | [Garoon](https://garoon.cybozu.co.jp/) | グループウェア |
| [`jobcan-workflow/`](./jobcan-workflow/) | [ジョブカン経費精算/ワークフロー](https://workflow.jobcan.ne.jp/) | 経費・ワークフロー |
| [`base-ec/`](./base-ec/) | [BASE](https://thebase.com/) | EC |
| [`esa/`](./esa/) | [esa](https://esa.io/) | チームナレッジ |
| [`cloudsign/`](./cloudsign/) | [クラウドサイン](https://www.cloudsign.jp/) | 電子契約 |
| [`herp/`](./herp/) | [HERP Hire](https://herp.co/) | 採用管理 |
| [`talentio/`](./talentio/) | [Talentio](https://talentio.com/) | 採用管理 |
| [`lineworks/`](./lineworks/) | [LINE WORKS](https://line-works.com/) | ビジネスチャット |
| [`board/`](./board/) | [board](https://the-board.jp/) | 経営・請求書管理 |
| [`jooto/`](./jooto/) | [Jooto](https://www.jooto.com/) | タスク・プロジェクト管理 |
| [`hrmos-kintai/`](./hrmos-kintai/) | [HRMOS勤怠](https://ieyasu.co/) | 勤怠管理 |
| [`misoca/`](./misoca/) | [Misoca](https://www.misoca.jp/) | 見積・請求書 |
| [`makeleaps/`](./makeleaps/) | [MakeLeaps](https://www.makeleaps.jp/) | 請求書・見積書 |
| [`notepm/`](./notepm/) | [NotePM](https://notepm.jp/) | 社内wiki |
| [`relation/`](./relation/) | [Re:lation](https://ingage.jp/relation/) | CS・メール共有 |
| [`karte/`](./karte/) | [KARTE](https://karte.io/) | MA・CDP |
| [`akashi/`](./akashi/) | [AKASHI / MFクラウド勤怠Plus](https://ak4.jp/) | 勤怠管理 |
| [`yappli-crm/`](./yappli-crm/) | [Yappli CRM](https://yapp.li/crm/) | モバイルCRM |
| [`payjp/`](./payjp/) | [PAY.JP](https://pay.jp/) | 決済 |

### グローバルSaaS（独自実装）

| コネクタ | サービス | カテゴリ |
|---------|---------|---------|
| [`pipedrive/`](./pipedrive/) | [Pipedrive](https://www.pipedrive.com/) | CRM |
| [`freshdesk/`](./freshdesk/) | [Freshdesk](https://freshdesk.com/) | カスタマーサポート |
| [`intercom/`](./intercom/) | [Intercom](https://www.intercom.com/) | CS・メッセージング |
| [`trello/`](./trello/) | [Trello](https://trello.com/) | プロジェクト管理 |
| [`toggl/`](./toggl/) | [Toggl Track](https://toggl.com/) | 時間計測 |
| [`harvest/`](./harvest/) | [Harvest](https://www.getharvest.com/) | 時間計測・請求書 |
| [`typeform/`](./typeform/) | [Typeform](https://www.typeform.com/) | フォーム作成 |
| [`sendgrid/`](./sendgrid/) | [SendGrid](https://sendgrid.com/) | メール配信 |

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

> これらのサービスについては、過去に独自実装したコネクタを [`archive/`](./archive/) に移動し、メンテナンス対象外としています。新規利用では公式 MCP を使ってください。

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
        "SMARTHR_CLIENT_ID": "your_client_id",
        "SMARTHR_CLIENT_SECRET": "your_client_secret", # pragma: allowlist secret
        "SMARTHR_SUBDOMAIN": "your_subdomain"
      }
    }
  }
}
```

各コネクタの詳細なセットアップ手順・必要な環境変数は、各ディレクトリの `README.md` を参照してください。

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
