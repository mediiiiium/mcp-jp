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
