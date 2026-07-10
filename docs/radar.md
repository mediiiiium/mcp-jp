# mcp-jp リサーチ・レーダー（2026年7月時点）

mcp-jp の発信ネタ・動向把握用のキュレーション。各項目に「なぜ関連か＋価値を足せる角度」を付記。本ドキュメントは **2026-07 時点のスナップショット** であり、一部は引用前に裏取りが必要（末尾の「投稿前の確認事項」参照）。

## JP SaaS × MCP（本丸）

- **freee-mcp（freee公式OSS・約270 API）**
  [GitHub: freee/freee-mcp](https://github.com/freee/freee-mcp) ／ [freee プレスリリース](https://corp.freee.co.jp/news/20260302freee_mcp.html)
  角度: 公開APIと「実務エージェントに必要なもの」のギャップ分析。

- **Money Forward リモートMCP（3月GA、Claude/Cursor/Gemini対応）**
  [Money Forward プレスリリース](https://corp.moneyforward.com/en/news/release/service/20260326-mf-press-1/)
  角度: freee vs MF の中立比較（認証・ツール網羅・remote UX）。最高価値の未着手ネタ。

- **kintone 公式MCP（Apache-2.0、公式＋非公式3つ乱立）**
  [GitHub: kintone/mcp-server](https://github.com/kintone/mcp-server) ／ [cybozu.dev 解説](https://cybozu.dev/ja/kintone/ai/kintone-mcp-server/)
  角度: どれを選ぶべきかの選定ガイド。

- **カラーミーショップ リモートMCP（国内EC初、開発者記事ゼロ）**
  [ASCII 記事](https://ascii.jp/elem/000/004/379/4379633/)
  角度: 最初のハンズオン連携チュートリアル（先行者利益）。

- **Sansan MCP PoC（エンタープライズ導入・住友トライアル）**
  [Sansan Builders Box](https://buildersbox.corp-sansan.com/entry/2025/12/24/170000) ／ [SalesZine 記事](https://saleszine.jp/news/detail/7860)
  角度: 実企業のMCP活用事例は希少。

- **Money Forward 勤怠 非公式MCP（個人自作）**
  [Zenn 記事](https://zenn.dev/91works/articles/c5dcc7d39bbc73)
  角度: 散在する個人サーバーの品質基準・受け皿を mcp-jp が担う。

## MCPエコシステム／レジストリ

- **MCP仕様 RC（2026-07-28、最大改定）**
  [MCP ブログ: Release Candidate](https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/) ／ [MCP レジストリ](https://registry.modelcontextprotocol.io/)
  角度: 日本のSaaS MCPを公式レジストリに登録する方法ガイド。一番空いてる。

- **「12,653 MCP Servers. Zero Quality Signals.」**
  [Phase Transitions AI（Substack）](https://phasetransitionsai.substack.com/p/12653-mcp-servers-zero-quality-signals)
  角度: mcp-jp ＝ JP特化の検証済みインデックスの存在意義そのもの。

- **X が公式MCPサーバー公開（2026-06-30）**
  [TechCrunch 記事](https://techcrunch.com/2026/06/30/x-now-offers-an-mcp-server-to-make-its-platform-easier-for-ai-tools-to-use/) ／ [rocket-boys 解説](https://rocket-boys.co.jp/security-measures-lab/x-official-mcp-server-xmcp-launch/)
  角度: JP SaaSがサーバーをどう公開すべきかのJP文脈の考察。

## 議論・設計品質

- **「freee-mcp のトークン代が月額より高くなった話」**
  [Qiita 記事](https://qiita.com/kenimo49/items/99eab0f669e43f8bda6e)
  角度: 重いMCPを使うべきでない時＆JP-SaaS MCPのトークン効率設計。

- **JP SaaS 100社のMCP対応調査（約35%対応）**
  [Qiita 記事](https://qiita.com/michie_yamaguchi/items/665890a406043cf3cb28)
  角度: ★mcp-jpと同コンセプトの商用（KanseiLink）。最良の参考＝最大の競合。差別化は開放性・中立・統合の深さ。

- **MCP認証 + OAuth 2.1/DCR 解説**
  [Zenn 記事](https://zenn.dev/luoxi/articles/mcp-auth-oauth-from-scratch)
  角度: freee/MF の OAuth がエージェントで実際どう動くか、APIキー vs OAuth2 の選定ガイド。

- **「MCP is dead; long live the CLI」論争（HN）**
  [Hacker News スレッド](https://news.ycombinator.com/item?id=47380270)
  角度: JPエンタープライズはガバナンス/ID駆動＝「CLIで十分」が崩れる事例で非US視点を足す。

- **MCPサプライチェーン／poisoned-tool セキュリティ**
  [The Hacker News: MCP design vulnerability](https://thehackernews.com/2026/04/anthropic-mcp-design-vulnerability.html) ／ [The Hacker News: poisoned MCP tool](https://thehackernews.com/2026/06/microsoft-warns-poisoned-mcp-tool.html)
  角度: 日本SaaSラッパー向けセキュリティ・レビュー・チェックリスト（APPI・データ所在含む）。

## フォロー・エンゲージ推奨アカウント

- **@karaage0703（からあげ）** — [x.com/karaage0703](https://x.com/karaage0703)
  JP MCPで最も安定した実践シグナル。一般ツール話をJP-SaaS特化に伸ばして絡む。

- **Michie Yamaguchi**（Qiita [@michie_yamaguchi](https://qiita.com/michie_yamaguchi) / X @michielinksee）
  同コンセプトを商用化中。ベンチマーク兼潜在コラボ。最重要ウォッチ。

- **kenimo49（Imoto Ken）**
  手を動かす批判派。コスト/設計批評に乗るのが非ハイプな入り方。

- **r3-yamauchi（アールスリー）**
  kintone MCP多作ビルダー（r3it.com）。@前にXハンドル要確認。

- **Classmethod「エンジニアのためのMCP勉強会」** — [connpass イベント](https://classmethod.connpass.com/event/352139/)
  JP最大のMCP勉強会（#1は約480人）。JP-SaaS MCP連携でLT登壇を狙う場。

## mcp-jp が独自の声を持てるレーン（強い順）

1. JP SaaS MCP の 開放・キュレーション・検証済みインデックス。
2. GA直後の中立ディープ比較（freee vs MF、kintone3種）。
3. 設計品質・コスト現実論（トークン効率、エージェント向けOAuth、領収書/ファイル処理）。
4. 空白カテゴリ（法務=CloudSign/GMOサイン/LegalOnゼロ、EC、SmartHR=API潤沢だが公式MCP無し）。
5. JP文脈のセキュリティ/ガバナンス（APPI・データ所在）＝US中心「MCPはブーム」論への反証。

## 投稿前の確認事項（裏取り）

- 「100社／35%」は単一調査（2026年4月・方向性は信頼可、単一ソース）。
- LINE公式MCPの有無は二次情報のみ、要確認。
- 一部Xハンドル（r3-yamauchi, kenimo49, shuji-bonji）は未検証。
- Redditは索引が薄い。r/mcp の top(month) を直接見ると正確。
