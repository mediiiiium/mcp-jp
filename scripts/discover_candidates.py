#!/usr/bin/env python3
"""
MCP候補 ティア式ウォッチャー

旧版は「MCP不在 × APIっぽいURLが200」の2軸足切りで候補を無差別に列挙していた。
本版の狙いは「Lステップ級だけを高精度で当てる選別器」。求めるのは年1〜2件の良い縦堀り
候補であって、長いリストではない。詳細仕様は notes/mcp-jp.md「発掘パイプライン」を参照。

評価する4シグナル:
  1. API硬判定        … OpenAPI/Swagger/OAuth/開発者向け本文の実在（URL 200では不十分）
  2. 公式が出さない確度 … 英語doc/dev portal/大手 = 出す側（減点）。日本語のみ国産 = 加点
  3. 利用者規模        … 「<名前> 代理店/構築」のエコシステム検索ヒット数（弱い代理指標）
  4. MCP/公式の存在    … あれば除外でなく deprecate（使う側に回す）

ティア（削除しない、降格するだけ）:
  Tier 1   即着手候補（API硬◯ × 公式が出さない確度 高 × 利用者規模◯）
  Tier 2   スタンバイ（API硬◯ だが「公式が出しそう」点灯。監視対象）
  Tier 3   保留（API怪しい / 海外グローバル大手）
  deprecate 公式・コミュニティMCPが既存

使い方:
  python3 discover_candidates.py                # フルスキャン → md + state.json
  python3 discover_candidates.py --watch        # Tier1/2 を再評価し差分だけ報告
  python3 discover_candidates.py --token <PAT>  # GitHub rate limit 緩和
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from dataclasses import dataclass, field, asdict
from datetime import date
from urllib.parse import urlparse, quote_plus

import httpx
from bs4 import BeautifulSoup

UA = {"User-Agent": "Mozilla/5.0 (compatible; mcp-jp-discover/2.0)"}

# ── カテゴリ一覧（PRONIアイミツのスラッグ） ──────────────────
CATEGORIES = [
    ("LINE・MAツール",       "line-marketing-tool"),
    ("メール配信",           "mail-delivery"),
    ("CRM・顧客管理",        "crm"),
    ("SFA・営業支援",        "sfa"),
    ("勤怠管理",             "attendance-management"),
    ("給与計算",             "payroll-software"),
    ("会計・経理",           "accounting-software"),
    ("請求書・見積",         "invoice"),
    ("予約管理",             "reservation"),
    ("POSシステム",          "pos-register"),
    ("電子契約",             "electronic-contract"),
    ("チャットボット",       "chatbot"),
    ("経費精算",             "expense"),
    ("採用管理",             "ats"),
    ("タレントマネジメント", "talent-management"),
    ("マーケティング自動化", "marketing-automation"),
    ("BI・分析",             "bi"),
    ("決済",                "payment"),
    ("在庫管理",            "inventory-control"),
]

PRONI_BASE = "https://saas.imitsu.jp"

API_PATTERNS = [
    "https://developers.{d}",
    "https://developer.{d}",
    "https://api.{d}",
    "https://docs.{d}/api",
    "https://{d}/developers",
    "https://{d}/api-docs",
    "https://{d}/api",
]

# 公式MCPを確実に出す側のグローバル大手（ドメイン部分一致）。Tier3 に落とす。
# 状況証拠の予測なので「削除」ではなく降格に使う。気づいたら手で足す。
GLOBAL_GIANTS = {
    "salesforce", "oracle", "sap", "zoho", "docusign", "squareup", "square",
    "hubspot", "google", "microsoft", "shopify", "stripe", "atlassian",
    "adobe", "servicenow", "freshworks", "freshworks",
}

# API硬判定に使う本文キーワード（lowercase照合）。openapi/swagger/oauth は単独で強い。
API_STRONG = ("openapi", "swagger", "oauth", "access token", "アクセストークン")
API_WEAK = (
    "api key", "client_id", "client secret", "endpoint", "rate limit",
    "/v1/", "/v2/", "認証", "api利用", "apiリファレンス", "api reference",
    "rest api", "webhook",
)

# 公式が出しそう確度のしきい値。これ以上なら Tier2（スタンバイ）へ。
RISK_THRESHOLD = 40

STATE_PATH = os.path.join(os.path.dirname(__file__), "../notes/candidates_state.json")
OUT_PATH = os.path.join(os.path.dirname(__file__), "../notes/candidates_auto.md")


@dataclass
class Signals:
    api_hard: bool = False
    api_url: str = ""
    api_evidence: list = field(default_factory=list)
    has_openapi: bool = False           # OpenAPI/Swagger 公開（API実在の硬い証拠 かつ 開発者志向）
    english_docs: bool = False          # 英語ドキュメント（開発者志向＝出す側のシグナル）
    global_giant: bool = False          # 海外グローバル大手
    ecosystem_hits: int | None = None   # 「<名前> 代理店/構築」検索ヒット数（弱い代理指標）
    mcp_exists: bool = False
    mcp_url: str = ""
    official_ship_risk: int = 0         # 0-100。高いほど公式が出しそう＝降格


# ── PRONIスクレイパー ─────────────────────────────────────────

def fetch_services(category_slug: str, category_name: str) -> list[dict]:
    url = f"{PRONI_BASE}/cate-{category_slug}/serviceList"
    try:
        r = httpx.get(url, timeout=15, follow_redirects=True, headers=UA)
        r.raise_for_status()
    except Exception as e:
        print(f"  ✗ 取得失敗 ({category_name}): {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    seen_ids: set[str] = set()
    services = []

    for a in soup.select(f"a[href*='/cate-{category_slug}/service/']"):
        href = a.get("href", "")
        m = re.search(r"/service/(\d+)$", href)
        if not m:
            continue
        service_id = m.group(1)
        if service_id in seen_ids:
            continue
        seen_ids.add(service_id)

        raw = a.get_text(strip=True)
        name = re.split(r"[（出典提供詳細\n]", raw)[0].strip()
        if not name or len(name) < 2 or name in ("詳細をみる", "もっと見る"):
            continue

        services.append({
            "name": name,
            "category": category_name,
            "proni_url": href if href.startswith("http") else PRONI_BASE + href,
        })

    return services


def resolve_domain(proni_url: str) -> str:
    """PRONIサービスページから公式サイトドメインを取得する。"""
    try:
        r = httpx.get(proni_url, timeout=10, follow_redirects=True, headers=UA)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        SKIP = {"imitsu.jp", "proni.co.jp", "ai-sainavi.com",
                "industry-dx-sainavi.com", "jinji-dx-sainavi.com", "it-ranking.com"}

        for a in soup.select("a[href^='http']"):
            href = a.get("href", "")
            text = a.get_text(strip=True)
            domain = _to_domain(href)
            if not domain or any(s in domain for s in SKIP):
                continue
            if any(kw in text for kw in ["情報取得元", "公式", "サービスサイト", "公式HP"]):
                return domain
    except Exception:
        pass
    return ""


def _to_domain(url: str) -> str:
    try:
        host = urlparse(url).netloc
        return re.sub(r"^www\.", "", host)
    except Exception:
        return ""


# ── シグナル1: API硬判定 ──────────────────────────────────────

def _japanese_ratio(text: str) -> float:
    """本文に占める日本語文字（かな・カナ・漢字）の割合。英語doc判定に使う。"""
    if not text:
        return 0.0
    jp = len(re.findall(r"[぀-ヿ一-鿿]", text))
    letters = len(re.findall(r"[A-Za-z぀-ヿ一-鿿]", text))
    return jp / letters if letters else 0.0


def detect_api(domain: str) -> Signals:
    """APIドキュメントを硬く判定する。URL 200では不十分なので本文の中身を見る。"""
    sig = Signals()
    if not domain:
        return sig

    for pattern in API_PATTERNS:
        url = pattern.format(d=domain)
        try:
            r = httpx.get(url, timeout=8, follow_redirects=True, headers=UA)
        except Exception:
            continue
        if r.status_code >= 400:
            continue

        body = r.text.lower()
        evidence = []
        if any(k in body for k in API_STRONG):
            evidence += [k for k in API_STRONG if k in body]
        weak_hits = [k for k in API_WEAK if k in body]
        evidence += weak_hits

        # 硬判定: 強キーワード1つ or 弱キーワード2つ以上
        strong_hit = any(k in body for k in API_STRONG)
        if strong_hit or len(weak_hits) >= 2:
            sig.api_hard = True
            sig.api_url = url
            sig.api_evidence = evidence[:6]
            sig.has_openapi = ("openapi" in body) or ("swagger" in body)
            # 英語doc判定: html lang か 本文の日本語率
            lang = ""
            m = re.search(r'<html[^>]*\blang=["\']?([a-zA-Z-]+)', r.text)
            if m:
                lang = m.group(1).lower()
            text = BeautifulSoup(r.text, "html.parser").get_text(" ", strip=True)
            sig.english_docs = lang.startswith("en") or (
                len(text) > 500 and _japanese_ratio(text) < 0.02
            )
            return sig

    return sig


# ── シグナル3: 利用者規模（エコシステム検索ヒット） ───────────

def ecosystem_signal(name: str) -> int | None:
    """「<名前> 代理店/構築」の検索ヒット数を弱い代理指標として取る。best-effort。

    代理店・構築業者が食えている＝SMB利用者が厚い、というLステップで効いた信号。
    DuckDuckGo の軽量HTMLを叩く。失敗時は None（指標なし）を返す。
    """
    q = quote_plus(f'"{name}" 代理店 構築')
    try:
        r = httpx.get(f"https://html.duckduckgo.com/html/?q={q}",
                      timeout=10, follow_redirects=True, headers=UA)
        if r.status_code >= 400:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        return len(soup.select("a.result__a"))
    except Exception:
        return None


# ── シグナル4: MCP/公式の存在 ─────────────────────────────────

def mcp_exists(service_name: str, token: str) -> tuple[bool, str]:
    """既存MCPの有無。日本語名は英語リポジトリにマッチしにくいので語を足して2回引く。"""
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    queries = [f'"{service_name}" mcp', f'{service_name} mcp server']
    for query in queries:
        try:
            r = httpx.get(
                "https://api.github.com/search/repositories",
                params={"q": query, "per_page": 3}, headers=headers, timeout=10,
            )
            if r.status_code == 403:
                print("  ⚠ GitHub rate limit。60秒待機...")
                time.sleep(61)
                r = httpx.get(
                    "https://api.github.com/search/repositories",
                    params={"q": query, "per_page": 3}, headers=headers, timeout=10,
                )
            r.raise_for_status()
            data = r.json()
            items = data.get("items", [])
            if data.get("total_count", 0) > 0 and items:
                return True, items[0]["html_url"]
        except Exception as e:
            print(f"  ✗ GitHub検索エラー: {e}")
        time.sleep(1)
    return False, ""


# ── スコアリング & ティア ─────────────────────────────────────

def score_official_risk(sig: Signals) -> int:
    """「公式がMCPを出しそう」確度（0-100）。高いほど降格。削除には使わない。"""
    risk = 0
    if sig.global_giant:
        risk += 60
    if sig.english_docs:
        risk += 40
    if sig.has_openapi:
        risk += 20  # OpenAPI公開は開発者志向＝出す側に寄る
    return min(risk, 100)


def assign_tier(sig: Signals) -> str:
    if sig.mcp_exists:
        return "deprecate"          # 既にMCPあり → 使う側に回す
    if not sig.api_hard:
        return "Tier3"              # API実在が硬く確認できない
    if sig.global_giant:
        return "Tier3"              # 海外グローバル大手は確実に公式が出す
    if sig.official_ship_risk >= RISK_THRESHOLD:
        return "Tier2"              # 出しそう → 消さずスタンバイ
    return "Tier1"                  # Lステップ的


def evaluate(svc: dict, token: str, with_ecosystem: bool = True) -> dict:
    """1サービスを全シグナル評価し、ティアまで決めた候補dictを返す。"""
    name = svc["name"]

    has_mcp, mcp_url = mcp_exists(name, token)
    domain = svc.get("domain") or resolve_domain(svc["proni_url"])
    sig = detect_api(domain)
    sig.mcp_exists = has_mcp
    sig.mcp_url = mcp_url
    sig.global_giant = any(g in domain for g in GLOBAL_GIANTS)

    # 利用者規模は Tier1 候補の優先度づけにしか使わないので、API硬判定◯のときだけ取る
    if with_ecosystem and sig.api_hard and not has_mcp and not sig.global_giant:
        sig.ecosystem_hits = ecosystem_signal(name)

    sig.official_ship_risk = score_official_risk(sig)
    tier = assign_tier(sig)

    return {**svc, "domain": domain, "tier": tier, "signals": asdict(sig)}


# ── 出力 ──────────────────────────────────────────────────────

TIER_ORDER = {"Tier1": 0, "Tier2": 1, "Tier3": 2, "deprecate": 3}
TIER_LABEL = {
    "Tier1": "Tier 1 — 即着手候補（Lステップ的）",
    "Tier2": "Tier 2 — スタンバイ（公式が出しそう／監視）",
    "Tier3": "Tier 3 — 保留（API不明 or 海外大手）",
    "deprecate": "deprecate — 既存MCPあり（使う側）",
}


def _sort_key(c: dict):
    sig = c["signals"]
    # Tier1内は利用者規模シグナル降順（None は最後）、その後リスク昇順
    hits = sig.get("ecosystem_hits")
    hits_rank = -(hits if hits is not None else -1)
    return (TIER_ORDER.get(c["tier"], 9), hits_rank, sig.get("official_ship_risk", 0))


def write_markdown(candidates: list[dict]):
    today = date.today().isoformat()
    lines = [
        "# MCP開発候補リスト（ティア式・自動生成）",
        "",
        f"生成日: {today}  ",
        "ソース: PRONIアイミツ 各カテゴリ  ",
        "判定: API硬判定 / 公式が出さない確度 / 利用者規模 / 既存MCP有無（notes/mcp-jp.md 参照）",
        "",
    ]
    by_tier: dict[str, list[dict]] = {}
    for c in candidates:
        by_tier.setdefault(c["tier"], []).append(c)

    for tier in ("Tier1", "Tier2", "Tier3", "deprecate"):
        items = by_tier.get(tier, [])
        if not items:
            continue
        lines.append(f"## {TIER_LABEL[tier]}（{len(items)}件）")
        lines.append("")
        lines.append("| サービス名 | カテゴリ | ドメイン | 利用者規模 | リスク | 根拠 | リンク |")
        lines.append("|-----------|---------|--------|:--------:|:----:|------|------|")
        for c in sorted(items, key=_sort_key):
            sig = c["signals"]
            hits = sig.get("ecosystem_hits")
            hits_s = "—" if hits is None else str(hits)
            note = []
            if sig.get("mcp_exists"):
                note.append("MCP既存")
            if sig.get("english_docs"):
                note.append("英語doc")
            if sig.get("has_openapi"):
                note.append("OpenAPI")
            if sig.get("global_giant"):
                note.append("海外大手")
            if sig.get("api_hard") and sig.get("api_evidence"):
                note.append("API: " + " · ".join(sig["api_evidence"][:3]))
            if not note:
                note.append("API硬判定なし")
            link = sig.get("api_url") or c.get("proni_url", "")
            lines.append(
                f"| {c['name']} | {c['category']} | {c.get('domain','')} "
                f"| {hits_s} | {sig.get('official_ship_risk',0)} "
                f"| {'; '.join(note)} | [link]({link}) |"
            )
        lines.append("")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def save_state(candidates: list[dict]):
    state = {
        "generated": date.today().isoformat(),
        "candidates": {c["name"]: c for c in candidates},
    }
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def load_state() -> dict:
    if not os.path.exists(STATE_PATH):
        return {}
    with open(STATE_PATH, encoding="utf-8") as f:
        return json.load(f).get("candidates", {})


# ── フルスキャン ──────────────────────────────────────────────

def full_scan(token: str, only_slugs: list[str] | None = None, max_per_cat: int | None = None):
    print("=== MCP候補 スキャン ===\n")
    candidates: list[dict] = []

    cats = CATEGORIES
    if only_slugs:
        cats = [(n, s) for (n, s) in CATEGORIES if s in only_slugs]
        if not cats:
            print(f"該当カテゴリなし: {only_slugs}（スラッグは CATEGORIES を参照）")
            return

    for category_name, slug in cats:
        print(f"\n[{category_name}] サービス取得中...")
        services = fetch_services(slug, category_name)
        if max_per_cat:
            services = services[:max_per_cat]
        print(f"  → {len(services)}件")
        time.sleep(1)

        for svc in services:
            print(f"  {svc['name']}... ", end="", flush=True)
            c = evaluate(svc, token)
            candidates.append(c)
            print(f"{c['tier']} (risk={c['signals']['official_ship_risk']})")
            time.sleep(1)

    candidates.sort(key=_sort_key)
    write_markdown(candidates)
    save_state(candidates)

    counts = {t: sum(1 for c in candidates if c["tier"] == t) for t in TIER_ORDER}
    print(f"\n完了: Tier1={counts['Tier1']} / Tier2={counts['Tier2']} "
          f"/ Tier3={counts['Tier3']} / deprecate={counts['deprecate']}")
    print(f"  → {OUT_PATH}")
    print(f"  → {STATE_PATH}")


# ── ウォッチャー（差分のみ再評価） ────────────────────────────

def watch(token: str):
    """Tier1/2 を再評価し、ティア変化（昇格/降格/deprecate）だけを報告する。"""
    prev = load_state()
    if not prev:
        print("state が無いので、まず引数なしでフルスキャンしてください。")
        return

    targets = [c for c in prev.values() if c["tier"] in ("Tier1", "Tier2")]
    print(f"=== ウォッチャー: Tier1/2 の {len(targets)}件を再評価 ===\n")

    changes = []
    for c in targets:
        svc = {"name": c["name"], "category": c["category"],
               "proni_url": c.get("proni_url", ""), "domain": c.get("domain", "")}
        new = evaluate(svc, token, with_ecosystem=False)
        if new["tier"] != c["tier"]:
            changes.append((c["name"], c["tier"], new["tier"], new["signals"]))
        prev[c["name"]] = new  # 状態更新
        time.sleep(1)

    if not changes:
        print("ティア変化なし。")
    else:
        print("ティア変化あり:\n")
        for name, old, newt, sig in changes:
            reason = "MCP化" if sig.get("mcp_exists") else \
                     ("公式が出しそう" if newt == "Tier2" else "再評価")
            print(f"  {name}: {old} → {newt}（{reason}）")

    # state を保存し直す（md は変化があったときだけ作り直してもよい）
    save_state(list(prev.values()))
    print(f"\nstate 更新: {STATE_PATH}")


# ── メイン ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""),
                        help="GitHub Personal Access Token（省略可、あると rate limit 緩和）")
    parser.add_argument("--watch", action="store_true",
                        help="フルスキャンせず Tier1/2 を再評価して差分だけ報告")
    parser.add_argument("--categories", default="",
                        help="対象カテゴリslugをカンマ区切りで限定（例: line-marketing-tool,crm）")
    parser.add_argument("--max-per-category", type=int, default=None,
                        help="各カテゴリの先頭N件だけ評価（token無しの試走用）")
    args = parser.parse_args()

    if args.watch:
        watch(args.token)
    else:
        slugs = [s.strip() for s in args.categories.split(",") if s.strip()] or None
        full_scan(args.token, only_slugs=slugs, max_per_cat=args.max_per_category)


if __name__ == "__main__":
    main()
