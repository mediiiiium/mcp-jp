# MCPエコシステム トレンドダイジェスト

> **2026-10-27 に停止しました。** 保守モードへの移行に合わせてワークフロー（`.github/workflows/mcp-trend-digest.yml`）を削除しました。
> スクリプト `scripts/mcp_trend_digest.py` は残しているので、ワークフローを戻せば再開できます。

`scripts/discover_candidates.py`（コネクタ候補発掘）とは目的が異なる仕組み。
あちらは「日本SMB SaaSの中から次に作るべきコネクタ候補」を発掘するのに対し、
これは**MCPエコシステム全体の動向を追い、自分の学習と情報源としてのポジションを
維持するため**の仕組み。

---

## 仕組み

`scripts/mcp_trend_digest.py` が週次で6ソースを巡回し、前回実行との差分（＝新着分）
だけを `notes/mcp_trend_digest.md` にまとめる。GitHub Actions
（`.github/workflows/mcp-trend-digest.yml`、毎週月曜 9:00 JST）が実行し、
新着があれば `mcp-digest` ラベル付きの GitHub Issue として起票する。新着が無い週は
Issueを作らない（読むもの・通知が無意味に増えないようにするため）。

状態は `notes/mcp_trend_state.json` に永続化し、コミットされる（`discover_candidates.py`
の `candidates_state.json` と同じパターン）。**初回実行時は差分の基準が無いため、
新着検出はせずベースライン保存のみ**を行う（いきなり数十〜数百件を新着として吐かないため）。

## 収集ソース（6つ）

| # | ソース | 内容 | 備考 |
|---|--------|------|------|
| 1 | GitHub topic検索 | `topic:mcp-server` / `topic:model-context-protocol` の新着リポジトリ | 未認証だと検索APIが10req/分と厳しいので `GITHUB_TOKEN` 推奨 |
| 2 | 公式org Releases | `modelcontextprotocol` 配下の主要リポジトリ（spec/servers/registry/主要SDK等）の新リリース | 監視対象は `ORG_RELEASE_REPOS` で手動キュレーション。新しい主要リポジトリが増えたら追記する |
| 3 | 公式MCPレジストリ | `registry.modelcontextprotocol.io/v0/servers` の新着サーバー | 認証不要。recency順ソートは未保証のため best-effort（先頭数百件を舐めて未見idを拾う） |
| 4 | Glama.ai | `glama.ai/api/mcp/v1/servers`（非公式API） | 公式ドキュメントが無いため仕様変更・停止のリスクあり。失敗時は静かにスキップする設計 |
| 5 | npm registry | `keywords:mcp-server` の新着パッケージ | npmの`date`は最新バージョンのpublish日であり初回公開日ではないため、「未見のパッケージ名」を新着の代理指標にしている |
| 6 | awesome-mcp-servers | `punkpeye/awesome-mcp-servers` のマージ済みPR | 人力キュレーション済みのため質の高いシグナル。似た名前の別リポジトリ（フォーク・派生）と混同しないよう owner/repo を固定で確認済み |

**PulseMCPは対象外**（2026-07時点）。旧APIは廃止予定（`v0beta` sunset）、後継APIは
APIキー登録必須のため、無料・無認証で叩ける今回のスコープに合わない。サイト本体も
bot対策で自動アクセスは403になる。

## 使い方

```bash
# 手動実行（.env に GITHUB_TOKEN があれば自動で読む）
python3 scripts/mcp_trend_digest.py

# トークンを直接渡す場合
python3 scripts/mcp_trend_digest.py --token <PAT>
```

出力:
- `notes/mcp_trend_digest.md` — 今回分の新着ダイジェスト（gitignore対象、CIがIssue本文に使う）
- `notes/mcp_trend_state.json` — 差分検出用の状態（コミット対象）
- `notes/digest_has_new.json` — CIが「Issueを作るか」を判定する一時ファイル（`{"has_new": true/false}`）

## メンテナンス

- `ORG_RELEASE_REPOS`（監視する公式org内リポジトリ）は手動リストなので、MCP仕様側で
  新しい重要リポジトリが増えたら気づいたときに追記する。
- Glama.aiは非公式APIのため、レスポンス形式が変わってエラーが増えたら
  `fetch_glama_servers()` の実装を見直す（致命的にはならず、その回は新着0件として続行する）。
- PulseMCPが将来 API キー不要の公開エンドポイントを出す、または RSS を用意したら
  ソースとして追加を検討する。
