"""カバレッジウォッチャー（scripts/coverage_inventory.py）の棚卸しロジックを検証する。

`scripts/` は import パスに含まれていないので、モジュールをパス指定で読み込む。
実際に AST 抽出した結果が現実（_discovery.py が発見するコネクタ・server.py の中身）と
一致しているかを見るのが目的で、ネットワークアクセスや mcp パッケージの import は行わない。
"""
import importlib.util
import sys
from pathlib import Path

import pytest

from _discovery import CONNECTORS, ROOT

SCRIPT_PATH = ROOT / "scripts" / "coverage_inventory.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("coverage_inventory", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def inventory():
    return _load_module()


def test_discovers_same_connectors_as_test_discovery(inventory):
    """coverage_inventory の発見規則が tests/_discovery.py と一致する。"""
    found = inventory.discover_connectors()
    found_names = sorted(name for name, _pkg, _path in found)
    expected_names = sorted(name for name, _pkg in CONNECTORS)
    assert found_names == expected_names


# (connector_name, package_name) を id 付きでパラメータ化
PARAMS = [pytest.param(name, pkg, id=name) for name, pkg in CONNECTORS]


@pytest.mark.parametrize("connector_name,package_name", PARAMS)
def test_extracts_at_least_one_tool(inventory, connector_name, package_name):
    """各コネクタから最低1つはツール名を抽出できる。"""
    server_py = ROOT / connector_name / "src" / package_name / "server.py"
    tools = inventory.extract_tool_names(server_py)
    assert tools, f"{connector_name}: ツールが1つも抽出できなかった"


@pytest.mark.parametrize("connector_name,package_name", PARAMS)
def test_tool_names_are_unique(inventory, connector_name, package_name):
    """抽出したツール名に重複がない（list_tools の一意性と対応するはず）。"""
    server_py = ROOT / connector_name / "src" / package_name / "server.py"
    tools = inventory.extract_tool_names(server_py)
    assert len(tools) == len(set(tools)), f"{connector_name}: ツール名が重複: {tools}"


def test_lstep_tools_include_recently_added_ones(inventory):
    """lstep は本日(2026-07-03)深掘りされ list_templates/upload_media が追加された。
    棚卸しがこの2つを含む list_friends 等の全体を正しく拾えているかを確認する。
    """
    server_py = ROOT / "lstep" / "src" / "lstep_mcp" / "server.py"
    tools = inventory.extract_tool_names(server_py)
    assert "list_friends" in tools
    assert "list_templates" in tools


def test_extract_docs_url_handles_known_conventions(inventory, tmp_path):
    """README の docs_url 抽出が主要な表記ゆれに耐える。"""
    cases = [
        ("- API ドキュメント: https://docs.lineml.jp/\n", "https://docs.lineml.jp/"),
        ("BASE API（公式ドキュメント: https://docs.thebase.in/api/ ）を調査した。\n",
         "https://docs.thebase.in/api/"),
        ("Jooto API（公式リファレンス: https://www.jooto.com/api/reference/request/）には\n",
         "https://www.jooto.com/api/reference/request/"),
        ("特に記載なしのREADME\n", None),
    ]
    for i, (content, expected) in enumerate(cases):
        readme = tmp_path / f"README_{i}.md"
        readme.write_text(content, encoding="utf-8")
        assert inventory.extract_docs_url(readme) == expected


def test_build_state_preserves_existing_last_deep_check_and_notes(inventory, monkeypatch, tmp_path):
    """再実行時に既存の last_deep_check / notes を上書きしないことを確認する（マージ）。"""
    fake_state_path = tmp_path / "coverage_state.json"
    monkeypatch.setattr(inventory, "STATE_PATH", fake_state_path)

    import json
    fake_state_path.write_text(json.dumps({
        "generated": "2026-01-01",
        "connectors": {
            "lstep": {
                "tool_count": 999,
                "tools": ["dummy"],
                "docs_url": "https://old.example/",
                "last_deep_check": "2026-07-03",
                "notes": "手動で書いたメモ",
            }
        },
    }), encoding="utf-8")

    state = inventory.build_state()
    lstep_rec = state["connectors"]["lstep"]
    # last_deep_check / notes は温存される
    assert lstep_rec["last_deep_check"] == "2026-07-03"
    assert lstep_rec["notes"] == "手動で書いたメモ"
    # tool_count / tools / docs_url は最新化される（古いダミー値ではない）
    assert lstep_rec["tools"] != ["dummy"]
    assert lstep_rec["tool_count"] == len(lstep_rec["tools"])
