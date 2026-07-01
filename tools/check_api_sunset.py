#!/usr/bin/env python3
"""各コネクタが依存する SaaS API のバージョン廃止（sunset）を巡回チェックするメンテナンス用スクリプト。

pipedrive で「API v1 が2025-12-31で動作保証終了」に気づかず据え置いていた事故を機に作成。
SaaS 側は個別に通知してくれないため、気づかないまま本番で動かなくなるリスクがある。
本スクリプトは全自動でAPIの廃止予定を検出するものではなく（33サービスの変更ログ構造は
バラバラで自動スクレイピングは非現実的）、「定期的に手動で変更ログを確認する」ことを
仕組みとして強制するための棚卸しリマインダー + 判明済みの sunset 日付が過ぎていないかの
ゲートである。

このスクリプトは `api_sunset_state.json`（各コネクタの api_version・last_reviewed・
sunset_date）と実体ディレクトリを突き合わせ、次を検出する:

  1. 鮮度      : last_reviewed からの経過日数（既定 120 日超で警告）
  2. 記録漏れ  : 稼働中コネクタが state ファイルに未登録（新規コネクタ追加時の登録漏れ）
  3. 廃止超過  : sunset_date が過去日付なのに残っている（= 移行忘れ。pipedrive の再発防止）

CI（ネットワークなし）で 1〜3 すべて実行される。2・3 のいずれかに該当すると終了コード 1。

使い方:
    python tools/check_api_sunset.py
"""
from __future__ import annotations

import datetime as _dt
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
STATE = pathlib.Path(__file__).resolve().parent / "api_sunset_state.json"

# 鮮度しきい値（日）。これを超えたら該当コネクタの変更ログを手動確認する。
STALE_DAYS = 120

_SKIP_DIRS = {"archive", "docs", "tests", "notes", "scripts", "tools", ".git", ".github"}


def active_connectors() -> list[str]:
    out = []
    for d in sorted(ROOT.iterdir()):
        if not d.is_dir() or d.name in _SKIP_DIRS or d.name.startswith("."):
            continue
        if list(d.glob("src/*_mcp/server.py")):
            out.append(d.name)
    return out


def load_state() -> dict:
    if not STATE.exists():
        return {}
    return json.loads(STATE.read_text(encoding="utf-8")).get("connectors", {})


def days_since(date_str: str) -> int | None:
    try:
        d = _dt.date.fromisoformat(date_str)
    except (ValueError, TypeError):
        return None
    return (_dt.date.today() - d).days


def main() -> int:
    active = active_connectors()
    state = load_state()

    print("=== mcp-jp API sunset 巡回チェック ===")
    print(f"稼働コネクタ: {len(active)} / 記録済み: {len(state)} 件\n")

    exit_code = 0

    # 2. 記録漏れ（ゲート）
    missing = [c for c in active if c not in state]
    if missing:
        exit_code = 1
        print("[記録漏れ] ⚠️ api_sunset_state.json に未登録のコネクタ:")
        for m in missing:
            print(f"  - {m}: api_version・last_reviewed を追記してください")
    else:
        print("[記録漏れ] OK（稼働コネクタは全件記録済み）")

    # 1. 鮮度（警告のみ）
    stale = []
    for name, info in state.items():
        if name not in active:
            continue
        elapsed = days_since(info.get("last_reviewed"))
        if elapsed is None:
            stale.append((name, None))
        elif elapsed > STALE_DAYS:
            stale.append((name, elapsed))
    if stale:
        print(f"\n[鮮度] ⚠️ 最終レビューから {STALE_DAYS} 日超（変更ログの手動確認を推奨）:")
        for name, elapsed in stale:
            label = f"{elapsed} 日経過" if elapsed is not None else "レビュー日未記録"
            print(f"  - {name}: {label}")
    else:
        print(f"\n[鮮度] OK（全コネクタが最終レビューから {STALE_DAYS} 日以内）")

    # 3. 廃止超過（ゲート）
    overdue = []
    for name, info in state.items():
        sunset = info.get("sunset_date")
        if not sunset:
            continue
        elapsed = days_since(sunset)
        if elapsed is not None and elapsed > 0:
            overdue.append((name, sunset, info.get("api_version"), info.get("note", "")))
    if overdue:
        exit_code = 1
        print("\n[廃止超過] ⚠️ sunset_date を過ぎたまま残っているコネクタ（移行忘れの疑い）:")
        for name, sunset, version, note in overdue:
            print(f"  - {name} ({version}): sunset_date={sunset} を経過。{note}")
    else:
        print("\n[廃止超過] OK（未移行のまま sunset を過ぎたAPIバージョンなし）")

    print()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
