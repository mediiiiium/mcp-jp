"""全コネクタの構造を検証する（ネットワーク・認証情報不要）。

list_tools のスキーマ妥当性・ツール名の一意性・エントリポイント・共通ヘルパーの存在を確認する。
新しいコネクタを追加すると自動的にこのテスト対象になる。
"""
import importlib

import pytest

from _discovery import CONNECTORS, run_async

# (connector_name, package_name) を id 付きでパラメータ化
PARAMS = [pytest.param(pkg, id=name) for name, pkg in CONNECTORS]


def test_connectors_discovered():
    assert CONNECTORS, "コネクタが 1 つも発見できなかった（パス構成を確認）"


@pytest.fixture(params=PARAMS)
def server_module(request):
    # request.param は _discovery.discover() がリポジトリ内のディレクトリを走査して
    # 生成した固定リスト由来で、外部・実行時入力は混入しない。
    return importlib.import_module(f"{request.param}.server")  # nosemgrep: python.lang.security.audit.non-literal-import.non-literal-import


def test_imports(server_module):
    """server モジュールが import できる。"""
    assert server_module is not None


def test_has_entrypoint(server_module):
    """`main` エントリポイントが存在する（pyproject の scripts と対応）。"""
    assert hasattr(server_module, "main"), "main() が定義されていない"


def test_uses_shared_http_helper(server_module):
    """共通ヘルパー format_response / error_response を取り込んでいる。"""
    assert hasattr(server_module, "format_response"), "_http.format_response を import していない"
    assert hasattr(server_module, "error_response"), "_http.error_response を import していない"


def test_list_tools_schema(server_module):
    """list_tools が妥当なツール定義を返す。"""
    tools = run_async(server_module.list_tools())
    assert tools, "ツールが空"
    names = []
    for t in tools:
        assert t.name, "ツール名が空"
        assert t.description, f"{t.name}: description が空"
        schema = t.inputSchema
        assert isinstance(schema, dict), f"{t.name}: inputSchema が dict でない"
        assert schema.get("type") == "object", f"{t.name}: inputSchema.type が object でない"
        assert "properties" in schema, f"{t.name}: properties がない"
        names.append(t.name)
    assert len(names) == len(set(names)), f"ツール名が重複: {names}"
