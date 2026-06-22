# mcp-jp

日本SMB向け MCP サーバー集

## コネクタ一覧

### 日本SMB向けローカルSaaS（公式MCPなし → 独自実装）

| ディレクトリ | サービス | ステータス |
|-------------|---------|-----------|
| `lstep/` | Lステップ（LINE MA） | 開発中（API全19エンドポイント実装済み） |
| `kingtime/` | KING OF TIME（勤怠管理） | 開発中（5ツール実装済み） |
| `smarthr/` | SmartHR（人事・労務管理） | 開発中（5ツール実装済み） |
| `kaonavi/` | カオナビ（タレントマネジメント） | 開発中（5ツール実装済み） |
| `mazrica/` | Mazrica Sales（SFA・営業支援） | 開発中（5ツール実装済み） |
| `invox/` | invox（受取請求書・仕訳エクスポート） | 開発中（5ツール実装済み） |
| `smaregi/` | スマレジ（POSレジ・店舗管理） | 開発中（5ツール実装済み） |
| `garoon/` | Garoon（サイボウズ グループウェア） | 開発中（5ツール実装済み） |
| `jobcan-workflow/` | ジョブカン経費精算/ワークフロー | 開発中（5ツール実装済み） |
| `base-ec/` | BASE（ECプラットフォーム） | 開発中（5ツール実装済み） |
| `esa/` | esa（チームナレッジ共有） | 開発中（5ツール実装済み） |
| `cloudsign/` | クラウドサイン（電子契約・電子署名） | 開発中（5ツール実装済み） |
| `herp/` | HERP Hire（採用管理システム） | 開発中（5ツール実装済み） |
| `talentio/` | Talentio（採用管理システム） | 開発中（5ツール実装済み） |
| `lineworks/` | LINE WORKS（ビジネスチャット・グループウェア） | 開発中（5ツール実装済み）JWT認証 |
| `board/` | board（業務・経営管理・請求書管理） | 開発中（5ツール実装済み） |
| `jooto/` | Jooto（タスク・プロジェクト管理） | 開発中（5ツール実装済み） |

### グローバルSaaS（公式MCPなし → 独自実装）

| ディレクトリ | サービス | ステータス |
|-------------|---------|-----------|
| `pipedrive/` | Pipedrive（CRM・営業パイプライン管理） | 開発中（5ツール実装済み） |
| `freshdesk/` | Freshdesk（カスタマーサポート・ヘルプデスク） | 開発中（5ツール実装済み）公式MCP EAP中 |
| `intercom/` | Intercom（カスタマーメッセージング・CRM） | 開発中（5ツール実装済み） |
| `trello/` | Trello（カンバン型プロジェクト管理） | 開発中（5ツール実装済み） |
| `toggl/` | Toggl Track（時間計測・工数管理） | 開発中（5ツール実装済み） |
| `harvest/` | Harvest（時間計測・請求書・プロジェクト管理） | 開発中（5ツール実装済み） |
| `typeform/` | Typeform（フォーム作成・アンケート） | 開発中（5ツール実装済み） |
| `sendgrid/` | SendGrid（メール送信・マーケティング） | 開発中（5ツール実装済み）Twilio MCP経由で部分対応 |

### 公式MCPが存在するサービス（参考実装）

| ディレクトリ | サービス | ステータス |
|-------------|---------|-----------|
| `freee/` | freee会計 | ~~開発中~~ → **公式MCPあり**（2026年3月公開、270 API）|
| `mfcloud/` | マネーフォワードクラウド | ~~開発中~~ → **公式MCPあり**（2026年3月全プラン開放）|
| `kintone/` | kintone | ~~開発中~~ → **公式MCPあり**（2026年5月公式QSG公開）|
| `chatwork/` | Chatwork（ビジネスチャット） | ~~開発中~~ → **公式MCPあり**（chatwork/chatwork-mcp-server）|
| `backlog/` | Backlog（プロジェクト管理・課題追跡） | ~~開発中~~ → **公式MCPあり**（nulab/backlog-mcp-server）|
| `sansan/` | Sansan（名刺管理・人脈管理） | ~~開発中~~ → **公式MCPあり**（2025年11月提供開始）|
| `zendesk/` | Zendesk（カスタマーサポート） | ~~開発中~~ → **公式MCPあり**（2026年夏 GA予定）|
| `hubspot/` | HubSpot CRM（営業・マーケティング） | ~~開発中~~ → **公式MCPあり**（mcp.hubspot.com、2026年4月 GA）|
| `notion/` | Notion（ナレッジ管理・プロジェクト管理） | ~~開発中~~ → **公式MCPあり**（mcp.notion.com）|
| `stripe/` | Stripe（決済・請求管理） | ~~開発中~~ → **公式MCPあり**（mcp.stripe.com）|
| `twilio/` | Twilio（SMS・音声通話） | ~~開発中~~ → **公式MCPあり**（Twilio Alpha MCP、Public Beta）|
| `airtable/` | Airtable（スプレッドシート型DB） | ~~開発中~~ → **公式MCPあり**（2026年2月 GA）|
| `gitlab/` | GitLab（ソースコード管理・CI/CD） | ~~開発中~~ → **公式MCPあり**（GitLab Duo MCP、Beta）|
| `asana/` | Asana（プロジェクト管理・タスク管理） | ~~開発中~~ → **公式MCPあり**（mcp.asana.com V2、2026年2月）|
| `jira/` | Jira（プロジェクト管理・課題追跡） | ~~開発中~~ → **公式MCPあり**（Atlassian MCP、2026年2月 GA）|
| `shopify/` | Shopify（ECプラットフォーム） | ~~開発中~~ → **公式MCPあり**（Storefront/Dev MCP、2026年1月〜）|
| `mailchimp/` | Mailchimp（メールマーケティング） | ~~開発中~~ → **公式MCPあり**（Intuit/Anthropic連携、2026年春）|
| `confluence/` | Confluence（ナレッジ管理・ドキュメント共有） | ~~開発中~~ → **公式MCPあり**（Atlassian MCP、2026年2月 GA）|
| `square/` | Square（決済・店舗管理） | ~~開発中~~ → **公式MCPあり**（mcp.squareup.com、Beta）|
| `box/` | Box（クラウドストレージ・ドキュメント管理） | ~~開発中~~ → **公式MCPあり**（mcp.box.com、2025年8月 GA）|
| `zoom/` | Zoom（ビデオ会議・ウェビナー管理） | ~~開発中~~ → **公式MCPあり**（Zoom MCP、2026年4月〜）|
| `dropbox/` | Dropbox（クラウドストレージ・ファイル共有） | ~~開発中~~ → **公式MCPあり**（mcp.dropbox.com、2026年3月 GA）|
| `pagerduty/` | PagerDuty（インシデント管理・オンコール管理） | ~~開発中~~ → **公式MCPあり**（PagerDuty/pagerduty-mcp-server）|
| `datadog/` | Datadog（クラウド監視・モニタリング） | ~~開発中~~ → **公式MCPあり**（datadog-labs/mcp-server、2026年3月 GA）|
| `clickup/` | ClickUp（プロジェクト管理・タスク管理） | ~~開発中~~ → **公式MCPあり**（mcp.clickup.com、Public Beta）|
| `calendly/` | Calendly（スケジュール調整・予約管理） | ~~開発中~~ → **公式MCPあり**（mcp.calendly.com）|
| `brevo/` | Brevo（メール・SMS マーケティング） | ~~開発中~~ → **公式MCPあり**（mcp.brevo.com）|
| `activecampaign/` | ActiveCampaign（マーケティングオートメーション・CRM） | ~~開発中~~ → **公式MCPあり**（mcp.activecampaign.com）|
| `sentry/` | Sentry（エラートラッキング・パフォーマンス監視） | ~~開発中~~ → **公式MCPあり**（getsentry/sentry-mcp、mcp.sentry.dev）|
| `heroku/` | Heroku（PaaS・アプリデプロイ管理） | ~~開発中~~ → **公式MCPあり**（heroku/heroku-mcp-server）|
| `cloudflare/` | Cloudflare（CDN・DNS・セキュリティ管理） | ~~開発中~~ → **公式MCPあり**（cloudflare/mcp-server-cloudflare）|
| `vercel/` | Vercel（フロントエンドデプロイ・ホスティング） | ~~開発中~~ → **公式MCPあり**（mcp.vercel.com、2025年8月〜）|
| `circleci/` | CircleCI（CI/CD パイプライン管理） | ~~開発中~~ → **公式MCPあり**（CircleCI-Public/mcp-server-circleci）|
| `colormeshop/` | カラーミーショップ（ECカート構築） | ~~開発中~~ → **公式MCPあり**（リモートMCPサーバー、2026年3月 GA）|

## 次の候補

| サービス | カテゴリ | API状況 | 優先度 |
|---------|---------|--------|-------|
| CYDAS | タレントマネジメント | 要申し込み（developer.cydas.com） | 高（アカウント取得後） |
| LetterSeal | 郵送 | 調査中 | 中 |

## 思想

- ベンダーがMCPを出していればそれを使う
- 日本SMBローカルのSaaSで、ベンダーが作らないものを自分たちが作る
- Claude等のAIエージェントから日本のSaaSを操作できるようにする
- 新しいコネクタを作る前に必ず公式MCPの有無を確認する

## 使い方

各ディレクトリのREADMEを参照。
