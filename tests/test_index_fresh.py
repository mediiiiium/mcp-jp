"""README の `## Tools` 節・connectors.json・llms.txt が、コードから生成した内容と一致するか確かめる。

ツールを足したり説明を変えたりしたのに再生成し忘れると、ここで落ちる。
直し方: python scripts/build_index.py を実行してコミットする。
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_generated_index_is_fresh():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_index.py"), "--check"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode == 0, result.stdout + result.stderr
