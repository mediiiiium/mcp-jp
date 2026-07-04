# カバレッジウォッチャー

各コネクタが実装しているツールと、公式APIドキュメントが実際に提供している機能との
差分を定期的に確認し、証拠（ドキュメントの記載）に基づいてツールを追加していくための
仕組み。`scripts/discover_candidates.py`（新規コネクタ候補の発掘）や
`scripts/mcp_trend_digest.py`（MCPエコシステム全体の動向把握）とは異なり、
こちらは**既存コネクタの深掘り**が対象。

## 背景

lstep コネクタで、この動きを手動で1回実施した（2026-07-03）。
公式ドキュメント（docs.lineml.jp）を精査した結果、`list_templates` /
`upload_media` の2ツールを実際に追加した一方、候補に挙がっていた
`get_friend`（友だち単体取得）は**ドキュメント上に実在が確認できなかったため
実装を見送った**。この「作れそうでも、確認できないものは作らない」を
再現性のある手順にしたのがこのウォッチャー。

## 仕組み

1. `scripts/coverage_inventory.py` が全コネクタの `server.py` を AST でパースし、
   実装済みツール名一覧・件数・README から検出したAPIドキュメントURLを
   `notes/coverage_state.json` に棚卸しする。
2. 棚卸し結果から「長らく深掘りされていないコネクタ」を選び、
   `docs/agents/coverage-watcher-prompt.md` のテンプレートでエージェントに
   深掘りを依頼する。
3. エージェントは公式ドキュメントを実際に読み、証拠のある差分だけを実装する。
   実装してもしなくても、`notes/coverage_state.json` の `last_deep_check` /
   `notes` を更新して締める。

## 棚卸しの実行

```bash
# 全コネクタを棚卸しし、notes/coverage_state.json を更新する
.venv/bin/python3 scripts/coverage_inventory.py

# ついでに last_deep_check が古い（または未実施）上位5件を見る
.venv/bin/python3 scripts/coverage_inventory.py --stale 5
```

`notes/coverage_state.json` の各コネクタのレコードは以下の形:

```json
{
  "tool_count": 21,
  "tools": ["list_friends", "..."],
  "docs_url": "https://docs.lineml.jp/",
  "last_deep_check": "2026-07-03",
  "notes": "list_templates/upload_media 追加。get_friend は実在確認できず見送り。"
}
```

`docs_url` が `null` のコネクタは、README がまだ「API ドキュメント: https://...」
のような検出可能な形式でURLを記載していない（記載自体が無い場合を含む）。
深掘りエージェントが自力で公式サイトを探すか、見つけたらREADMEにも追記するとよい。

`tool_count` / `tools` / `docs_url` は再実行のたびに最新化されるが、
`last_deep_check` / `notes` は**再実行しても上書きされない**（深掘りエージェントが
明示的に更新するまで温存される）。

## 深掘りエージェントの起動

`docs/agents/coverage-watcher-prompt.md` の `{connector}` を対象コネクタ名に
置き換えて、そのままエージェントに渡す。エージェントは公式ドキュメントを実際に
フェッチして検証するため、ネットワークアクセスが必要。

## 運用の目安

- **四半期ごと**: 全コネクタで `coverage_inventory.py` を実行し、
  `--stale` で優先度を確認。棚卸し自体は数秒で終わる。
- **月次程度**: `--stale` の上位から2〜3コネクタを選び、深掘りエージェントを
  起動する。34コネクタ全部を毎回深掘りする必要はない
  （`docs/strategy.md` の「本数より質」の方針と一致させる）。
- 深掘りの結果、実装追加が無かった場合でも `last_deep_check` は更新する
  （「確認した上で今回は追加なしだった」という事実自体が価値のある記録）。

## 関連ファイル

- `scripts/coverage_inventory.py` — 棚卸し本体。
- `notes/coverage_state.json` — 棚卸し結果（コミット対象）。
- `docs/agents/coverage-watcher-prompt.md` — 深掘りエージェント用プロンプトテンプレート。
- `tests/test_coverage_inventory.py` — 棚卸しロジックのテスト。
