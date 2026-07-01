# tools/

リポジトリのメンテナンス用スクリプト（公開対象）。

> 個人作業用の使い捨てスクリプトは `scripts/`（gitignore 済み）に置く。
> 公開・CI で回すものだけをここに置く。

## check_official_mcp.py

公式MCPの提供状況を巡回チェックする。このリポジトリは「公式MCPが存在しない
サービスだけを独自実装する」方針のため、README の公式MCP一覧が古くなると
独自実装が公式と重複してしまう。それを防ぐための歯止め。

```bash
python tools/check_official_mcp.py              # オフライン点検（鮮度・重複ゲート）
python tools/check_official_mcp.py --check-urls # 公式MCPドキュメントURLの死活も確認
```

- **鮮度**: `official_mcp_state.json` の `official_list_reviewed` からの経過日数。
  90 日超で警告。README 一覧を手動レビューしたら日付を更新する。
- **重複ゲート**: 稼働中コネクタが公式MCP提供済みサービスに該当したら exit 1。
  新たに公式MCPが出たサービスを見つけたら、スクリプト内 `KNOWN_ALIASES` に追記し、
  該当コネクタを `archive/` へ退避する。
- **リンク死活**: `--check-urls` で公式MCPドキュメントURLの到達性を確認（要ネットワーク）。

オフライン点検は `tests/test_official_mcp_check.py` 経由で CI でも自動実行される。

### レビュー運用

1. 四半期に一度、`--check-urls` 付きで実行する。
2. 新規に公式MCPが提供されたサービスを README の一覧へ追記する。
3. 該当する稼働コネクタがあれば `archive/` へ退避し、`KNOWN_ALIASES` に登録する。
4. `official_mcp_state.json` の `official_list_reviewed` を当日に更新する。

## check_api_sunset.py

各コネクタが依存する SaaS API のバージョン廃止（sunset）を巡回チェックする。
pipedrive で「API v1 が2025-12-31で動作保証終了」に気づかず据え置いていた事故を
機に作成（後に v2 へ移行済み）。SaaS 側は個別に通知してくれないため、
気づかないまま本番で動かなくなるリスクがある。33サービスの変更ログ構造はバラバラで
自動スクレイピングは非現実的なため、全自動検出ではなく「定期的に手動で変更ログを
確認する」ことを仕組みとして強制する棚卸しリマインダー + 判明済み sunset 日付の
ゲートとして機能する。

```bash
python tools/check_api_sunset.py
```

- **鮮度**: `api_sunset_state.json` の各コネクタ `last_reviewed` からの経過日数。
  120 日超で警告（ゲートではない）。
- **記録漏れゲート**: 稼働中コネクタが `api_sunset_state.json` に未登録なら exit 1。
  新規コネクタ追加時は `api_version`・`last_reviewed`・`sunset_date`（null可）を追記する。
- **廃止超過ゲート**: `sunset_date` が過去日付のまま残っていたら exit 1（= 移行忘れ）。

オフライン点検は `tests/test_api_sunset_check.py` 経由で CI でも自動実行される。

### レビュー運用

1. 半年に一度程度、`api_sunset_state.json` に載っている各コネクタの使用中APIバージョンの
   変更ログ・非推奨告知を手動確認する（WebSearch等でサービス名 + "API deprecat" 等）。
2. 廃止予告を見つけたら `sunset_date` に日付を記録し、移行タスクを起票する。
3. 確認したコネクタの `last_reviewed` を当日に更新する。
4. 実際に移行したら `api_version` を更新し、`sunset_date` を null に戻す。
