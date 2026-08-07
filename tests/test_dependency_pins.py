"""mcp SDK のバージョン上限が外れていないことを検査する。

2026-08-07、mcp 2.0.0 が低レベル Server の `@app.list_tools()` /
`@app.call_tool()` デコレータを廃止した（ツール登録は `MCPServer.tool()` に移行）。
このリポジトリのコネクタは全て旧 API で書かれているため、`mcp>=1.0.0` のまま
新しい環境で pip install すると 2.x が入り、40 本超が一斉に
`AttributeError: 'Server' object has no attribute 'list_tools'` で import 不能になる。
既存の venv は 1.x が残るので気づけない。壊れるのは「初めて使う人」の環境だけ。

コネクタを追加するときは pyproject.toml をコピーして作るので、上限を外した記述が
そのまま増えていく。ここで機械的に止める。

上限を外していいのは、全コネクタを `MCPServer` に移植し終えたとき。
そのときはこのテストごと書き換える。
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# 依存に mcp を書いているファイル（archive も対象。あそこも pip install され得る）
FILES = sorted(ROOT.glob("*/pyproject.toml")) + sorted(ROOT.glob("archive/*/pyproject.toml")) + [
    ROOT / "requirements-dev.txt"
]

# 行中の mcp 要件を拾う。`"mcp>=1.0.0,<2",` / `mcp>=1.0.0,<2` の両方に当たる
MCP_REQ = re.compile(r'\bmcp\s*(?P<spec>(?:[<>=!~]=?\s*[0-9][^,"\s]*\s*,?\s*)+)')


def _mcp_specs(path: Path) -> list[str]:
    specs = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("#"):
            continue
        m = MCP_REQ.search(line)
        if m:
            specs.append(m.group("spec").strip().rstrip(","))
    return specs


@pytest.mark.parametrize("path", FILES, ids=[str(p.relative_to(ROOT)) for p in FILES])
def test_mcp_has_upper_bound(path):
    """mcp の依存指定に 2.x を弾く上限がある。"""
    specs = _mcp_specs(path)
    assert specs, f"{path.relative_to(ROOT)}: mcp の依存指定が見つからない"
    for spec in specs:
        assert "<2" in spec.replace(" ", ""), (
            f"{path.relative_to(ROOT)}: mcp の上限がない（{spec!r}）。"
            "2.x はコネクタが使っている低レベル Server のデコレータ API を廃止したので、"
            "`mcp>=1.0.0,<2` と書く。"
        )


def test_installed_mcp_is_v1():
    """実際に入っている mcp が 1.x である（テストの前提を満たしている）。"""
    from importlib.metadata import version

    major = int(version("mcp").split(".")[0])
    assert major == 1, (
        f"mcp {version('mcp')} が入っている。2.x ではコネクタが import できない。"
        "`pip install -r requirements-dev.txt` で入れ直すこと。"
    )
