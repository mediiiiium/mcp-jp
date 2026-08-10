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
from urllib.parse import urlparse, urlunparse, quote_plus

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
    "cydas.com",         # cydas
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

# 2xx なのに本文がこれ未満なら「ページを見られた」とみなさない。
# ボット緩和は 4xx ではなく 200/202 + 空body で返してくることがある
# （PRONI が GitHub Actions のIPに返したのがまさに 202 + 0バイト）。
# 中身が無いのを「APIが無い」と読むと、回線の悪い日に候補を降格させてしまう。
MIN_BODY_CHARS = 200

_HERE = os.path.dirname(os.path.abspath(__file__))

# 出力先。このスクリプトが吐く候補リストには「まだ着手していない候補サービスの実名」が
# 並ぶため公開できない。単体の公開リポジトリとして使う場合は notes/ しか置き場がないが、
# 非公開の親リポジトリ配下に置かれている場合は必ずそちら（mcp-private/）へ書く。
# notes/ は公開ミラーの対象で、ここに書くと publish_mirror の policy_check が弾く。
_PARENT = os.path.normpath(os.path.join(_HERE, "../.."))
# 親が非公開モノレポであることの決め手は publish_mirror.py の存在（公開ミラーの送り出し口）。
# mcp-private/ の存在だけで判定すると、公開リポジトリをたまたま同名ディレクトリの隣に
# clone しただけで出力先が変わってしまう。
_IS_MONOREPO = os.path.isfile(os.path.join(_PARENT, "publish", "publish_mirror.py"))
_PRIVATE_DIR = os.path.join(_PARENT, "mcp-private")
_OUT_DIR = (_PRIVATE_DIR if _IS_MONOREPO and os.path.isdir(_PRIVATE_DIR)
            else os.path.join(_HERE, "../notes"))

STATE_PATH = os.path.join(_OUT_DIR, "candidates_state.json")
OUT_PATH = os.path.join(_OUT_DIR, "candidates_auto.md")
# フルスキャンで新規に Tier1 入りした候補の一覧。state と違いコミットしない一時ファイル。
NEW_TIER1_PATH = os.path.join(_OUT_DIR, "new_tier1_candidates.json")
# 人が見て却下した候補。自動判定はここを覆せない。
# これが無いと、裏取りで落とした候補が翌月のフルスキャンでそのまま「新規Tier1」として戻ってくる
# （2026-08-07 のフルスキャンで実際に発生。「新規Tier1」3件のうち2件は、前日に
# 「検出APIがベンダーの別製品のもの」と裏取りして手でTier3に落としたものだった。
# 該当サービス名と裏取りの内容は mcp-private 側の却下リストにある。ここは公開ミラーに流れるので書かない）。
# 毎月同じものを再確認させられるなら「手間なく回っている」とは言えないので、判定を残す。
REJECTED_PATH = os.path.join(_OUT_DIR, "candidates_rejected.json")
# 走行中の中間結果。フルスキャンは746サービスで1〜2時間かかるので、途中で死んだときに
# 全部やり直しにならないようカテゴリ完了ごとに書く。完走したら消す（state とは別物で、
# state はあくまで「前回の完走結果」＝新規Tier1判定の基準として保つ）。
PROGRESS_PATH = os.path.join(_OUT_DIR, "candidates_progress.json")

# .env の探索先。単体リポジトリなら直下、モノレポに取り込まれている場合は親側にある。
ENV_PATHS = [
    os.path.join(_HERE, "../.env"),
    os.path.normpath(os.path.join(_HERE, "../../.env")),
]


def load_dotenv():
    """.env を os.environ に流し込む（既存の環境変数は上書きしない）。

    依存を増やさないための最小実装。GITHUB_TOKEN をここで供給するので、
    一度 .env に書けば毎回 --token を渡さなくてよくなる。.env は .gitignore 済み。

    GitHub の検索APIは未認証だと 10req/分と厳しく、候補数百件のフルスキャンでは
    レート制限待ちで実行時間が桁違いになる。トークンを拾えないまま走り出すと
    気づけないので、見つからなかった場合は警告を出す。
    """
    for path in ENV_PATHS:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))
    if not os.environ.get("GITHUB_TOKEN"):
        print("⚠ GITHUB_TOKEN が見つかりません（.env か --token で指定してください）。"
              "未認証だと GitHub 検索が 10req/分に制限され、フルスキャンに数時間かかります。")


@dataclass
class Signals:
    api_hard: bool = False
    api_check_timeout: bool = False     # 探索が時間切れ（＝「APIが無い」と確認できていない）
    api_check_failed: bool = False      # 1ページも中身を見られなかった（回線断・ボット緩和）
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
    rejected: bool = False              # 人が裏取りして却下済み（candidates_rejected.json）
    rejected_reason: str = ""           # 却下理由。レポートに出して、判断を毎月やり直さずに済ませる
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


def resolve_official_url(proni_url: str) -> str:
    """PRONIサービスページから公式サイトURLを「パスごと」取得する。

    ここは746件ぶん必ず通るのでスキャン全体の律速。timeout はスカラーで書かないこと
    （HTTP_TIMEOUT のコメント参照。connect が12アドレス分に化ける）。

    2026-08-06 まではここでドメインだけを返していた。PRONIの「情報取得元」リンクは
    製品ごとのパスを持っている（例: www.example.com/business/services/<製品>.html）のに、
    それを捨ててドメインにしていた。結果、複数の製品を抱えるベンダーでは
    detect_api がベンダー全社の開発者ポータルを拾い、「その製品のAPI」として計上する。
    2026-08-06 のフルスキャンでは Tier1 6件のうち2件がこれで、拾った開発者ポータルの
    本文に当該製品名が1回も出てこなかった（該当サービス名は mcp-private 側のスキャン結果を参照）。

    「ベンダーのAPIか、その製品のAPIか」を自動で判定する案は2つ測って両方捨てた:
      1. API文書に製品名が出るか → developer.kingoftime.jp に「給与」0回、
         developer.smarthr.jp に「タレント」0回。正例を殺す。
      2. 製品ページがAPI文書へリンクするか → freee・KING OF TIME は0件。同じく正例を殺す。
    どちらもゲートにすると、このrepoが2回踏んでいる「締めすぎ」を再発させる。
    なので判定はしない。製品URLを捨てずに持ち回り、レポートで api_url と並べて出す
    （人間が見れば数秒で分かる。実際その2件はそうやって落とした）。
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
                # 計測用クエリ（?fr=top_lfo&set_ip2cinfo=true 等）は製品の識別に不要なので落とす
                return urlunparse(urlparse(href)._replace(query="", fragment=""))
    except Exception as e:
        # 黙って "" を返すとサービスが1件、痕跡なく候補から消える。
        # このパイプラインは「静かに0件」で何度も時間を溶かしているので必ず出す。
        print(f"  ✗ 公式URL解決失敗: {type(e).__name__} {proni_url}", flush=True)
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
    # 「そこにAPIドキュメントは無い」と言い切れた試行 / 中身を見られなかった試行。
    # 両者を数え分けないと、回線断とAPI不在が同じ api_hard=False になる。
    observed = 0
    inconclusive = 0
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
                inconclusive += 1
                continue
            if r.status_code >= 400:
                observed += 1       # 404 等は「そこには無い」という立派な観測
                continue
            if len(r.text.strip()) < MIN_BODY_CHARS:
                # 2xx なのに空 ＝ ボット緩和の典型。観測できていない側に数える。
                inconclusive += 1
                continue
            observed += 1

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

    # 1ページも中身を見られていないのに api_hard=False なら、それは「APIが無い」ではなく
    # 「調べられなかった」。watch() がこれを見て state の上書きを止める。
    sig.api_check_failed = (not sig.api_hard) and observed == 0 and inconclusive > 0
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
            params={"q": query, "per_page": 10}, headers=headers, timeout=15,
        )
        if r.status_code in (403, 429):
            wait = _search_retry_wait(r)
            print(f"  ⚠ GitHub rate limit。{wait}秒待機（{i + 1}/{attempts}）...", flush=True)
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"レート制限で {attempts} 回とも引けなかった: {query}")


# ブランド名を取り出すときに落とすサブドメインと公開サフィックス。
BRAND_SUBDOMAINS = ("www.", "biz.", "app.", "jp.", "cloud.", "service.", "my.")
BRAND_SUFFIXES = {"com", "net", "org", "jp", "co", "ne", "ad", "or", "io",
                  "ltd", "inc", "cloud", "app", "tech", "work", "biz", "info"}
# 短すぎるブランド名（ntt, sas 等）は無関係なリポジトリを大量に拾うので使わない。
BRAND_MIN_LEN = 4


def _brand_from_domain(domain: str) -> str:
    """ドメインからベンダー名を1語取り出す。freee.co.jp→freee / biz.moneyforward.com→moneyforward"""
    host = (domain or "").lower().strip()
    for p in BRAND_SUBDOMAINS:
        if host.startswith(p):
            host = host[len(p):]
            break
    labels = [x for x in host.split(".") if x]
    while len(labels) > 1 and labels[-1] in BRAND_SUFFIXES:
        labels.pop()
    return labels[-1] if labels else ""


def mcp_exists(service_name: str, domain: str, token: str) -> tuple[bool | None, str]:
    """既存MCPの有無。

    戻り値の第1要素は3値。True=あり / False=無い / None=確認できなかった。
    以前はエラー時に False を返していたが、False は「MCP無し」＝候補として生き残る、を意味する。
    つまり検索が失敗するほど Tier1 が増える fail-open になっていた。

    2026-08-06、同じ fail-open が別の層に残っていたのを修正した。
    以前はサービス名の完全一致を要求していた（`name_lower in repo_name`）ため、
    `"freee勤怠管理" in "freee-mcp"` が False になり、公式リポジトリを取りこぼしていた。
    公式MCPは英語名なので日本語の製品名が丸ごと入ることはまずない。実害として、
    ★482 の freee/freee-mcp が存在するのに freee 製品7件が Tier1（着手候補）に並んだ。
    ドメイン由来のベンダー名で引き直す。

    2026-08-06、同じ病の3例目。ベンダー名には BRAND_MIN_LEN の下限があるのに
    **サービス名側には無く**、3文字の名前が部分一致で誤爆していた。実測:
      RPM → mcperf-rpm（mcperf の RPM パッケージ。無関係）
      GEN → mcp-ui（説明文の "generative" に "gen" が一致）
    名前が4文字未満のサービスは744件中55件あり、うち4件が「MCPあり」扱いで
    候補から消えていた。短い名前は検索では決着しないので、名前側の一致は使わず、
    ベンダー名で引く。ベンダー名も短くて使えないなら None（判定不能）を返す。
    False（＝MCP無し）にしてしまうと、確認できていないものが候補として通ってしまう。
    """
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    brand = _brand_from_domain(domain)
    name_lower = service_name.lower()
    # 短い名前は部分一致が当たりすぎて信用できない（上記 RPM / GEN）。
    name_usable = len(name_lower) >= BRAND_MIN_LEN
    if not name_usable and len(brand) < BRAND_MIN_LEN:
        # 名前もベンダー名も短い。この手法では判定できないので、黙って消さず保留に回す。
        print(f"  ? MCP有無を判定できず（名前もドメインも短い）: {service_name} / {domain}",
              flush=True)
        return None, ""
    # 「マネーフォワード クラウド会計」→「マネーフォワード」。製品名の後半を落とした先頭語も見る。
    first_token = name_lower.split()[0] if name_lower.split() else ""

    queries = [f'"{service_name}" mcp', f'{service_name} mcp server']
    if len(brand) >= BRAND_MIN_LEN:
        queries.insert(0, f"{brand} mcp server")

    for query in queries:
        try:
            data = _github_search(query, headers)
        except Exception as e:
            print(f"  ✗ GitHub検索エラー（判定不能）: {e}", flush=True)
            return None, ""
        for item in data.get("items", []):
            repo_name = (item.get("name") or "").lower()
            repo_desc = (item.get("description") or "").lower()
            # MCPサーバーであること自体を必ず確認する。ベンダー名だけの一致だと
            # 無関係なリポジトリを「MCPあり」と誤判定し、良い候補を握り潰す。
            if "mcp" not in f"{repo_name} {repo_desc}":
                continue
            # ベンダー名がドメイン由来だと一般語になることがある（channel.io→"channel"）。
            # 説明文まで見ると誤爆する。実例: AlexAI-MCP/cc-channel-mem は
            # 「ClaudeCode の Discord/Telegram チャンネル用メモリ」で、同名ベンダーとは無関係。
            # ベンダー名側の判定は、リポジトリ名に ベンダー名と "mcp" が両方出るときに限る。
            # これで cc-channel-mem（mcp無し）も MCP23016（channel無し）も落ちる。
            brand_hit = (len(brand) >= BRAND_MIN_LEN
                         and brand in repo_name and "mcp" in repo_name)
            hit = (
                (name_usable and (name_lower in repo_name or name_lower in repo_desc))
                or brand_hit
                # 日本語の先頭語（「マネーフォワード クラウド会計」→「マネーフォワード」）は
                # 一般語になりにくいので説明文まで見てよい。
                or (len(first_token) >= BRAND_MIN_LEN and first_token in repo_desc)
            )
            if hit:
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


def load_rejected() -> dict:
    """人が却下した候補 {サービス名: {"date":..., "reason":...}} を読む。

    ファイルが無ければ空。壊れていても落とさない（却下は補助情報で、
    読めないことを理由に744件のスキャンを止める価値はない）。
    """
    if not os.path.exists(REJECTED_PATH):
        return {}
    try:
        with open(REJECTED_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"  ⚠ 却下リストを読めませんでした（無視して続行）: {e}", flush=True)
        return {}


def assign_tier(sig: Signals) -> str:
    if sig.rejected:
        # 人が裏取りして落としたもの。自動判定より人を優先する。
        # deprecate ではなく Tier3 に置くのは、却下理由が覆る（製品固有APIが後から出る等）
        # 可能性を残すため。復活させたいときは却下リストから消せばよい。
        return "Tier3"
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


def evaluate(svc: dict, token: str, with_ecosystem: bool = True,
             rejected: dict | None = None) -> dict:
    """1サービスを全シグナル評価し、ティアまで決めた候補dictを返す。"""
    name = svc["name"]
    rejected = load_rejected() if rejected is None else rejected

    # ドメインを先に解決する。mcp_exists() がブランド名の取り出しにドメインを使うため。
    # official_url は製品パス込み。detect_api はドメイン単位なので domain を渡すが、
    # 「そのAPIが本当にこの製品のものか」は人が見るしかないので official_url も残す
    # （resolve_official_url のコメント参照）。
    official_url = svc.get("official_url") or ""
    domain = svc.get("domain") or ""
    if not domain:
        official_url = resolve_official_url(svc["proni_url"])
        domain = _to_domain(official_url)
    has_mcp, mcp_url = mcp_exists(name, domain, token)
    sig = detect_api(domain)
    sig.mcp_check_failed = has_mcp is None
    sig.mcp_exists = has_mcp is True
    sig.mcp_url = mcp_url
    sig.self_implemented = is_implemented_domain(domain)
    sig.global_giant = any(g in domain for g in GLOBAL_GIANTS)
    if name in rejected:
        sig.rejected = True
        sig.rejected_reason = rejected[name].get("reason", "")

    # 利用者規模は Tier1 候補の優先度づけにしか使わないので、API硬判定◯のときだけ取る
    if (with_ecosystem and sig.api_hard and has_mcp is False
            and not sig.self_implemented and not sig.global_giant and not sig.rejected):
        sig.ecosystem_hits = ecosystem_signal(name)

    sig.official_ship_risk = score_official_risk(sig)
    tier = assign_tier(sig)

    return {**svc, "domain": domain, "official_url": official_url,
            "tier": tier, "signals": asdict(sig)}


# ── 出力 ──────────────────────────────────────────────────────

TIER_ORDER = {"Tier1": 0, "Tier2": 1, "Tier3": 2, "deprecate": 3}
TIER_LABEL = {
    "Tier1": "Tier 1 — 即着手候補（Lステップ的）",
    "Tier2": "Tier 2 — スタンバイ（公式が出しそう／監視）",
    "Tier3": "Tier 3 — 保留（API不明 or 海外大手）",
    "deprecate": "deprecate — 既存MCPあり（使う側）",
}


def _short_url(url: str, limit: int = 42) -> str:
    """表示用にURLを詰める。スキームと www. を落とし、長ければ末尾を … にする。"""
    s = re.sub(r"^https?://(www\.)?", "", url or "").rstrip("/")
    return s if len(s) <= limit else s[:limit - 1] + "…"


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
        # 製品ページとAPI検出先は必ず横に並べる。この2つが食い違っているとき
        # （製品ページ=vendor.com/services/<製品>.html / API=developer.vendor.com）は、別製品のAPIを
        # 拾っているので候補にならない。自動判定はできないので目視用に出す。
        lines.append("| サービス名 | カテゴリ | 製品ページ | API検出先 | 利用者規模 | リスク | 根拠 |")
        lines.append("|-----------|---------|----------|----------|:--------:|:----:|------|")
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
            if sig.get("rejected"):
                # 却下理由は必ず出す。理由が見えないと「なぜTier3なのか」を毎月調べ直すことになる。
                note.append(f"却下: {sig.get('rejected_reason') or '理由未記載'}")
            if sig.get("api_hard") and sig.get("api_evidence"):
                note.append("API: " + " · ".join(sig["api_evidence"][:3]))
            if not note:
                note.append("API硬判定なし")
            official = c.get("official_url") or ""
            product_cell = (f"[{_short_url(official)}]({official})" if official
                            else c.get("domain", "") or "—")
            api_url = sig.get("api_url") or ""
            api_cell = f"[{_short_url(api_url)}]({api_url})" if api_url else "—"
            lines.append(
                f"| {c['name']} | {c['category']} | {product_cell} | {api_cell} "
                f"| {hits_s} | {sig.get('official_ship_risk',0)} "
                f"| {'; '.join(note)} |"
            )
        lines.append("")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def save_state(candidates: list[dict], full_scan_done: bool = False):
    """state を書く。

    generated は「何かしら回った日」で、週次ウォッチでも部分スキャンでも更新される。
    それだけだと、週次が動いている限り月次フルスキャンが死んでいても新鮮に見えてしまう。
    このrepoは「緑なのに何もしていない」を既に一度やっているので（週次ウォッチが
    state 不在時に exit 0 して6週間空回りした）、フルスキャンの完走日は別に持つ。
    ダッシュボードはこちらの古さも見る。
    """
    prev_full = ""
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, encoding="utf-8") as f:
            prev_full = json.load(f).get("last_full_scan", "")
    state = {
        "generated": date.today().isoformat(),
        "last_full_scan": date.today().isoformat() if full_scan_done else prev_full,
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
    rejected = load_rejected()   # 744件ぶんファイルを開き直さないよう1回だけ読む
    if rejected:
        print(f"却下リスト {len(rejected)}件を適用します（{REJECTED_PATH}）\n")
    candidates: list[dict] = []
    done_categories: list[str] = []
    failed_categories: list[str] = []

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

        # PRONIのカテゴリが本当に空になることはない。0件は取得失敗（ボット緩和・回線）とみなす。
        # 「失敗」と「本当に空」を取り違えるなら、失敗側に倒すほうが安全（消さずに残る）。
        if not services:
            failed_categories.append(category_name)
            continue
        time.sleep(1)

        for svc in services:
            print(f"  {svc['name']}... ", end="", flush=True)
            c = evaluate(svc, token, rejected=rejected)
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

    # 部分スキャン（--categories / --max-per-category）は走査した分しか手元に無い。
    # そのまま書くと未走査のサービスが state から丸ごと消える。
    # 2026-08-07、`--categories crm --max-per-category 2` の試走で 744件が2件になった。
    # 上の「全カテゴリ0件」ガードと同じ趣旨だが、あちらは0件しか見ていないので素通りする。
    # 走査した分だけ差し替え、残りは前回の値を保持する。
    #
    # 一部のカテゴリだけ取得に失敗した場合も同じ扱いにする。全滅ガード（上）は0件しか
    # 見ていないので、20カテゴリ中3つが 202 で空になっても素通りし、その3カテゴリの
    # サービスが state から消えたうえ「フルスキャン完走」として記録されてしまう
    # （＝ダッシュボードの ⚠️ も出ない）。自宅回線以外で走ると現実に起きる。
    partial = bool(only_slugs or max_per_cat) or bool(failed_categories)
    if failed_categories:
        print(f"\n⚠ 取得できなかったカテゴリ {len(failed_categories)}件: "
              f"{', '.join(failed_categories)}")
        print("  回線・ボット緩和の可能性。このカテゴリのサービスを消さないよう既存stateにマージし、")
        print("  フルスキャン完走としては記録しません（ダッシュボードに ⚠️ が出続けます）。")
        print("  自宅回線で `--resume` を付けて回すと、失敗したカテゴリだけ取り直せます。")
    if partial:
        merged = prev_state.copy()
        merged.update({c["name"]: c for c in candidates})
        candidates = sorted(merged.values(), key=_sort_key)
        print(f"  既存stateにマージ（合計 {len(candidates)}件）", flush=True)

    write_markdown(candidates)
    save_state(candidates, full_scan_done=not partial)
    # 完走したので中間ファイルは用済み。残すと次回 --resume が誤って引き継いでしまう。
    # ただし取得に失敗したカテゴリがあるときは残す。失敗分は done_categories に入れていないので、
    # --resume を付けるとそこだけ取り直せる（消してしまうと744件を最初からやり直しになる）。
    if os.path.exists(PROGRESS_PATH) and not failed_categories:
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

    rejected = load_rejected()
    targets = [c for c in prev.values() if c["tier"] in ("Tier1", "Tier2")]
    print(f"=== ウォッチャー: Tier1/2 の {len(targets)}件を再評価"
          + (f"（却下リスト {len(rejected)}件を適用）" if rejected else "") + " ===\n")

    changes = []
    unverified = []
    for c in targets:
        svc = {"name": c["name"], "category": c["category"],
               "proni_url": c.get("proni_url", ""), "domain": c.get("domain", ""),
               "official_url": c.get("official_url", "")}
        new = evaluate(svc, token, with_ecosystem=False, rejected=rejected)
        nsig = new["signals"]
        blocked = ("API確認不可" if nsig.get("api_check_failed") else
                   "MCP確認不可" if nsig.get("mcp_check_failed") else "")
        if blocked and new["tier"] != c["tier"]:
            # 降格の根拠が「確認できなかった」だけのケース。ここで書き戻すと、その候補は
            # Tier1/2 から外れて翌週以降の再評価対象にすら入らず、次の月次フルスキャンまで
            # 消えたままになる（週次は Tier1/2 しか見ないので自己修復しない）。
            # 回線が悪い月曜が一度あるだけでパイプラインが空になるので、上書きしない。
            unverified.append((c["name"], c["tier"], new["tier"], blocked))
            time.sleep(1)
            continue
        if new["tier"] != c["tier"]:
            changes.append((c["name"], c["tier"], new["tier"], nsig))
        prev[c["name"]] = new  # 状態更新
        time.sleep(1)

    if unverified and len(unverified) == len(targets):
        # 全件が確認不可＝回線かボット緩和。state を書かずに落とす。
        # generated が古いままになるので、ダッシュボードに ⚠️ が出る。
        print(f"✗ {len(targets)}件すべて確認できませんでした（回線・ボット緩和の可能性）。")
        for name, old, newt, why in unverified:
            print(f"  {name}: {old} → {newt} になるところを保留（{why}）")
        print("state は更新しません。自宅回線で再実行してください。")
        sys.exit(1)

    if unverified:
        print(f"⚠ 確認できず保留した候補 {len(unverified)}件（降格させていません）:")
        for name, old, newt, why in unverified:
            print(f"  {name}: {old} のまま（{why} / 判定上は {newt}）")
        print()

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
