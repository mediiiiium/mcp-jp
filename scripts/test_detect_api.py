#!/usr/bin/env python3
"""detect_api() の回帰テスト。

判定器は2回続けて逆方向に壊れている:
  2026-07-03 緩すぎ → Tier1候補7件中6件が誤検知
  2026-08-06 締めすぎ → 3カテゴリ104件で api_hard が1件も立たない（freee も HubSpot も落ちる）

どちら側に倒れたかを毎回このテストで確認する。ネットワークを叩くので実行は手動。
  python3 scripts/test_detect_api.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from discover_candidates import detect_api  # noqa: E402

# APIドキュメントが公開されていることを人手で確認済み。ここが False なら締めすぎ。
POSITIVES = [
    ("freee.co.jp", "freee 会計 — developers.freee.co.jp にOpenAPI公開"),
    ("hubspot.jp", "HubSpot — developers.hubspot.jp"),
    ("smarthr.jp", "SmartHR — developer.smarthr.jp"),
]

# 判定器のバグではなく、この手法そのものの上限。API_PATTERNS の7URLしか見ないので、
# そこに実体が無いサービスは APIがあっても検出できない。
# 例: moneyforward.com は developers./developer./api./docs. が全てDNS不在で、
#     主ドメイン配下の /developers /api-docs /api も404（2026-08-06実測）。
# 取りこぼしを減らすには探索先を増やすしかなく、増やせば誤検知も増える。
KNOWN_BLIND_SPOTS = [
    ("moneyforward.com", "マネーフォワード — 7つの探索先のどこにもdocsが無い"),
]

# 2026-07-03 に Tier1 として上がってしまい、人手で誤検知と確認されたもの。
# ここが True に戻ったら緩めすぎ。
NEGATIVES = [
    ("socialplus.jp", "ソーシャルPLUS — マーケTOPへのリダイレクト"),
    ("autoline.timetechnologies.ltd", "Ligla — マーケTOPへのリダイレクト"),
    ("netbot.jp", "NetBot — 「APIとは」解説ブログにキーワードが偶然含まれていただけ"),
    # Proflly のドメインは製品サイトではなくベンダーのコーポレートサイト(classmethod.jp)に
    # 解決される。あそこは開発ブログ(dev.classmethod.jp)を抱えていてAPI記事が大量にあるので、
    # 誤検知しやすい。resolve_domain() の弱点でもあり、最も落としにくい負例。
    ("classmethod.jp", "Proflly — 解決先がベンダーのコーポレートサイト、無関係な告知ページ"),
]


def main():
    failed = []

    print("=== APIが実在する（True を期待）===")
    for domain, note in POSITIVES:
        sig = detect_api(domain)
        ok = sig.api_hard
        print(f"  {'OK  ' if ok else 'NG  '} {domain:32} api_hard={sig.api_hard} "
              f"evidence={sig.api_evidence[:3]} url={sig.api_url[:50]}")
        print(f"       {note}")
        if not ok:
            failed.append(f"取りこぼし: {domain}（{note}）")

    print("\n=== 誤検知の実物（False を期待）===")
    for domain, note in NEGATIVES:
        sig = detect_api(domain)
        ok = not sig.api_hard
        print(f"  {'OK  ' if ok else 'NG  '} {domain:32} api_hard={sig.api_hard} "
              f"evidence={sig.api_evidence[:3]} url={sig.api_url[:50]}")
        print(f"       {note}")
        if not ok:
            failed.append(f"誤検知の再発: {domain}（{note}）")

    print("\n=== 手法の上限（検出できないことが分かっているもの）===")
    for domain, note in KNOWN_BLIND_SPOTS:
        sig = detect_api(domain)
        state = "想定どおり検出できず" if not sig.api_hard else "★検出できるようになった"
        print(f"  {domain:32} api_hard={sig.api_hard}  {state}")
        print(f"       {note}")

    print()
    if failed:
        print(f"✗ {len(failed)}件の不合格:")
        for f in failed:
            print(f"  - {f}")
        return 1
    print(f"✓ 全{len(POSITIVES) + len(NEGATIVES)}件合格")
    return 0


if __name__ == "__main__":
    sys.exit(main())
