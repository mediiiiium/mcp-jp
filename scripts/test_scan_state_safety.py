#!/usr/bin/env python3
"""フルスキャンが state を壊さないことの回帰テスト（ネットワーク不要）。

このrepoは「候補が黙って消える」を何度も踏んでいる。同じ形の4例目が
2026-08-07 に見つかった: 20カテゴリ中3つが PRONI のボット緩和で空になっても、
残りが取れていれば全滅ガード（`if not candidates`）を素通りし、
失敗したカテゴリのサービスが state から丸ごと消えたうえ「フルスキャン完走」として
記録される。完走扱いなのでダッシュボードの ⚠️ も出ない。
自宅回線以外（テザリング・外出先Wi-Fi）で月次が走ると現実に起きる。

ここで固定するのは3点:
  1. 一部カテゴリが失敗したら、既存stateにマージする（消さない）
  2. そのとき last_full_scan を更新しない（＝ダッシュボードに ⚠️ が出続ける）
  3. 全カテゴリ成功なら置き換え、last_full_scan を更新する

ネットワークは fetch_services / evaluate を差し替えて遮断する。
state の書き先も一時ディレクトリへ向けるので、本物の candidates_state.json は触らない。

  python3 scripts/test_scan_state_safety.py
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import discover_candidates as dc  # noqa: E402


def _svc(name):
    return {"name": name, "category": "テスト", "proni_url": "", "domain": "", "official_url": ""}


def _fake_candidate(name, tier="Tier3"):
    return {"name": name, "category": "テスト", "proni_url": "", "domain": "",
            "official_url": "", "tier": tier,
            "signals": {"official_ship_risk": 0, "api_url": "", "api_evidence": [],
                        "mcp_exists": False, "has_api": True}}


def run_scan(tmpdir, category_results, prev_candidates):
    """category_results: {カテゴリ名: [サービス名...]}（空リスト = 取得失敗）"""
    dc.STATE_PATH = os.path.join(tmpdir, "state.json")
    dc.OUT_PATH = os.path.join(tmpdir, "out.md")
    dc.PROGRESS_PATH = os.path.join(tmpdir, "progress.json")
    dc.NEW_TIER1_PATH = os.path.join(tmpdir, "new_tier1.json")

    # 前回の state を用意（last_full_scan は十分に古い日付）
    with open(dc.STATE_PATH, "w", encoding="utf-8") as f:
        json.dump({"generated": "2026-01-01", "last_full_scan": "2026-01-01",
                   "candidates": {n: _fake_candidate(n) for n in prev_candidates}}, f)

    dc.CATEGORIES = [(n, f"slug-{i}") for i, n in enumerate(category_results)]
    dc.fetch_services = lambda slug, name: [_svc(s) for s in category_results[name]]
    dc.REJECTED_PATH = os.path.join(tmpdir, "rejected.json")   # 本物の却下リストを読ませない
    dc.evaluate = (lambda svc, token, with_ecosystem=True, rejected=None:
                   _fake_candidate(svc["name"]))
    dc.time.sleep = lambda _s: None

    dc.full_scan("")

    with open(dc.STATE_PATH, encoding="utf-8") as f:
        return json.load(f)


def run_watch(tmpdir, prev, results):
    """週次ウォッチを走らせる。

    prev:    {サービス名: 現在のtier}
    results: {サービス名: (再評価後のtier, 追加シグナル)} — 未指定の候補は tier 据え置き
    """
    dc.STATE_PATH = os.path.join(tmpdir, "state.json")
    dc.REJECTED_PATH = os.path.join(tmpdir, "rejected.json")
    with open(dc.STATE_PATH, "w", encoding="utf-8") as f:
        json.dump({"generated": "2026-01-01", "last_full_scan": "2026-01-01",
                   "candidates": {n: _fake_candidate(n, t) for n, t in prev.items()}}, f)

    def _fake_eval(svc, token, with_ecosystem=True, rejected=None):
        tier, extra = results.get(svc["name"], (prev[svc["name"]], {}))
        c = _fake_candidate(svc["name"], tier)
        c["signals"].update(extra)
        return c

    dc.evaluate = _fake_eval
    dc.time.sleep = lambda _s: None

    dc.watch("")

    with open(dc.STATE_PATH, encoding="utf-8") as f:
        return json.load(f)


def check(label, cond, detail=""):
    print(f"  {'✓' if cond else '✗'} {label}" + (f" — {detail}" if not cond else ""))
    return cond


def main():
    ok = True

    print("1) 一部カテゴリが取得失敗（回線・ボット緩和）")
    with tempfile.TemporaryDirectory() as td:
        st = run_scan(td,
                      {"取れたカテゴリ": ["A", "B"], "落ちたカテゴリ": []},
                      prev_candidates=["A", "B", "C-落ちたカテゴリ側", "D-落ちたカテゴリ側"])
        names = set(st["candidates"])
        ok &= check("失敗カテゴリのサービスが残っている",
                    {"C-落ちたカテゴリ側", "D-落ちたカテゴリ側"} <= names, f"残: {sorted(names)}")
        ok &= check("last_full_scan を更新していない（⚠️ が出続ける）",
                    st["last_full_scan"] == "2026-01-01", f"実際: {st['last_full_scan']}")
        ok &= check("progress を残している（--resume で失敗分だけ取り直せる）",
                    os.path.exists(dc.PROGRESS_PATH))

    print("2) 全カテゴリ成功（正常なフルスキャン）")
    with tempfile.TemporaryDirectory() as td:
        st = run_scan(td,
                      {"カテゴリ1": ["A"], "カテゴリ2": ["B"]},
                      prev_candidates=["A", "B", "消えるべき廃止サービス"])
        names = set(st["candidates"])
        ok &= check("PRONIから消えたサービスは state からも消える",
                    "消えるべき廃止サービス" not in names, f"残: {sorted(names)}")
        ok &= check("last_full_scan を更新する",
                    st["last_full_scan"] != "2026-01-01", f"実際: {st['last_full_scan']}")
        ok &= check("progress を掃除している", not os.path.exists(dc.PROGRESS_PATH))

    print("3) 全カテゴリ失敗（state を書かずに落ちる）")
    with tempfile.TemporaryDirectory() as td:
        try:
            run_scan(td, {"カテゴリ1": [], "カテゴリ2": []}, prev_candidates=["A", "B"])
            ok &= check("exit する", False, "落ちずに戻ってきた")
        except SystemExit as e:
            ok &= check("exit(1) で落ちる", e.code == 1, f"code={e.code}")
            with open(dc.STATE_PATH, encoding="utf-8") as f:
                st = json.load(f)
            ok &= check("state は前回のまま", set(st["candidates"]) == {"A", "B"})

    print("4) 週次ウォッチ: 確認不可を理由に降格させない")
    with tempfile.TemporaryDirectory() as td:
        # A は本当に降格（確認できたうえで Tier3）、B は回線が死んで確認不可。
        st = run_watch(td,
                       prev={"A": "Tier1", "B": "Tier1", "C": "Tier3"},
                       results={"A": ("Tier3", {}),
                                "B": ("Tier3", {"api_check_failed": True})})
        ok &= check("確認できた降格は反映する", st["candidates"]["A"]["tier"] == "Tier3",
                    f"実際: {st['candidates']['A']['tier']}")
        ok &= check("確認不可の降格は保留する（Tier1 のまま）",
                    st["candidates"]["B"]["tier"] == "Tier1",
                    f"実際: {st['candidates']['B']['tier']}")

    print("5) 週次ウォッチ: 全件確認不可なら state を書かずに落ちる")
    with tempfile.TemporaryDirectory() as td:
        try:
            run_watch(td, prev={"A": "Tier1", "B": "Tier2"},
                      results={"A": ("Tier3", {"api_check_failed": True}),
                               "B": ("Tier3", {"mcp_check_failed": True})})
            ok &= check("exit する", False, "落ちずに戻ってきた")
        except SystemExit as e:
            ok &= check("exit(1) で落ちる", e.code == 1, f"code={e.code}")
            with open(dc.STATE_PATH, encoding="utf-8") as f:
                st = json.load(f)
            ok &= check("generated が古いまま（ダッシュボードに ⚠️ が出る）",
                        st["generated"] == "2026-01-01", f"実際: {st['generated']}")
            ok &= check("Tier が据え置き",
                        [st["candidates"][n]["tier"] for n in ("A", "B")] == ["Tier1", "Tier2"])

    print("\n" + ("全て通過" if ok else "失敗あり"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
