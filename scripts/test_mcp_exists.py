#!/usr/bin/env python3
"""mcp_exists() の回帰テスト。

この判定器は detect_api() と同じく両方向に壊れる:
  緩すぎ → 無関係なリポジトリを「MCPあり」と誤判定し、良い候補を deprecate で握り潰す（静かに消える）
  締めすぎ → 公式MCPを見落とし、作る必要のないものが Tier1 に並ぶ

2026-08-06 は両方向で壊れていた。
  締めすぎ: サービス名の完全一致を要求していたため `"freee勤怠管理" in "freee-mcp"` が
    False になり、★482 の freee 公式MCPがあるのに freee / マネーフォワード の製品15件が
    Tier1（着手候補21件中）を占めた。
  緩すぎ: ベンダー名には長さの下限があるのに**サービス名側には無く**、3文字の名前が
    部分一致で誤爆した（RPM → mcperf-rpm、GEN → 説明文の "generative"）。
    名前が4文字未満のサービスは744件中55件あり、うち4件が候補から消えていた。

**このファイルは公開ミラー（mcp-jp）に流れる。** 着手前の候補サービス名を書かないこと。
題材は自社実装済みのコネクタ、または既にMCPが存在するサービスから採っている
（どちらも候補になり得ないので、候補リストが更新されても実名が公開側へ漏れない）。

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
NOT_EXISTS = [
    ("KING OF TIME", "kingtime.jp", "該当リポジトリなし"),
    ("invox受取請求書", "invox.jp", "該当リポジトリなし。日本語の製品名バリエーション"),
    # 短い名前の誤爆。名前側の一致を使わずベンダー名で引けば決着する側。
    ("RPM", "zeku.co.jp",
     "3文字。修正前は mcperf-rpm（mcperf の RPM パッケージ）に一致していた"),
    ("GEN", "gen-square.com",
     "3文字。修正前は説明文の 'generative' に一致していた"),
]

# 名前もベンダー名も短く、この手法では決着しないもの。None（判定不能）を返すこと。
# False（＝MCP無し）にすると、確認できていないものが候補として通ってしまう。
UNDECIDABLE = [
    ("JMP", "jmp.com", "名前3文字・ベンダー名3文字。黙って消さず保留に回す"),
    ("B4A", "service.b4a.co.jp", "同上。サブドメインを剥がしても3文字"),
]

BRAND_CASES = [
    ("freee.co.jp", "freee"),
    ("biz.moneyforward.com", "moneyforward"),
    ("kingtime.jp", "kingtime"),
    ("the-board.jp", "the-board"),
    ("esa.io", "esa"),
    ("service.b4a.co.jp", "b4a"),
]

# 手法そのものの上限（判定器のバグではない）:
# ベンダー名はドメインから取るので、一般語になるサービスでは検索が成立しない。
# 例えばドメインが channel.io なら ベンダー名は "channel" になり、
# 「channel mcp server」の上位は Discord/Telegram/YouTube 系に埋め尽くされて
# 本命が20件見ても出てこない。足りないのは検索件数ではなくカタカナ→英字の変換で、
# そこまでは作らない。該当するサービスは既存MCPを見落として Tier1 に残る
# （人手で気づける側の誤り）。具体的に該当したサービス名は mcp-private 側に記録がある。


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
            # None（判定不能）は保留に回るだけで握り潰しではないので区別する
            kind = "誤判定で候補を握り潰す" if has is True else "判定不能"
            failed.append(f"{kind}: {name}（{note}）")

    print("\n=== 判定できない（None を期待。False で通すと確認せずに候補化する）===")
    for name, domain, note in UNDECIDABLE:
        has, url = mcp_exists(name, domain, token)
        ok = has is None
        print(f"  {'OK  ' if ok else 'NG  '} {name[:26]:28} has={has}")
        print(f"       {note}")
        if not ok:
            failed.append(f"判定不能にすべきものが {has} になった: {name}（{note}）")

    print()
    total = len(BRAND_CASES) + len(EXISTS) + len(NOT_EXISTS) + len(UNDECIDABLE)
    if failed:
        print(f"✗ {len(failed)}件の不合格:")
        for f in failed:
            print(f"  - {f}")
        return 1
    print(f"✓ 全{total}件合格")
    return 0


if __name__ == "__main__":
    sys.exit(main())
