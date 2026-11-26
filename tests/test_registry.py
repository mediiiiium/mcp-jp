"""公式 MCP Registry 用の <コネクタ>/server.json が、コネクタの実体と食い違っていないか確かめる。

- name が io.github.mediiiiium/<コネクタ> で、Dockerfile の LABEL と一致する（Registry の所有権確認に使われる）
- version が pyproject.toml の version と一致し、イメージのタグにも同じ version が付いている
- environmentVariables がコードの読んでいる環境変数と過不足なく一致する
- description が Registry の上限（100文字）以内
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SERVER_JSONS = sorted(p for p in ROOT.glob("*/server.json") if p.parent.name != "archive")
_ENV = re.compile(r"""os\.(?:environ\.get|getenv)\(\s*["']([A-Z0-9_]+)["']|os\.environ\[\s*["']([A-Z0-9_]+)["']\s*\]""")


def test_server_jsons_exist():
    assert SERVER_JSONS, "*/server.json が1つもない"


@pytest.mark.parametrize("path", SERVER_JSONS, ids=lambda p: p.parent.name)
def test_server_json(path: Path):
    connector = path.parent.name
    doc = json.loads(path.read_text(encoding="utf-8"))

    assert doc["name"] == f"io.github.mediiiiium/{connector}"
    assert 1 <= len(doc["description"]) <= 100, "description は 1〜100 文字"
    assert doc["repository"] == {
        "url": "https://github.com/mediiiiium/mcp-jp",
        "source": "github",
        "subfolder": connector,
    }

    dockerfile = (path.parent / "Dockerfile").read_text(encoding="utf-8")
    m = re.search(r'^LABEL io\.modelcontextprotocol\.server\.name="([^"]+)"$', dockerfile, re.M)
    assert m and m.group(1) == doc["name"], "Dockerfile の LABEL と name が違う"

    pyproject = (path.parent / "pyproject.toml").read_text(encoding="utf-8")
    version = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.M).group(1)
    assert doc["version"] == version, "server.json と pyproject.toml の version が違う"

    (package,) = doc["packages"]
    assert package["registryType"] == "oci"
    assert package["identifier"] == f"ghcr.io/mediiiiium/{connector}-mcp:{version}"
    assert package["transport"] == {"type": "stdio"}

    server_py = next((path.parent / "src").glob("*/server.py")).read_text(encoding="utf-8")
    used = {a or b for a, b in _ENV.findall(server_py)}
    declared = {e["name"] for e in package.get("environmentVariables", [])}
    assert declared == used, f"環境変数がコードと違う: 足りない={used - declared} 余分={declared - used}"
