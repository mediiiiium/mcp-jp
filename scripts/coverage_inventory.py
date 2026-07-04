#!/usr/bin/env python3
"""
カバレッジウォッチャー: 棚卸しスクリプト

各コネクタが「今どのツールを実装しているか」を機械的に棚卸しし、
`notes/coverage_state.json` に保存する。lstep コネクタで手動検証した
「公式APIドキュメントと突き合わせて未実装ツールを見つける」動きを繰り返し
実施できるようにするための土台で、実際の深掘り（ドキュメント精査・実装）は
このスクリプトではなく `docs/agents/coverage-watcher-prompt.md` のエージェントが行う。

このスクリプトがやること:
  1. `tests/_discovery.py` と同じ規則でコネクタを発見する
     （`<dir>/src/<pkg>_mcp/server.py` を持つトップレベルディレクトリ、
     archive/tests/scripts/docs/ドットディレクトリ等は除外）。
  2. 各 `server.py` を `ast` でパースし、`types.Tool(name="...")` の
     ツール名一覧を抽出する（regex ではなく AST。コネクタパッケージの
     import はしない — `mcp` が未インストールの環境でも動かすため）。
  3. 各 `README.md` から公式APIドキュメントのURLをベストエフォートで抽出する。
  4. `notes/coverage_state.json` を更新する。既存の `last_deep_check` /
     `notes` は温存し、`tool_count` / `tools` / `docs_url` だけ最新化する
     （マージ、上書きではない）。

使い方:
  python3 scripts/coverage_inventory.py            # 棚卸しを実行して state を更新
  python3 scripts/coverage_inventory.py --stale 5  # last_deep_check が古い（or null）上位5件を表示
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = ROOT / "notes" / "coverage_state.json"

# tests/_discovery.py と同じ除外規則（コネクタではないトップレベルディレクトリ）
_SKIP = {"archive", "tests", "scripts", "docs", ".venv", ".venv-scan", ".git", ".github", ".claude"}

# README から公式APIドキュメントURLを拾うためのパターン。
# 表記ゆれが多いので複数パターンを順に試す:
#   - 独立した箇条書き行:   "- API ドキュメント: https://..."
#   - 文中の丸括弧付き:     "（公式ドキュメント: https://... ）" / "（`https://...`）"
#   - 文中のラベル直後:     "公式リファレンス: https://..."
_DOCS_LINE_PATTERNS = [
    re.compile(r"^-\s*API\s*ドキュメント\s*[:：]\s*(?P<url>https?://\S+?)\s*$", re.MULTILINE),
    re.compile(r"(?:公式)?(?:API)?\s*ドキュメント\s*[:：]\s*[`（(]*\s*(?P<url>https?://[^\s)）`]+)"),
    re.compile(r"(?:公式)?(?:API)?\s*リファレンス\s*[:：]\s*[`（(]*\s*(?P<url>https?://[^\s)）`]+)"),
]


def discover_connectors() -> list[tuple[str, str, Path]]:
    """[(connector_dir_name, package_name, server_py_path), ...] を返す。

    tests/_discovery.py の discover() と同じ探索規則（ここでは import はしない）。
    """
    found = []
    for d in sorted(ROOT.iterdir()):
        if not d.is_dir() or d.name in _SKIP or d.name.startswith("."):
            continue
        src = d / "src"
        if not src.is_dir():
            continue
        for pkg in sorted(src.iterdir()):
            server_py = pkg / "server.py"
            if pkg.is_dir() and server_py.exists():
                found.append((d.name, pkg.name, server_py))
                break
    return found


def extract_tool_names(server_py: Path) -> list[str]:
    """server.py を AST でパースし、types.Tool(name="...") のツール名一覧を返す。

    import は行わない（mcp パッケージが無い環境でも動かすため）。
    `types.Tool(...)` に限らず `Tool(...)`（`from mcp.types import Tool` 形式）
    にも対応するため、呼び出し先の関数名の末尾が "Tool" かどうかで判定する。
    """
    source = server_py.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(server_py))

    names: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        func_name = None
        if isinstance(func, ast.Attribute):
            func_name = func.attr
        elif isinstance(func, ast.Name):
            func_name = func.id
        if func_name != "Tool":
            continue
        for kw in node.keywords:
            if kw.arg == "name" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                names.append(kw.value.value)
    return names


def extract_docs_url(readme_path: Path) -> str | None:
    """README.md から公式APIドキュメントのURLをベストエフォートで抽出する。

    見つからない場合は None（呼び出し側で JSON の null に変換する）。
    """
    if not readme_path.exists():
        return None
    text = readme_path.read_text(encoding="utf-8")
    for pattern in _DOCS_LINE_PATTERNS:
        m = pattern.search(text)
        if m:
            url = m.group("url").rstrip("）)、。」』")
            return url
    return None


def load_existing_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    with open(STATE_PATH, encoding="utf-8") as f:
        return json.load(f).get("connectors", {})


def build_state() -> dict:
    """全コネクタを棚卸しし、既存の last_deep_check / notes を温存した state を返す。"""
    existing = load_existing_state()
    connectors = {}

    for dir_name, pkg_name, server_py in discover_connectors():
        tools = extract_tool_names(server_py)
        readme_path = ROOT / dir_name / "README.md"
        docs_url = extract_docs_url(readme_path)

        prev = existing.get(dir_name, {})
        connectors[dir_name] = {
            "tool_count": len(tools),
            "tools": tools,
            # README から抽出できない場合は手動設定済みの既存値を温存する
            # （深掘りエージェントが docs_url を直接記入するケースがあるため）
            "docs_url": docs_url or prev.get("docs_url"),
            "last_deep_check": prev.get("last_deep_check"),
            "notes": prev.get("notes", ""),
        }

    return {
        "generated": date.today().isoformat(),
        "connectors": connectors,
    }


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write("\n")


def print_stale(state: dict, n: int) -> None:
    """last_deep_check が古い（or null）順に上位 n 件を表示する。

    null は「一度も深掘りされていない」＝最優先で見るべき対象として最も古い扱いにする。
    """
    connectors = state["connectors"]

    def sort_key(item):
        name, rec = item
        check = rec.get("last_deep_check")
        # null を最も古い扱いにするため、日付が無ければ空文字（辞書順で最小）を使う
        return (check or "", name)

    ordered = sorted(connectors.items(), key=sort_key)
    print(f"last_deep_check が古い順 上位{n}件:")
    for name, rec in ordered[:n]:
        check = rec.get("last_deep_check") or "(未実施)"
        print(f"  - {name}: last_deep_check={check}, tool_count={rec['tool_count']}, docs_url={rec.get('docs_url')}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stale", type=int, metavar="N", default=None,
                        help="last_deep_check が古い（or未実施）上位N件を表示して終了する（state は更新される）")
    args = parser.parse_args()

    state = build_state()
    save_state(state)

    connectors = state["connectors"]
    total_tools = sum(rec["tool_count"] for rec in connectors.values())
    with_docs = sum(1 for rec in connectors.values() if rec.get("docs_url"))
    print(f"棚卸し完了: コネクタ {len(connectors)}件 / ツール合計 {total_tools}件 / docs_url検出 {with_docs}件")
    print(f"  → {STATE_PATH}")

    if args.stale is not None:
        print()
        print_stale(state, args.stale)


if __name__ == "__main__":
    main()
