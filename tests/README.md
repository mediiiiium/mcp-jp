# tests

全コネクタ共通のスモークテスト。コネクタを追加すると自動的に対象になる（個別の登録は不要）。

## 何を検証するか

| ファイル | 内容 | ネットワーク |
|---|---|---|
| `test_structure.py` | import 可否・`list_tools` のスキーマ妥当性・ツール名の一意性・`main` の存在・共通ヘルパーの取り込み | 不要 |
| `test_error_handling.py` | `_http` の整形/エラー変換、`call_tool` が例外を投げず `error_response` を返すこと | 不要 |
| `test_live_smoke.py` | 実 API への読み取り疎通（**既定でスキップ**） | 必要（オプトイン） |

`test_structure.py` / `test_error_handling.py` は**認証情報もネットワークも不要**で、CI で常時実行する。

## 実行

```bash
# 依存をインストール（初回のみ）
.venv/bin/pip install -r requirements-dev.txt

# 全テスト（ネットワーク不要のものだけ走る）
.venv/bin/pytest

# 実 API 疎通も含める（認証情報が必要・読み取り専用ツールのみ）
RUN_LIVE_SMOKE=1 PAYJP_SECRET_KEY=sk_test_xxx .venv/bin/pytest tests/test_live_smoke.py -v
```

## 新しいコネクタを追加したら

- `test_structure.py` / `test_error_handling.py` は**自動で対象に含まれる**（`_discovery.py` が `src/<pkg>_mcp/server.py` を探索）。
- ライブ疎通も確かめたい場合は `test_live_smoke.py` の `LIVE_CASES` に
  `(パッケージ名, 必要な環境変数, 読み取り専用ツール, 引数)` を 1 行追加する。
