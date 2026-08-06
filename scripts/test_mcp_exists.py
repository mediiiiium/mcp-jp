#!/usr/bin/env python3
"""mcp_exists() の回帰テスト。

この判定器は detect_api() と同じく両方向に壊れる:
  緩すぎ → 無関係なリポジトリを「MCPあり」と誤判定し、良い候補を deprecate で握り潰す（静かに消える）
  締めすぎ → 公式MCPを見落とし、作る必要のないものが Tier1 に並ぶ

2026-08-06 は締めすぎ側で壊れていた。サービス名の完全一致を要求していたため
`"freee勤怠管理" in "freee-mcp"` が False になり、★482 の freee 公式MCPがあるのに
freee 製品7件・マネーフォワード製品8件が Tier1（着手候補21件中15件）を占めた。

ネットワークとGitHub検索APIを叩くので実行は手動。トークンは GITHUB_TOKEN か .env。
  python3 scripts/test_mcp_exists.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from discover_candidates import mcp_exists, load_dotenv, _brand_from_domain  # noqa: E402

# 既存MCPを人手で確認済み。ここが False なら締めすぎ＝作る必要のないものが Tier1 に並ぶ。
EXISTS = [
    ("freee勤怠管理", "freee.co.jp", "freee/freee-mcp（★482、freee公式）"),
    ("freeeサイン", "freee.co.jp", "同上。製品バリエーション違いでも拾えること"),
    ("マネーフォワード クラウド会計", "biz.moneyforward.com",
     "jp-mcp/mcp-server-moneyforward ほか複数"),
]

# 既存MCPが無いことを人手で確認済み。ここが True なら緩すぎ＝良い候補を握り潰す。
# sakura.ad.jp はブランド名が「sakura」という一般語になるので最も誤爆しやすい。
NOT_EXISTS = [
    ("KING OF TIME 給与", "kingoftime.jp", "該当リポジトリなし"),
    ("SmartGo® Staple", "ntt.com", "ブランド名が ntt（3文字）で短く、使わない側に倒す"),
    ("電子契約プラットフォームβ", "sakura.ad.jp", "ブランドが一般語。誤爆の起きやすさを見る"),
]

BRAND_CASES = [
    ("freee.co.jp", "freee"),
    ("biz.moneyforward.com", "moneyforward"),
    ("kingoftime.jp", "kingoftime"),
    ("sakura.ad.jp", "sakura"),
    ("ntt.com", "ntt"),
    ("www.sbpayment.jp", "sbpayment"),
]


def main():
    load_dotenv()
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("GITHUB_TOKEN が無いと検索が rate limit で判定不能になる。中止。")
        return 2

    failed = []

    print("=== ドメイン→ベンダー名 ===")
    for domain, want in BRAND_CASES:
        got = _brand_from_domain(domain)
        ok = got == want
        print(f"  {'OK  ' if ok else 'NG  '} {domain:24} → {got!r}（期待 {want!r}）")
        if not ok:
            failed.append(f"ブランド抽出: {domain} → {got!r} 期待 {want!r}")

    print("\n=== 既存MCPあり（True を期待）===")
    for name, domain, note in EXISTS:
        has, url = mcp_exists(name, domain, token)
        ok = has is True
        print(f"  {'OK  ' if ok else 'NG  '} {name[:26]:28} has={has} {url[:56]}")
        print(f"       {note}")
        if not ok:
            failed.append(f"公式MCPの見落とし: {name}（{note}）")

    print("\n=== 既存MCPなし（False を期待）===")
    for name, domain, note in NOT_EXISTS:
        has, url = mcp_exists(name, domain, token)
        ok = has is False
        print(f"  {'OK  ' if ok else 'NG  '} {name[:26]:28} has={has} {url[:56]}")
        print(f"       {note}")
        if not ok:
            # None（判定不能）は Tier3 送りになるだけで握り潰しではないので区別する
            kind = "誤判定で候補を握り潰す" if has is True else "判定不能"
            failed.append(f"{kind}: {name}（{note}）")

    print()
    if failed:
        print(f"✗ {len(failed)}件の不合格:")
        for f in failed:
            print(f"  - {f}")
        return 1
    print(f"✓ 全{len(BRAND_CASES) + len(EXISTS) + len(NOT_EXISTS)}件合格")
    return 0


if __name__ == "__main__":
    sys.exit(main())
