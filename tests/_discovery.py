"""全コネクタを動的に発見し、import 可能にする共通ヘルパー。

各コネクタは独立パッケージ（`<dir>/src/<pkg>_mcp/`）で、pip install されていない前提。
ここで各 `src` を sys.path に通し、`<pkg>_mcp.server` を import できるようにする。
"""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# コネクタではないトップレベルディレクトリ
_SKIP = {"archive", "tests", "scripts", "docs", ".venv", ".venv-scan", ".git", ".github", ".claude"}


def discover():
    """[(connector_name, package_name), ...] を返す。archive は除外。"""
    connectors = []
    for d in sorted(ROOT.iterdir()):
        if not d.is_dir() or d.name in _SKIP or d.name.startswith("."):
            continue
        src = d / "src"
        if not src.is_dir():
            continue
        for pkg in sorted(src.iterdir()):
            if pkg.is_dir() and (pkg / "server.py").exists():
                if str(src) not in sys.path:
                    sys.path.insert(0, str(src))
                connectors.append((d.name, pkg.name))
                break
    return connectors


def run_async(coro):
    """同期テストから async 関数を実行する小ヘルパー。"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# import 時点で sys.path を整えておく
CONNECTORS = discover()
