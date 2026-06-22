"""エラーハンドリング基盤（_http）の検証。

(1) format_response / error_response 単体の挙動
(2) 全コネクタの call_tool が「例外を送出せず、意味のあるエラーを返す」こと
    — 未知ツール名なら通信を伴わず error_response が返るはず（今回の改修の肝）。
"""
import importlib

import httpx
import pytest

from _discovery import CONNECTORS, run_async

PARAMS = [pytest.param(pkg, id=name) for name, pkg in CONNECTORS]

# 代表として 1 コネクタの _http を読み込む（全コネクタで内容は同一）
_first_pkg = CONNECTORS[0][1] if CONNECTORS else None
_http = importlib.import_module(f"{_first_pkg}._http") if _first_pkg else None


@pytest.mark.skipif(_http is None, reason="コネクタ未発見")
def test_format_response_truncates_large_payload():
    big = {"items": [{"i": i, "text": "x" * 100} for i in range(1000)]}
    out = _http.format_response(big, max_chars=2000)
    assert len(out) == 1
    text = out[0].text
    assert "省略" in text, "切り詰めメッセージがない"
    assert len(text) < 2500, "上限を大きく超えている"


@pytest.mark.skipif(_http is None, reason="コネクタ未発見")
def test_format_response_small_payload_intact():
    out = _http.format_response({"ok": True})
    assert '"ok": true' in out[0].text
    assert "省略" not in out[0].text


@pytest.mark.skipif(_http is None, reason="コネクタ未発見")
@pytest.mark.parametrize("code,keyword", [(401, "認証"), (403, "権限"), (404, "見つかりません"), (429, "レート")])
def test_error_response_maps_status(code, keyword):
    req = httpx.Request("GET", "https://example.test/api")
    resp = httpx.Response(code, request=req, text="error body")
    err = httpx.HTTPStatusError("err", request=req, response=resp)
    out = _http.error_response(err)
    assert keyword in out[0].text
    assert out[0].text.startswith("⚠️")


@pytest.mark.parametrize("pkg", PARAMS)
def test_unknown_tool_returns_error_not_raise(pkg):
    """未知ツール呼び出しは例外を投げず error_response を返す（try/except 包囲の確認）。

    未知ツール名なので通信は発生しない。認証情報も不要。
    """
    server = importlib.import_module(f"{pkg}.server")
    result = run_async(server.call_tool("__smoke_unknown_tool__", {}))
    assert isinstance(result, list) and result, "戻り値が空 / list でない"
    assert hasattr(result[0], "text"), "TextContent が返っていない"
    # 生のスタックトレースではなく、整形済みエラーが返ること
    assert "⚠️" in result[0].text
