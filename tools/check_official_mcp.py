#!/usr/bin/env python3
"""公式MCPの提供状況を巡回チェックするメンテナンス用スクリプト。

このリポジトリの戦略は「公式MCPが存在しないサービスだけを独自実装する」こと。
そのため README の「公式MCPが提供されているサービス」一覧が古くなると、
独自実装が公式と重複し、戦略の根拠が崩れる。

このスクリプトは README と実体ディレクトリを突き合わせ、次を検出する:

  1. 一覧の鮮度  : 最終レビュー日からの経過日数（既定 90 日超で警告）
  2. リンク死活  : --check-urls で公式MCPドキュメントURLの到達性を確認（任意・要ネットワーク）
  3. 重複の疑い  : 稼働中コネクタ名が「公式MCPあり」一覧の別名に一致したら警告
                  （= archive/ へ退避すべき候補）

CI（ネットワークなし）では 1 と 3 のみ実行される。3 のいずれかに該当すると
終了コード 1 を返す。新たに公式MCPが出たサービスを独自実装し続けないための歯止め。

使い方:
    python tools/check_official_mcp.py              # オフライン点検
    python tools/check_official_mcp.py --check-urls # リンク死活も確認
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
STATE = pathlib.Path(__file__).resolve().parent / "official_mcp_state.json"

# 鮮度しきい値（日）。これを超えたら README 一覧の手動レビューを促す。
STALE_DAYS = 90

# 稼働中コネクタが「実は公式MCPあり」になった場合の別名対応表。
# 公式MCPが出たサービスを検知したらここに追記して archive/ へ退避する。
# 形式: 稼働中コネクタのディレクトリ名 -> 一覧での表記（部分一致）
KNOWN_ALIASES: dict[str, str] = {
    # 例) "intercom": "Intercom",   ← 公式MCPが出たら有効化し archive/ へ移す
}

_SKIP_DIRS = {"archive", "docs", "tests", "notes", "scripts", "tools", ".git", ".github"}


def active_connectors() -> list[str]:
    out = []
    for d in sorted(ROOT.iterdir()):
        if not d.is_dir() or d.name in _SKIP_DIRS:
            continue
        if list(d.glob("src/*_mcp/server.py")):
            out.append(d.name)
    return out


def archived_connectors() -> list[str]:
    arc = ROOT / "archive"
    if not arc.is_dir():
        return []
    return sorted(p.name for p in arc.iterdir() if p.is_dir())


def parse_official_section() -> list[tuple[str, str]]:
    """README の「公式MCPが提供されているサービス」表からサービス名とURLを抽出する。"""
    text = README.read_text(encoding="utf-8")
    # 当該セクションを切り出す（次の見出し or 区切りまで）
    m = re.search(r"###\s*公式MCP[^\n]*\n(.*?)(?:\n---|\n##\s)", text, re.S)
    if not m:
        return []
    body = m.group(1)
    rows = []
    # | [サービス名](URL) | 公式MCP説明 |
    for line in body.splitlines():
        cell = re.match(r"\s*\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|", line)
        if cell:
            rows.append((cell.group(1).strip(), cell.group(2).strip()))
    return rows


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {}


def days_since(date_str: str) -> int | None:
    try:
        d = _dt.date.fromisoformat(date_str)
    except (ValueError, TypeError):
        return None
    return (_dt.date.today() - d).days


def check_urls(rows: list[tuple[str, str]]) -> list[str]:
    """公式MCPドキュメントURLの到達性を確認（要ネットワーク）。"""
    import urllib.error
    import urllib.request

    problems = []
    for name, url in rows:
        if not url.startswith("http"):
            continue
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "mcp-jp-link-check"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status >= 400:
                    problems.append(f"{name}: HTTP {resp.status} <{url}>")
        except urllib.error.HTTPError as e:
            if e.code in (403, 405):  # HEAD拒否はリンク切れではない
                continue
            problems.append(f"{name}: HTTP {e.code} <{url}>")
        except Exception as e:  # noqa: BLE001
            problems.append(f"{name}: 到達不可 ({e.__class__.__name__}) <{url}>")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description="公式MCP提供状況の巡回チェック")
    ap.add_argument("--check-urls", action="store_true", help="公式MCPドキュメントURLの死活も確認（要ネットワーク）")
    args = ap.parse_args()

    active = active_connectors()
    archived = archived_connectors()
    official = parse_official_section()
    state = load_state()

    print("=== mcp-jp 公式MCP巡回チェック ===")
    print(f"稼働コネクタ: {len(active)} / archive: {len(archived)} / 一覧の公式MCP: {len(official)} 件\n")

    exit_code = 0

    # 1. 鮮度
    reviewed = state.get("official_list_reviewed")
    elapsed = days_since(reviewed) if reviewed else None
    if elapsed is None:
        print(f"[鮮度] 最終レビュー日が未記録。{STATE.name} に "
              f'\'{{"official_list_reviewed": "YYYY-MM-DD"}}\' を記録してください。')
    elif elapsed > STALE_DAYS:
        print(f"[鮮度] ⚠️ 公式MCP一覧の最終レビューから {elapsed} 日経過（しきい値 {STALE_DAYS} 日）。"
              "新規の公式MCPが出ていないか手動で確認を。")
    else:
        print(f"[鮮度] OK（最終レビューから {elapsed} 日）")

    # 3. 重複の疑い（オフラインで実行可能・ゲート）
    dup = []
    official_names_lower = [n.lower() for n, _ in official]
    for conn in active:
        alias = KNOWN_ALIASES.get(conn)
        if alias and any(alias.lower() in on for on in official_names_lower):
            dup.append(f"{conn} → 一覧の「{alias}」と重複（公式MCPあり）。archive/ へ退避を。")
    if dup:
        exit_code = 1
        print("\n[重複] ⚠️ 稼働中コネクタが公式MCP提供済みサービスと重複:")
        for d in dup:
            print(f"  - {d}")
    else:
        print("[重複] OK（稼働コネクタと公式MCP一覧の既知の重複なし）")

    # 2. リンク死活（任意）
    if args.check_urls:
        print("\n[リンク] 公式MCPドキュメントURLの死活確認中...")
        problems = check_urls(official)
        if problems:
            print("[リンク] ⚠️ 要確認:")
            for p in problems:
                print(f"  - {p}")
        else:
            print("[リンク] OK（全URL到達）")
    else:
        print("\n[リンク] スキップ（--check-urls で有効化）")

    print()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
