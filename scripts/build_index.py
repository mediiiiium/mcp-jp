"""コネクタのコードからツール一覧を集め、機械が読める索引を生成する。

生成物:
  - README.md の `## Tools` 節（<!-- tools:start --> と <!-- tools:end --> の間）
  - connectors.json（コネクタ・カテゴリ・インストール方法・環境変数・ツール一覧）
  - llms.txt（AI チャット／エージェント向けの入口）

ツール一覧は各コネクタの list_tools() から取るので、手で書いた表とずれない。
コネクタのサービス名・カテゴリ・動作確認の状況は README の「コネクタ一覧」の表から読む。

使い方:
  python scripts/build_index.py          # 生成して書き出す
  python scripts/build_index.py --check  # 生成物が最新かだけを確かめる（CI 用、差分があれば終了コード 1）
"""
from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))

from _discovery import CONNECTORS, run_async  # noqa: E402

REPO = "mediiiiium/mcp-jp"
REPO_URL = f"https://github.com/{REPO}"
README = ROOT / "README.md"
CONNECTORS_JSON = ROOT / "connectors.json"
LLMS_TXT = ROOT / "llms.txt"
START = "<!-- tools:start -->"
END = "<!-- tools:end -->"

# README のコネクタ表の1行: | [`smarthr/`](./smarthr/) | [SmartHR](https://smarthr.jp/) | 人事・労務 | 未確認 |
_ROW = re.compile(
    r"^\|\s*\[`(?P<dir>[\w-]+)/`\]\(\./[\w-]+/\)\s*\|\s*\[(?P<service>[^\]]+)\]\((?P<url>[^)]+)\)\s*"
    r"\|\s*(?P<category>[^|]+?)\s*\|\s*(?P<status>[^|]+?)\s*\|\s*$"
)
_REGION_HEADINGS = {"### 日本SMB向け（独自実装）": "jp", "### グローバルSaaS（独自実装）": "global"}
_ENV = re.compile(r"""os\.(?:environ\.get|getenv)\(\s*["']([A-Z0-9_]+)["']|os\.environ\[\s*["']([A-Z0-9_]+)["']\s*\]""")


def readme_rows(text: str) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    region = None
    for line in text.splitlines():
        if line.startswith("### "):
            region = _REGION_HEADINGS.get(line.strip())
            continue
        m = _ROW.match(line)
        if m and region:
            rows[m["dir"]] = {**m.groupdict(), "region": region}
    return rows


def summary(description: str, limit: int = 90) -> str:
    """description の1文目を、表に載る長さに切る。"""
    text = re.sub(r"\s+", " ", description.strip())
    depth = 0
    first = text
    for i, ch in enumerate(text):
        if ch in "（(「":
            depth += 1
        elif ch in "）)」":
            depth = max(depth - 1, 0)
        elif ch == "。" and depth == 0:
            first = text[:i]
            break
    first = first.strip()
    return first if len(first) <= limit else first[: limit - 1] + "…"


def env_vars(connector_dir: str, package: str) -> list[str]:
    src = (ROOT / connector_dir / "src" / package / "server.py").read_text(encoding="utf-8")
    seen: list[str] = []
    for a, b in _ENV.findall(src):
        name = a or b
        if name not in seen:
            seen.append(name)
    return seen


def entrypoint(connector_dir: str) -> str:
    pyproject = (ROOT / connector_dir / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r"^\[project\.scripts\]\s*\n\s*([\w-]+)\s*=", pyproject, re.M)
    if not m:
        raise SystemExit(f"{connector_dir}/pyproject.toml に [project.scripts] がない")
    return m.group(1)


def collect() -> list[dict]:
    rows = readme_rows(README.read_text(encoding="utf-8"))
    out = []
    for name, package in CONNECTORS:
        row = rows.get(name)
        if row is None:
            raise SystemExit(f"README のコネクタ一覧に {name}/ の行がない（表に足してから再実行）")
        module = importlib.import_module(f"{package}.server")  # nosemgrep: python.lang.security.audit.non-literal-import.non-literal-import
        tools = run_async(module.list_tools())
        command = entrypoint(name)
        out.append(
            {
                "name": name,
                "service": row["service"],
                "service_url": row["url"],
                "category": row["category"],
                "region": row["region"],
                "verification": row["status"],
                "path": f"{name}/",
                "readme": f"{REPO_URL}/blob/main/{name}/README.md",
                "skill": (
                    f"{REPO_URL}/blob/main/skills/{name}/SKILL.md"
                    if (ROOT / "skills" / name / "SKILL.md").exists()
                    else None
                ),
                "command": command,
                "install": f'pip install "git+{REPO_URL}#subdirectory={name}"',
                "env": env_vars(name, package),
                "tools": [
                    {"name": t.name, "summary": summary(t.description)}
                    for t in tools
                ],
            }
        )
    return out


def render_tools_section(connectors: list[dict]) -> str:
    total = sum(len(c["tools"]) for c in connectors)
    lines = [
        START,
        "## Tools",
        "",
        f"{len(connectors)} コネクタ・{total} ツール。各コネクタのコード（`list_tools()`）から "
        "[`scripts/build_index.py`](./scripts/build_index.py) で生成しています（手で編集しないでください）。",
        f"同じ内容を機械可読の [`connectors.json`](./connectors.json) と [`llms.txt`](./llms.txt) にも出しています。",
        "",
    ]
    for c in connectors:
        lines.append(f"### {c['name']} — {c['service']}（{c['category']}）")
        lines.append("")
        for t in c["tools"]:
            lines.append(f"- `{t['name']}` — {t['summary']}")
        lines.append("")
    lines.append(END)
    return "\n".join(lines)


def render_readme(text: str, section: str) -> str:
    if START in text and END in text:
        before, rest = text.split(START, 1)
        _, after = rest.split(END, 1)
        return before + section + after
    # 初回: 「公式MCPが提供されているサービス」の節の後ろ、最初の「## セットアップ」の前に入れる
    anchor = "## セットアップ"
    if anchor not in text:
        raise SystemExit("README に「## セットアップ」見出しがない")
    head, tail = text.split(anchor, 1)
    return head + section + "\n\n---\n\n" + anchor + tail


def render_json(connectors: list[dict]) -> str:
    doc = {
        "name": "mcp-jp",
        "description": "日本の SMB 向け SaaS に対応した MCP サーバー集（公式 MCP がないサービスへの独自実装）",
        "repository": REPO_URL,
        "license": "MIT",
        "transport": "stdio",
        "runtime": "python>=3.10",
        "generated_by": "scripts/build_index.py",
        "connectors": connectors,
    }
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


def render_llms(connectors: list[dict]) -> str:
    total = sum(len(c["tools"]) for c in connectors)
    lines = [
        "# mcp-jp",
        "",
        "> 日本の SMB 向け SaaS（SmartHR、KING OF TIME、スマレジ、クラウドサインなど）を、"
        "Claude などの AI エージェントから操作するための MCP サーバー集。"
        f"公式 MCP がないサービスだけを独自実装している（{len(connectors)} コネクタ・{total} ツール、Python、stdio、MIT）。",
        "",
        "各コネクタは独立したパッケージで、使いたいものだけを入れる。"
        "インストールは `pip install \"git+https://github.com/mediiiiium/mcp-jp#subdirectory=<コネクタ名>\"`、"
        "起動コマンドは `<コネクタ名>-mcp`、認証情報は環境変数で渡す。"
        "公式 MCP が出たサービスのコネクタは archive/ に移している（README の「公式MCPが提供されているサービス」の表を参照）。",
        "",
        "## Docs",
        "",
        f"- [README]({REPO_URL}/blob/main/README.md): 全体の説明・コネクタ一覧・ツール一覧・セットアップ",
        f"- [connectors.json]({REPO_URL}/blob/main/connectors.json): コネクタごとのインストール方法・環境変数・ツール一覧（機械可読）",
        "",
        "## Skills",
        "",
        "主力コネクタには、準備・進め方・書き込み時の注意をまとめた SKILL.md（Claude のスキル）がある。MCP サーバーと組み合わせて使う。",
        "",
    ]
    for c in connectors:
        if c["skill"]:
            lines.append(f"- [{c['service']}]({c['skill']}): 準備・進め方・書き込み時の注意")
    lines += [
        "",
        "## Connectors",
        "",
    ]
    for c in connectors:
        env = "、".join(f"`{e}`" for e in c["env"]) or "なし"
        tools = ", ".join(t["name"] for t in c["tools"])
        lines.append(
            f"- [{c['service']}]({c['readme']}): {c['category']}。コマンド `{c['command']}`、環境変数 {env}。"
            f"ツール: {tools}"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="生成物が最新かを確かめるだけ（書き出さない）")
    args = parser.parse_args()

    connectors = collect()
    readme_text = README.read_text(encoding="utf-8")
    targets = {
        README: render_readme(readme_text, render_tools_section(connectors)),
        CONNECTORS_JSON: render_json(connectors),
        LLMS_TXT: render_llms(connectors),
    }

    stale = [p for p, body in targets.items() if not p.exists() or p.read_text(encoding="utf-8") != body]
    if args.check:
        for p in stale:
            print(f"古い: {p.relative_to(ROOT)}（python scripts/build_index.py で再生成）")
        return 1 if stale else 0
    for p in stale:
        p.write_text(targets[p], encoding="utf-8")
        print(f"更新: {p.relative_to(ROOT)}")
    if not stale:
        print("変更なし")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
