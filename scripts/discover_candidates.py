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
import sys
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

# 自社が既に実装済みのコネクタが対象とするドメイン（各 server.py の実 API ドメインから抽出）。
# mcp_exists() は GitHub 検索で「<サービス名> mcp」に一致するリポジトリしか見ないため、
# モノレポの説明文にサービス名が出てこない自社コネクタ自身を見逃す（kingtime/mazrica で確認済みの誤検知）。
# ドメイン一致でここを補完し、Tier1 への混入を防ぐ。新規コネクタ追加時はここにも追記する。
IMPLEMENTED_DOMAINS = {
    "ak4.jp",            # akashi
    "thebase.in",        # base-ec
    "the-board.jp",      # board
    "cloudsign.jp",      # cloudsign
    "esa.io",            # esa
    "freshdesk.com",     # freshdesk
    "cybozu.com",        # garoon
    "harvestapp.com",    # harvest
    "herp.cloud",        # herp
    "ieyasu.co",         # hrmos-kintai
    "intercom.io",       # intercom
    "invox.jp",          # invox
    "jobcan.jp",         # jobcan-workflow
    "jooto.com",         # jooto
    "kaonavi.jp",        # kaonavi
    "karte.io",          # karte
    "kingtime.jp",       # kingtime
    "worksmobile.com",   # lineworks
    "worksapis.com",     # lineworks
    "lineml.jp",         # lstep
    "makeleaps.com",     # makeleaps（APIドメイン）
    "makeleaps.jp",      # makeleaps（マーケサイト。PRONIからはこちらが解決される）
    "mazrica.com",       # mazrica
    "misoca.jp",         # misoca
    "notepm.jp",         # notepm
    "pay.jp",            # payjp
    "pipedrive.com",     # pipedrive
    "relationapp.jp",    # relation
    "sendgrid.com",      # sendgrid
    "smaregi.jp",        # smaregi
    "smarthr.jp",        # smarthr
    "talentio.com",      # talentio
    "toggl.com",         # toggl
    "trello.com",        # trello
    "typeform.com",      # typeform
}


def is_implemented_domain(domain: str) -> bool:
    if not domain:
        return False
    return any(domain == d or domain.endswith("." + d) for d in IMPLEMENTED_DOMAINS)

# API硬判定に使う本文キーワード（lowercase照合）。openapi/swagger/oauth は単独で強い。
API_STRONG = ("openapi", "swagger", "oauth", "access token", "アクセストークン")
API_WEAK = (
    "api key", "client_id", "client secret", "endpoint", "rate limit",
    "/v1/", "/v2/", "認証", "api利用", "apiリファレンス", "api reference",
    "rest api", "webhook",
)

# 公式が出しそう確度のしきい値。これ以上なら Tier2（スタンバイ）へ。
RISK_THRESHOLD = 40

# 2026-07-03 セッションで Tier1候補7件中6件が誤検知と判明（notes/candidates_state.json 参照）。
# 共通パターンは「本文にキーワードは含まれるが、実際に着地したページはdevdocsではない」:
#   (a) マーケティングTOPへのリダイレクト（CC-BizMate/Ligla/ソーシャルPLUS）
#   (b) SSO/認証ウォールへのリダイレクト（SendWOW = Cloudflare Access）
#   (c) キーワードが偶然含まれるだけの無関係記事（NetBot=API解説ブログ、Proflly=無関係な告知ページ）
# これを踏まえ、「キーワード一致」だけでなく「着地URLが本物のdevdocsか」「構造的な証拠があるか」を追加で見る。

# SSO/認証ウォールとして知られるドメイン・パスの部分文字列。
# ここに着地した＝公開ドキュメントではなくログイン必須の非公開リソース、という強い陰性シグナル。
AUTH_WALL_MARKERS = (
    "cloudflareaccess.com", "/cdn-cgi/access/login", "/cdn-cgi/access",
    "auth0.com", "okta.com", "/sso", "/login", "/signin", "/sign-in",
)

# マーケティングTOP（ホームページ）へのリダイレクトとみなすパス。
# ルート直下 or よくあるトップページ相当のスラッグのみで、developers/api 等の実体が伴わない場合。
HOMEPAGE_LIKE_PATHS = ("", "/", "/index", "/index.html", "/home", "/top")

# 構造的証拠: 単発キーワードより信頼できる「本物のAPI docsらしさ」のシグナル。
# コードブロック、curl例、HTTPメソッド+パスの組、OpenAPI/Swaggerの実ファイルなど。
STRUCTURAL_PATTERNS = (
    re.compile(r"<pre[^>]*>|<code[^>]*>"),                       # コードブロック
    re.compile(r"\bcurl\s+-"),                                    # curl 実行例
    re.compile(r"\b(GET|POST|PUT|DELETE|PATCH)\s+/\S+"),          # HTTPメソッド + パス
    re.compile(r"\"openapi\"\s*:\s*\"3"),                          # OpenAPI 3.x JSON
    re.compile(r"^openapi:\s*3", re.MULTILINE),                    # OpenAPI 3.x YAML
    re.compile(r"\"swagger\"\s*:\s*\"2"),                          # Swagger 2.0 JSON
)

# 開発者専用ホストの接頭辞。マーケティングサイトはこの種のサブドメインを持たないので、
# ここに 200 で着地したこと自体が「本物のdevdocs」の証拠になる。
# 2026-07-03 の誤検知（NetBot/Proflly）は主ドメイン配下のパスで起きており、この判定には乗らない。
DEV_HOST_PREFIXES = ("developers.", "developer.", "api.", "docs.")

# detect_api() が1ドメインに使ってよい総時間。
# httpx の timeout はリクエスト単位なので、リダイレクトが連なると1ホップごとに予算が付き直し、
# 応答をゆっくり返すサーバー相手には上限にならない。実測で1ドメイン192.9秒かかった例があり、
# そのペースだと746件の完走に27時間かかる。総時間で切る。
DETECT_API_BUDGET_SEC = 20

# 接続タイムアウトは「1アドレスあたり」であって「1リクエストあたり」ではない。
# httpx の同期トランスポートは socket.create_connection 相当で、DNSが返したアドレスを
# 直列に総当たりする。PRONI(CloudFront)は saas.imitsu.jp に IPv6×8 + IPv4×4 の
# 計12アドレスを返すので、詰まると connect の12倍まで膨らむ。
# 2026-08-06 実測: 生ソケットの connect(timeout=30) が240秒（≒12アドレス分）、
# 同時刻に curl は同URLを1.2秒（curl は Happy Eyeballs で並列に試すので影響を受けない）。
# 「timeout を設定したのに1ドメイン80〜240秒かかる」の正体がこれ。
# 詰まる条件はサーバー側なので消せない。connect を詰めて最悪値を抑える。
#   最悪 12アドレス × 2秒 = 24秒（従来の3秒設定だと36秒、10秒設定だと120秒）
HTTP_TIMEOUT = httpx.Timeout(5.0, connect=2.0)
MAX_REDIRECTS = 5

STATE_PATH = os.path.join(os.path.dirname(__file__), "../notes/candidates_state.json")
OUT_PATH = os.path.join(os.path.dirname(__file__), "../notes/candidates_auto.md")
ENV_PATH = os.path.join(os.path.dirname(__file__), "../.env")
# フルスキャンで新規に Tier1 入りした候補の一覧（CI が読んで Issue 化する）。state と違いコミットしない一時ファイル。
NEW_TIER1_PATH = os.path.join(os.path.dirname(__file__), "../notes/new_tier1_candidates.json")
# 走行中の中間結果。フルスキャンは746サービスで1〜2時間かかるので、途中で死んだときに
# 全部やり直しにならないようカテゴリ完了ごとに書く。完走したら消す（state とは別物で、
# state はあくまで「前回の完走結果」＝新規Tier1判定の基準として保つ）。
PROGRESS_PATH = os.path.join(os.path.dirname(__file__), "../notes/candidates_progress.json")


def load_dotenv():
    """プロジェクト直下の .env を os.environ に流し込む（既存の環境変数は上書きしない）。

    依存を増やさないための最小実装。GITHUB_TOKEN をここで供給するので、
    一度 .env に書けば毎回 --token を渡さなくてよくなる。.env は .gitignore 済み。
    """
    if not os.path.exists(ENV_PATH):
        return
    with open(ENV_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


@dataclass
class Signals:
    api_hard: bool = False
    api_check_timeout: bool = False     # 探索が時間切れ（＝「APIが無い」と確認できていない）
    api_url: str = ""
    api_evidence: list = field(default_factory=list)
    has_openapi: bool = False           # OpenAPI/Swagger 公開（API実在の硬い証拠 かつ 開発者志向）
    english_docs: bool = False          # 英語ドキュメント（開発者志向＝出す側のシグナル）
    global_giant: bool = False          # 海外グローバル大手
    ecosystem_hits: int | None = None   # 「<名前> 代理店/構築」検索ヒット数（弱い代理指標）
    mcp_exists: bool = False
    mcp_check_failed: bool = False      # MCP有無を確認できなかった（＝「無い」と区別する）
    mcp_url: str = ""
    self_implemented: bool = False      # 自社の既存コネクタと同一ドメイン（IMPLEMENTED_DOMAINS 一致）
    official_ship_risk: int = 0         # 0-100。高いほど公式が出しそう＝降格


# ── PRONIスクレイパー ─────────────────────────────────────────

def fetch_services(category_slug: str, category_name: str) -> list[dict]:
    url = f"{PRONI_BASE}/cate-{category_slug}/serviceList"
    try:
        # 一覧は587KB前後あるので読み取りは長めに。接続だけは HTTP_TIMEOUT と同じ2秒で切る
        # （スカラーで timeout=15 と書くと connect も15秒になり、12アドレス総当たりで180秒に化ける）。
        r = httpx.get(url, timeout=httpx.Timeout(20.0, connect=2.0),
                      follow_redirects=True, headers=UA)
        r.raise_for_status()
        # PRONI 側のボット緩和は 202 + 空ボディを返す（GitHub runner の IP から実行すると
        # 全リクエストがこれになる）。raise_for_status() は 2xx を通すので明示的に弾く。
        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code}（{len(r.content)} bytes）: ボット緩和の可能性")
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
        # 文字クラス [出典提供詳細] だと1文字ごとに分割され、「支出」「提携」等を
        # 含むサービス名がその1文字目で切れてしまう。単語単位で区切る。
        name = re.split(r"（|出典|提供|詳細|\n", raw)[0].strip()
        if not name or len(name) < 2 or name in ("詳細をみる", "もっと見る"):
            continue

        services.append({
            "name": name,
            "category": category_name,
            "proni_url": href if href.startswith("http") else PRONI_BASE + href,
        })

    # 200 が返っているのに0件、は「取得失敗」と区別がつかないまま静かに空スキャンになる。
    # GitHub Actions の runner から実行すると全カテゴリ0件になる事象があるため、
    # 「サーバが別の中身を返した」のか「HTMLの構造が変わった」のかをログで切り分けられるようにする。
    if not services:
        title = ""
        t = soup.find("title")
        if t:
            title = t.get_text(strip=True)[:120]
        print(f"\n  ⚠ 0件: status={r.status_code} bytes={len(r.content)} "
              f"anchors={len(soup.find_all('a'))} title={title!r}")

    return services


def resolve_domain(proni_url: str) -> str:
    """PRONIサービスページから公式サイトドメインを取得する。

    ここは746件ぶん必ず通るのでスキャン全体の律速。timeout はスカラーで書かないこと
    （HTTP_TIMEOUT のコメント参照。connect が12アドレス分に化ける）。
    """
    try:
        r = httpx.get(proni_url, timeout=httpx.Timeout(10.0, connect=2.0),
                      follow_redirects=True, headers=UA)
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
    except Exception as e:
        # 黙って "" を返すとサービスが1件、痕跡なく候補から消える。
        # このパイプラインは「静かに0件」で何度も時間を溶かしているので必ず出す。
        print(f"  ✗ ドメイン解決失敗: {type(e).__name__} {proni_url}", flush=True)
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


def _is_redirect_to_homepage(requested_url: str, final_url: str) -> bool:
    """「/developers」等の意味あるパスを叩いたのに、リダイレクトの結果パスが
    消えてTOP相当になっていないかを判定する。

    元々パスの無いURL（https://developers.{d} のような devサブドメイン直下）は対象外――
    これは正規のdevdocsの置き方として普通にありうるので誤爆させない。
    見るのは「意味のあるパスを要求したのに、そのパスが失われたか」だけ。
    CC-BizMate・Ligla・ソーシャルPLUSは、/developers等を要求してTOPへ302/301されていた。
    """
    try:
        req_path = urlparse(requested_url).path.rstrip("/")
        final_path = urlparse(final_url).path.rstrip("/")
    except Exception:
        return False
    requested_meaningful_path = req_path not in HOMEPAGE_LIKE_PATHS
    final_lost_path = final_path in HOMEPAGE_LIKE_PATHS
    return requested_meaningful_path and final_lost_path


def _is_auth_wall(final_url: str) -> bool:
    """最終着地URLがSSO/ログインウォールかを判定する（Cloudflare Access等）。

    公開されたAPIドキュメントではなく、ログインしないと中身が見えない非公開リソース。
    SendWOW（Cloudflare Access）で確認された誤検知パターン。
    """
    lower = final_url.lower()
    return any(marker in lower for marker in AUTH_WALL_MARKERS)


def _has_structural_evidence(raw_html: str, body_lower: str) -> bool:
    """単発キーワードより強い「本物のAPI docsらしさ」の構造的証拠があるか。

    コードブロック/curl例/HTTPメソッド+パス/OpenAPI実体のいずれかがあれば、
    無関係な記事にキーワードが偶然含まれているだけ、という誤検知を減らせる。
    """
    return any(p.search(raw_html) or p.search(body_lower) for p in STRUCTURAL_PATTERNS)


def _is_dedicated_dev_host(url: str, final_url: str) -> bool:
    """developers.example.com のような開発者専用ホストに、別ホストへ飛ばされず着地したか。

    STRUCTURAL_PATTERNS は <pre>/<code>/curl 例といった「HTMLに実物が載っている」前提だが、
    最近の開発者ポータルはJSで描画するので初期HTMLにそれが無い。実測では
    developers.freee.co.jp（91KB, title "freee Developers Hub"）も
    developers.hubspot.jp（199KB, title "HubSpot開発者向けサイト"）も構造的証拠ゼロで落ちていた。
    専用ホストの存在自体を証拠として扱い、この取りこぼしを埋める。
    """
    host = urlparse(url).netloc.lower()
    if not any(host.startswith(p) for p in DEV_HOST_PREFIXES):
        return False
    # マーケTOPや認証基盤など別ホストへ飛ばされていたら証拠にしない
    return host == urlparse(final_url).netloc.lower()


def detect_api(domain: str) -> Signals:
    """APIドキュメントを硬く判定する。URL 200では不十分なので本文の中身を見る。

    2026-07-03時点の追加チェック（誤検知6/7を受けての改修）:
      1. リダイレクトを追跡し、最終URLがマーケティングTOP相当なら不採用（強い陰性）
      2. 最終URLがSSO/認証ウォール（Cloudflare Access等）なら不採用（非公開リソース）
      3. キーワード一致に加えて構造的証拠（コード例・OpenAPI実体等）を要求する。
         強キーワード（openapi/swagger/oauth等）単体では採用せず、必ず構造的証拠と併せて判定する。
    """
    sig = Signals()
    if not domain:
        return sig

    deadline = time.time() + DETECT_API_BUDGET_SEC
    client = httpx.Client(timeout=HTTP_TIMEOUT, follow_redirects=True,
                          max_redirects=MAX_REDIRECTS, headers=UA)
    try:
        for pattern in API_PATTERNS:
            if time.time() > deadline:
                # 予算切れ。「APIが無い」ではなく「調べ切れなかった」ので印を残す。
                sig.api_check_timeout = True
                break

            url = pattern.format(d=domain)
            try:
                r = client.get(url)
            except Exception:
                continue
            if r.status_code >= 400:
                continue

            final_url = str(r.url)

            # 陰性シグナル1: マーケティングTOPへのリダイレクト（devdocsの実体なし）
            if _is_redirect_to_homepage(url, final_url):
                continue
            # 陰性シグナル2: SSO/認証ウォール（公開ドキュメントではない）
            if _is_auth_wall(final_url):
                continue

            body = r.text.lower()
            evidence = []
            if any(k in body for k in API_STRONG):
                evidence += [k for k in API_STRONG if k in body]
            weak_hits = [k for k in API_WEAK if k in body]
            evidence += weak_hits

            strong_hit = any(k in body for k in API_STRONG)
            keyword_hard = strong_hit or len(weak_hits) >= 2
            if not keyword_hard:
                continue

            # キーワードが無関係な記事に偶然含まれているだけのケースを弾く。
            # （NetBotの「APIとは」解説ブログ、Profllyの無関係な告知ページがこのパターン）
            # 証拠は2通り: HTMLに実物が載っている（構造的証拠）か、開発者専用ホストに着地したか。
            # 前者だけを条件にしていた結果、JS描画のポータルを全部取りこぼしていた
            # （実測: 3カテゴリ104件で api_hard=0件。freee も HubSpot も落ちていた）。
            structural = _has_structural_evidence(r.text, body)
            dev_host = _is_dedicated_dev_host(url, final_url)
            if not (structural or dev_host):
                continue

            if dev_host and not structural:
                evidence.insert(0, "開発者専用ホスト")

            sig.api_hard = True
            sig.api_check_timeout = False   # 見つかったので予算切れは関係ない
            sig.api_url = final_url
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
    finally:
        client.close()

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

def _search_retry_wait(r: httpx.Response) -> int:
    """レート制限に当たったとき、次にいつ叩けるか。ヘッダに従い、無ければ61秒。"""
    retry_after = r.headers.get("retry-after")
    if retry_after and retry_after.isdigit():
        return max(5, min(int(retry_after), 300))
    reset = r.headers.get("x-ratelimit-reset")
    if reset and reset.isdigit():
        return max(5, min(int(int(reset) - time.time()) + 2, 300))
    return 61


def _github_search(query: str, headers: dict, attempts: int = 4) -> dict:
    """GitHub検索。検索APIは 30回/分と厳しいので、制限に当たったら reset まで待って引き直す。
    全部失敗したときだけ例外を投げる。呼び出し側はそれを「判定不能」に倒すこと。"""
    for i in range(attempts):
        r = httpx.get(
            "https://api.github.com/search/repositories",
            params={"q": query, "per_page": 3}, headers=headers, timeout=15,
        )
        if r.status_code in (403, 429):
            wait = _search_retry_wait(r)
            print(f"  ⚠ GitHub rate limit。{wait}秒待機（{i + 1}/{attempts}）...", flush=True)
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"レート制限で {attempts} 回とも引けなかった: {query}")


def mcp_exists(service_name: str, token: str) -> tuple[bool | None, str]:
    """既存MCPの有無。日本語名は英語リポジトリにマッチしにくいので語を足して2回引く。

    戻り値の第1要素は3値。True=あり / False=無い / None=確認できなかった。
    以前はエラー時に False を返していたが、False は「MCP無し」＝候補として生き残る、を意味する。
    つまり検索が失敗するほど Tier1 が増える fail-open になっていた（誤検知の主犯と見ている）。
    """
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    queries = [f'"{service_name}" mcp', f'{service_name} mcp server']
    for query in queries:
        try:
            data = _github_search(query, headers)
        except Exception as e:
            print(f"  ✗ GitHub検索エラー（判定不能）: {e}", flush=True)
            return None, ""
        items = data.get("items", [])
        if data.get("total_count", 0) > 0 and items:
            name_lower = service_name.lower()
            for item in items:
                repo_name = (item.get("name") or "").lower()
                repo_desc = (item.get("description") or "").lower()
                if name_lower in repo_name or name_lower in repo_desc:
                    return True, item["html_url"]
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
    if sig.mcp_exists or sig.self_implemented:
        return "deprecate"          # 既にMCPあり（自社実装含む） → 使う側に回す
    if sig.mcp_check_failed:
        # MCPの有無が確認できていない以上、着手候補には上げられない。保留に置けば、
        # 次回検索が通ったときに Tier1 へ上がり「新規Tier1」として拾い直される。
        return "Tier3"
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
    sig.mcp_check_failed = has_mcp is None
    sig.mcp_exists = has_mcp is True
    sig.mcp_url = mcp_url
    sig.self_implemented = is_implemented_domain(domain)
    sig.global_giant = any(g in domain for g in GLOBAL_GIANTS)

    # 利用者規模は Tier1 候補の優先度づけにしか使わないので、API硬判定◯のときだけ取る
    if (with_ecosystem and sig.api_hard and has_mcp is False
            and not sig.self_implemented and not sig.global_giant):
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
            if sig.get("self_implemented"):
                note.append("自社実装済み")
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


def save_progress(candidates: list[dict], done_categories: list[str]):
    with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
        json.dump({"done_categories": done_categories,
                   "candidates": candidates}, f, ensure_ascii=False, indent=2)


def load_progress() -> tuple[list[dict], set[str]]:
    if not os.path.exists(PROGRESS_PATH):
        return [], set()
    with open(PROGRESS_PATH, encoding="utf-8") as f:
        d = json.load(f)
    return d.get("candidates", []), set(d.get("done_categories", []))


# ── フルスキャン ──────────────────────────────────────────────

def full_scan(token: str, only_slugs: list[str] | None = None, max_per_cat: int | None = None,
              resume: bool = False):
    print("=== MCP候補 スキャン ===\n")
    prev_state = load_state()
    candidates: list[dict] = []
    done_categories: list[str] = []

    cats = CATEGORIES
    if only_slugs:
        cats = [(n, s) for (n, s) in CATEGORIES if s in only_slugs]
        if not cats:
            print(f"該当カテゴリなし: {only_slugs}（スラッグは CATEGORIES を参照）")
            return

    if resume:
        candidates, done = load_progress()
        done_categories = sorted(done)
        if candidates:
            print(f"中断分を引き継ぎ: {len(done_categories)}カテゴリ / {len(candidates)}件は再評価しません")
            cats = [(n, s) for (n, s) in cats if n not in done]
            if not cats:
                print("全カテゴリが完了済みです。仕上げだけ行います。")

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

        # カテゴリ単位で中間保存。ここで落ちても失うのは直近1カテゴリぶんだけになる。
        done_categories.append(category_name)
        save_progress(candidates, done_categories)
        print(f"  [中間保存] {len(done_categories)}カテゴリ / {len(candidates)}件", flush=True)

    # 全カテゴリ0件は「候補が無い」ではなく取得側の異常。ここで state / md を書くと
    # 空の結果が前回分を上書きし、以後の「新規Tier1」判定が全部無意味になる。書く前に落とす。
    if not candidates:
        print("\n✗ 全カテゴリで0件。PRONI 側の取得に失敗しています（上の ⚠ 行を参照）。"
              "\n  state と md は更新せずに終了します。")
        sys.exit(1)

    candidates.sort(key=_sort_key)
    write_markdown(candidates)
    save_state(candidates)
    # 完走したので中間ファイルは用済み。残すと次回 --resume が誤って引き継いでしまう。
    if os.path.exists(PROGRESS_PATH):
        os.remove(PROGRESS_PATH)

    # 新規Tier1検出: 前回 state で Tier1 でなかった（＝存在しなかった、または下位ティアだった）ものだけを拾う。
    # これが「候補が湧いたら開発にパスする」導線のトリガーになる。
    new_tier1 = [
        c for c in candidates
        if c["tier"] == "Tier1" and prev_state.get(c["name"], {}).get("tier") != "Tier1"
    ]
    with open(NEW_TIER1_PATH, "w", encoding="utf-8") as f:
        json.dump(new_tier1, f, ensure_ascii=False, indent=2)

    counts = {t: sum(1 for c in candidates if c["tier"] == t) for t in TIER_ORDER}
    print(f"\n完了: Tier1={counts['Tier1']} / Tier2={counts['Tier2']} "
          f"/ Tier3={counts['Tier3']} / deprecate={counts['deprecate']}")

    # 判定不能が多い回の結果は信用しない。何件を取りこぼしたかを必ず出す。
    unknown = sum(1 for c in candidates if c["signals"].get("mcp_check_failed"))
    if unknown:
        print(f"  ⚠ MCP有無を確認できず Tier3 に落としたもの: {unknown}/{len(candidates)}件"
              f"（{unknown * 100 // len(candidates)}%）。多いなら結果は不完全なので回し直すこと。")
    else:
        print(f"  MCP有無は全{len(candidates)}件で確認できています。")

    timed_out = sum(1 for c in candidates if c["signals"].get("api_check_timeout"))
    if timed_out:
        print(f"  ⚠ API探索が時間切れ（APIの有無を確認できていない）: "
              f"{timed_out}/{len(candidates)}件（{timed_out * 100 // len(candidates)}%）")
    print(f"  → {OUT_PATH}")
    print(f"  → {STATE_PATH}")
    if new_tier1:
        print(f"\n新規Tier1候補: {len(new_tier1)}件")
        for c in new_tier1:
            print(f"  - {c['name']} ({c['category']})")
    else:
        print("\n新規Tier1候補: なし")


# ── ウォッチャー（差分のみ再評価） ────────────────────────────

def watch(token: str):
    """Tier1/2 を再評価し、ティア変化（昇格/降格/deprecate）だけを報告する。"""
    prev = load_state()
    if not prev:
        # 以前はここで exit 0 していたため、state が復元できていない週も CI は緑になり、
        # 「毎週何もしていない」ことに気づけなかった。落として気づけるようにする。
        print("✗ state が無いので再評価できません。まず引数なしでフルスキャンしてください。")
        sys.exit(1)

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
    load_dotenv()  # .env の GITHUB_TOKEN を環境変数へ（argparse の default 評価より前）
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
    parser.add_argument("--resume", action="store_true",
                        help="中断したフルスキャンの続きから（完了済みカテゴリは再評価しない）")
    args = parser.parse_args()

    if args.watch:
        watch(args.token)
    else:
        slugs = [s.strip() for s in args.categories.split(",") if s.strip()] or None
        full_scan(args.token, only_slugs=slugs, max_per_cat=args.max_per_category,
                  resume=args.resume)


if __name__ == "__main__":
    main()
