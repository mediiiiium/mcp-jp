"""skills/<コネクタ>/SKILL.md が、実在するコネクタとツールを指しているか確かめる。

- フロントマターに name と description があり、name がディレクトリ名と一致する
- 「## ツール」節に並べたツール名が、そのコネクタの list_tools() と過不足なく一致する
- 本文中にバッククォートで書いたツールらしき名前（list_ / get_ などで始まる）が実在する
"""
import importlib
import re
from pathlib import Path

import pytest

from _discovery import CONNECTORS, run_async

ROOT = Path(__file__).resolve().parent.parent
SKILLS = sorted((ROOT / "skills").glob("*/SKILL.md"))
PACKAGES = dict(CONNECTORS)
_TOOLISH = re.compile(r"`((?:list|get|create|update|delete|set|send|record|search|post)_[a-z_]+)`")


def _tool_names(connector: str) -> set[str]:
    module = importlib.import_module(f"{PACKAGES[connector]}.server")  # nosemgrep: python.lang.security.audit.non-literal-import.non-literal-import
    return {t.name for t in run_async(module.list_tools())}


def test_skills_exist():
    assert SKILLS, "skills/*/SKILL.md が1つもない"


@pytest.mark.parametrize("path", SKILLS, ids=lambda p: p.parent.name)
def test_skill(path: Path):
    connector = path.parent.name
    assert connector in PACKAGES, f"skills/{connector}/ に対応するコネクタがない"
    text = path.read_text(encoding="utf-8")

    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, "フロントマター（--- で囲む）がない"
    front = dict(line.split(":", 1) for line in m.group(1).splitlines() if ":" in line)
    assert front.get("name", "").strip() == connector, "name がディレクトリ名と違う"
    assert front.get("description", "").strip(), "description が空"

    tools = _tool_names(connector)
    section = text.split("## ツール", 1)
    assert len(section) == 2, "「## ツール」節がない"
    listed = set(re.findall(r"`([a-z_]+)`", section[1].split("\n\n詳しい", 1)[0]))
    assert listed == tools, f"ツール一覧がコードと違う: 足りない={tools - listed} 余分={listed - tools}"

    unknown = set(_TOOLISH.findall(text)) - tools
    assert not unknown, f"存在しないツール名を書いている: {unknown}"
