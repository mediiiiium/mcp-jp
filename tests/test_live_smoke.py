"""実 API への疎通スモークテスト（既定でスキップ・オプトイン）。

認証情報を環境変数に設定し、`RUN_LIVE_SMOKE=1` のときだけ実行する。
読み取り専用ツールのみを叩き、エラー（⚠️）が返らないことを確認する。
CI では実行しない。ローカルでコネクタが本当に動くかを確かめる用途。

実行例:
    RUN_LIVE_SMOKE=1 PAYJP_SECRET_KEY=sk_test_xxx \
        .venv/bin/pytest tests/test_live_smoke.py -v

新しいコネクタを追加したら、下の LIVE_CASES に
(コネクタ名, 必要な環境変数, 読み取り専用ツール名, 引数) を 1 行足す。
"""
import importlib
import os

import pytest

from _discovery import run_async

RUN = os.environ.get("RUN_LIVE_SMOKE") == "1"

# (package, [必要env...], 読み取り専用ツール, 引数)
LIVE_CASES = [
    ("payjp_mcp", ["PAYJP_SECRET_KEY"], "list_charges", {"limit": 1}),
    ("smarthr_mcp", ["SMARTHR_ACCESS_TOKEN", "SMARTHR_TENANT_ID"], "list_crews", {"per_page": 1}),
    # TODO: 他コネクタの読み取り専用ツールを追加していく
]


@pytest.mark.skipif(not RUN, reason="RUN_LIVE_SMOKE=1 のときのみ実行")
@pytest.mark.parametrize("pkg,envs,tool,args", LIVE_CASES, ids=[c[0] for c in LIVE_CASES])
def test_live_read_only(pkg, envs, tool, args):
    missing = [e for e in envs if not os.environ.get(e)]
    if missing:
        pytest.skip(f"環境変数未設定: {missing}")
    server = importlib.import_module(f"{pkg}.server")
    result = run_async(server.call_tool(tool, args))
    text = result[0].text
    assert "⚠️" not in text, f"{pkg}.{tool} がエラーを返した:\n{text}"
