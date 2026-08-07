#!/usr/bin/env python3
"""resolve_official_url() の回帰テスト。

守るのは1点だけ: PRONIの「情報取得元」リンクの**パスを捨てないこと**。

2026-08-06 まではここでドメインだけを返していた。そのせいで
「www.example.com/business/services/<製品>.html」が「example.com」に潰れ、
複数製品を持つベンダーでは detect_api がベンダー全社の開発者ポータルを拾い、
それを「その製品のAPI」として計上していた。同日のフルスキャンでは Tier1 6件のうち
2件がこれで、どちらも作れないものだった。

「ベンダーのAPIか製品のAPIか」の自動判定は入れない（2案とも正例を殺すことを実測済み。
resolve_official_url のコメント参照）。人がレポートで製品ページとAPI検出先を見比べる。
だからこそ、比べる材料であるパスを落とさないことがこのテストの全て。

**このファイルは公開ミラー（mcp-jp）に流れる。** 着手前の候補サービス名を書かないこと。
題材は自社実装済みのコネクタから採っている（実装済み＝候補になり得ないので、
候補リストが更新されても実名が公開側へ漏れない）。実際に壊れた2件の具体名は
mcp-private 側のスキャン結果に記録がある。

ネットワークを叩くので実行は手動。
  python3 scripts/test_resolve_official_url.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from discover_candidates import resolve_official_url, _to_domain  # noqa: E402

# (PRONI URL, 期待する公式URL, 何を守っているか)
# 全て自社実装済みコネクタのサービス＝候補リストには載らない。
CASES = [
    # ここが本題。ベンダーが複数製品を持ち、製品ごとにパスが分かれているケース。
    # ドメインへ潰すと「どの製品の話か」が消え、別製品のAPIを取り違える。
    ("https://saas.imitsu.jp/cate-talent-management/service/4423",
     "https://smarthr.jp/function/talent-management/",
     "製品パスを保持する（潰すと同一ベンダーの別製品と区別できない）"),
    # 計測用クエリ (?fr=top_lfo&set_ip2cinfo=true) が落ちること
    ("https://saas.imitsu.jp/cate-accounting-software/service/1894",
     "https://www.freee.co.jp/erp-professional.html",
     "パスは残し、製品の識別に不要なクエリは落とす"),
    # 単一製品ベンダーはルート直。パスが無いこと自体は異常ではない
    ("https://saas.imitsu.jp/cate-attendance-management/service/33",
     "http://www.kingtime.jp/",
     "ルート直。パスが無いのが正しいケース"),
    ("https://saas.imitsu.jp/cate-talent-management/service/2808",
     "https://www.kaonavi.jp/",
     "同上。https / www あり"),
    ("https://saas.imitsu.jp/cate-invoice/service/2141",
     "https://the-board.jp/",
     "同上。www なし"),
]


def main():
    failed = []
    for proni_url, want, note in CASES:
        got = resolve_official_url(proni_url)
        # 末尾スラッシュの有無はPRONI側の表記ゆれなので同一視する
        ok = got.rstrip("/") == want.rstrip("/")
        print(f"  {'OK  ' if ok else 'NG  '} {got or '(空)'}")
        if not ok:
            print(f"       期待: {want}")
        print(f"       {note}")
        if not ok:
            failed.append(f"{proni_url} → {got or '(空)'} 期待 {want}")

    print("\n=== ドメインへの変換は従来どおり動くこと ===")
    for _, want, _ in CASES:
        d = _to_domain(want)
        print(f"  {want[:52]:54} → {d}")
        if not d:
            failed.append(f"_to_domain が空: {want}")

    print()
    if failed:
        print(f"✗ {len(failed)}件の不合格:")
        for f in failed:
            print(f"  - {f}")
        return 1
    print(f"✓ 全{len(CASES)}件合格")
    return 0


if __name__ == "__main__":
    sys.exit(main())
