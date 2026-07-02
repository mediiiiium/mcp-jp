#!/usr/bin/env python3
"""
MCPエコシステム動向ウォッチャー

週次でMCPエコシステムの新着情報を6ソースから収集し、前回実行との差分を
notes/mcp_trend_state.json で検出、新着分だけを Markdown ダイジェスト
（notes/mcp_trend_digest.md）にまとめる。仕様の背景は docs/x-trend-digest.md 参照。

収集ソース:
  1. GitHub topic検索      … topic:mcp-server / topic:model-context-protocol の新着リポジトリ
  2. 公式org Releases      … modelcontextprotocol 配下の主要リポジトリの新リリース
  3. 公式MCPレジストリ     … registry.modelcontextprotocol.io の新着サーバー
  4. Glama.ai              … 非公式API。新着サーバー（仕様変更リスクあり）
  5. npm registry          … keywords:mcp-server の新着パッケージ
  6. awesome-mcp-servers   … punkpeye/awesome-mcp-servers のマージ済みPR（キュレーション済み高品質シグナル）

初回実行時は前回状態が無いため「新着」は検出せず、ベースラインの保存のみ行う
（いきなり数百件を新着として吐かないため）。2回目以降の実行から差分が出る。

使い方:
  python3 mcp_trend_digest.py                # 全ソース収集 → 差分検出 → md + state.json
  python3 mcp_trend_digest.py --token <PAT>  # GitHub rate limit 緩和（推奨、search/PR系で必須級）
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime, timedelta, timezone

import httpx

UA = {"User-Agent": "Mozilla/5.0 (compatible; mcp-jp-trend-digest/1.0)"}

# ── ソース設定 ───────────────────────────────────────────────

GITHUB_TOPICS = ["mcp-server", "model-context-protocol"]
GITHUB_TOPIC_LOOKBACK_DAYS = 21  # 週次実行 + 実行漏れのバッファ

# 公式org(42+リポジトリ)全部は追わず、主要どころだけ手動キュレーション。
# 増えたら気づいたときにここへ追記する（discover_candidates.py の IMPLEMENTED_DOMAINS と同じ運用）。
ORG_RELEASE_REPOS = [
    "modelcontextprotocol/modelcontextprotocol",  # spec本体
    "modelcontextprotocol/servers",                # reference実装
    "modelcontextprotocol/registry",
    "modelcontextprotocol/typescript-sdk",
    "modelcontextprotocol/python-sdk",
    "modelcontextprotocol/inspector",
]

REGISTRY_URL = "https://registry.modelcontextprotocol.io/v0/servers"
GLAMA_URL = "https://glama.ai/api/mcp/v1/servers"
NPM_SEARCH_URL = "https://registry.npmjs.org/-/v1/search"
AWESOME_REPO = "punkpeye/awesome-mcp-servers"

SECTION_LIMIT = 15  # 1ソースあたりダイジェストに載せる新着の上限（多すぎる回はここで打ち切り）

STATE_PATH = os.path.join(os.path.dirname(__file__), "../notes/mcp_trend_state.json")
OUT_PATH = os.path.join(os.path.dirname(__file__), "../notes/mcp_trend_digest.md")
ENV_PATH = os.path.join(os.path.dirname(__file__), "../.env")
HAS_NEW_PATH = os.path.join(os.path.dirname(__file__), "../notes/digest_has_new.json")


def load_dotenv():
    """プロジェクト直下の .env を os.environ に流し込む（既存の環境変数は上書きしない）。"""
    if not os.path.exists(ENV_PATH):
        return
    with open(ENV_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def gh_headers(token: str) -> dict:
    h = {"Accept": "application/vnd.github+json", **UA}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


# ── 1. GitHub topic検索 ─────────────────────────────────────

def fetch_github_new_repos(token: str, seen: dict) -> tuple[dict, list]:
    """topic:mcp-server / model-context-protocol の新着リポジトリ。

    API の sort=created はドキュメント通りに並ばない挙動を確認済みのため、
    取得後に created_at でクライアント側ソートする。
    """
    headers = gh_headers(token)
    by_name: dict[str, dict] = {}
    for topic in GITHUB_TOPICS:
        try:
            r = httpx.get(
                "https://api.github.com/search/repositories",
                params={"q": f"topic:{topic}", "sort": "updated", "order": "desc", "per_page": 100},
                headers=headers, timeout=15,
            )
            r.raise_for_status()
            for item in r.json().get("items", []):
                by_name[item["full_name"]] = {
                    "name": item["full_name"],
                    "url": item["html_url"],
                    "description": item.get("description") or "",
                    "created_at": item["created_at"],
                    "stars": item.get("stargazers_count", 0),
                }
        except Exception as e:
            print(f"  ✗ GitHub topic検索エラー ({topic}): {e}")

    cutoff = datetime.now(timezone.utc) - timedelta(days=GITHUB_TOPIC_LOOKBACK_DAYS)
    new_items = []
    for name, repo in sorted(by_name.items(), key=lambda kv: kv[1]["created_at"], reverse=True):
        if name in seen:
            continue
        created = datetime.fromisoformat(repo["created_at"].replace("Z", "+00:00"))
        if created < cutoff:
            continue  # 監視窓より古いものは新着扱いしない（seenには足すのでノイズは出ない）
        new_items.append(repo)

    updated_seen = {**seen, **{name: repo["created_at"] for name, repo in by_name.items()}}
    return updated_seen, new_items[:SECTION_LIMIT]


# ── 2. 公式org Releases ─────────────────────────────────────

def fetch_org_releases(token: str, seen: dict) -> tuple[dict, list]:
    headers = gh_headers(token)
    updated_seen = dict(seen)
    new_items = []
    for repo in ORG_RELEASE_REPOS:
        try:
            r = httpx.get(
                f"https://api.github.com/repos/{repo}/releases",
                params={"per_page": 1}, headers=headers, timeout=15,
            )
            r.raise_for_status()
            releases = r.json()
            if not releases:
                continue
            latest = releases[0]
            tag = latest.get("tag_name", "")
            if seen.get(repo) != tag:
                new_items.append({
                    "repo": repo,
                    "tag": tag,
                    "url": latest.get("html_url", ""),
                    "published_at": latest.get("published_at", ""),
                })
            updated_seen[repo] = tag
        except Exception as e:
            print(f"  ✗ Releases取得エラー ({repo}): {e}")
    return updated_seen, new_items


# ── 3. 公式MCPレジストリ ─────────────────────────────────────

def fetch_registry_servers(seen: dict) -> tuple[dict, list]:
    """registry.modelcontextprotocol.io の新着サーバー。

    recency順ソートが保証されていないため best-effort。先頭数百件を毎回舐めて
    「前回までに見ていないid」を新着として拾う設計（漏れる可能性はある）。
    """
    updated_seen = dict(seen)
    new_items = []
    cursor = None
    pages = 0
    while pages < 3:
        try:
            params = {"limit": 100}
            if cursor:
                params["cursor"] = cursor
            r = httpx.get(REGISTRY_URL, params=params, headers=UA, timeout=15)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"  ✗ MCPレジストリ取得エラー: {e}")
            break

        servers = data.get("servers", data.get("data", []))
        if not servers:
            break
        for s in servers:
            sid = s.get("id") or s.get("name", "")
            name = s.get("name", sid)
            if sid and sid not in seen:
                new_items.append({
                    "name": name,
                    "description": s.get("description", ""),
                    "id": sid,
                })
            if sid:
                updated_seen[sid] = name

        cursor = (data.get("metadata") or {}).get("next_cursor")
        pages += 1
        if not cursor:
            break

    return updated_seen, new_items[:SECTION_LIMIT]


# ── 4. Glama.ai（非公式API） ─────────────────────────────────

def fetch_glama_servers(seen: dict) -> tuple[dict, list]:
    """glama.ai の非公式APIから新着サーバーを拾う。公式ドキュメントが無いため
    レスポンス形式が変わる可能性がある。失敗時は静かにスキップする。
    """
    updated_seen = dict(seen)
    new_items = []
    try:
        r = httpx.get(GLAMA_URL, params={"first": 100}, headers=UA, timeout=15)
        r.raise_for_status()
        data = r.json()
        servers = data.get("servers", [])
        for s in servers:
            sid = s.get("id") or s.get("slug") or s.get("name", "")
            name = s.get("name", sid)
            if sid and sid not in seen:
                new_items.append({
                    "name": name,
                    "description": s.get("description", ""),
                    "url": f"https://glama.ai/mcp/servers/{s.get('slug', '')}" if s.get("slug") else "",
                })
            if sid:
                updated_seen[sid] = name
    except Exception as e:
        print(f"  ✗ Glama.ai取得エラー（非公式APIのため仕様変更の可能性あり）: {e}")

    return updated_seen, new_items[:SECTION_LIMIT]


# ── 5. npm registry ──────────────────────────────────────────

def fetch_npm_packages(seen: dict) -> tuple[dict, list]:
    """keywords:mcp-server の新着パッケージ。npmのdateは最新バージョンのpublish日で
    初回公開日ではないため、「前回までに見ていないパッケージ名」を新着の代理指標にする。
    """
    updated_seen = dict(seen)
    new_items = []
    try:
        r = httpx.get(
            NPM_SEARCH_URL,
            params={"text": "keywords:mcp-server", "size": 100},
            headers=UA, timeout=15,
        )
        r.raise_for_status()
        for obj in r.json().get("objects", []):
            pkg = obj.get("package", {})
            name = pkg.get("name", "")
            if not name:
                continue
            if name not in seen:
                new_items.append({
                    "name": name,
                    "description": pkg.get("description", ""),
                    "url": (pkg.get("links") or {}).get("npm", f"https://www.npmjs.com/package/{name}"),
                })
            updated_seen[name] = pkg.get("date", "")
    except Exception as e:
        print(f"  ✗ npm registry取得エラー: {e}")

    return updated_seen, new_items[:SECTION_LIMIT]


# ── 6. awesome-mcp-servers ───────────────────────────────────

def fetch_awesome_prs(token: str, seen: dict) -> tuple[dict, list]:
    """punkpeye/awesome-mcp-servers のマージ済みPR。人力キュレーション済みなので
    質の高いシグナルになる。似た名前の別リポジトリ（フォーク・派生）と混同しないこと。
    """
    headers = gh_headers(token)
    last_number = seen.get("last_number", 0)
    new_items = []
    max_seen = last_number

    try:
        r = httpx.get(
            f"https://api.github.com/repos/{AWESOME_REPO}/pulls",
            params={"state": "closed", "sort": "updated", "direction": "desc", "per_page": 30},
            headers=headers, timeout=15,
        )
        r.raise_for_status()
        for pr in r.json():
            if not pr.get("merged_at"):
                continue
            number = pr["number"]
            max_seen = max(max_seen, number)
            if number > last_number:
                new_items.append({
                    "title": pr["title"],
                    "url": pr["html_url"],
                    "merged_at": pr["merged_at"],
                })
    except Exception as e:
        print(f"  ✗ awesome-mcp-servers PR取得エラー: {e}")

    new_items.sort(key=lambda p: p["merged_at"], reverse=True)
    return {"last_number": max_seen}, new_items[:SECTION_LIMIT]


# ── 出力 ──────────────────────────────────────────────────────

SECTION_TITLES = {
    "github_topics": "新着MCPサーバーリポジトリ（GitHub topic検索）",
    "org_releases": "公式org 新リリース（modelcontextprotocol）",
    "registry_servers": "公式MCPレジストリ 新着サーバー",
    "glama_servers": "Glama.ai 新着サーバー（非公式API）",
    "npm_packages": "npm 新着パッケージ（keywords:mcp-server）",
    "awesome_prs": "awesome-mcp-servers 新着マージPR",
}


def write_markdown(results: dict[str, list], is_first_run: bool):
    today = date.today().isoformat()
    lines = [
        "# MCPエコシステム動向ダイジェスト",
        "",
        f"生成日: {today}",
        "",
    ]

    if is_first_run:
        lines += [
            "**初回実行**：ベースラインを保存しました。新着の差分検出は次回実行分から有効になります。",
            "",
        ]
        with open(OUT_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        return

    any_new = any(results.get(k) for k in SECTION_TITLES)
    if not any_new:
        lines += ["新着なし（前回実行時点から変化のあったソースはありませんでした）。", ""]
        with open(OUT_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        return

    if "github_topics" in results and results["github_topics"]:
        lines.append(f"## {SECTION_TITLES['github_topics']}")
        lines.append("")
        for repo in results["github_topics"]:
            lines.append(f"- [{repo['name']}]({repo['url']}) （★{repo['stars']}）— {repo['description']}")
        lines.append("")

    if "org_releases" in results and results["org_releases"]:
        lines.append(f"## {SECTION_TITLES['org_releases']}")
        lines.append("")
        for rel in results["org_releases"]:
            lines.append(f"- **{rel['repo']}** {rel['tag']} （{rel['published_at']}）— [リリースノート]({rel['url']})")
        lines.append("")

    if "registry_servers" in results and results["registry_servers"]:
        lines.append(f"## {SECTION_TITLES['registry_servers']}")
        lines.append("")
        for s in results["registry_servers"]:
            desc = f" — {s['description']}" if s.get("description") else ""
            lines.append(f"- {s['name']}{desc}")
        lines.append("")

    if "glama_servers" in results and results["glama_servers"]:
        lines.append(f"## {SECTION_TITLES['glama_servers']}")
        lines.append("")
        for s in results["glama_servers"]:
            desc = f" — {s['description']}" if s.get("description") else ""
            link = f" ([link]({s['url']}))" if s.get("url") else ""
            lines.append(f"- {s['name']}{desc}{link}")
        lines.append("")

    if "npm_packages" in results and results["npm_packages"]:
        lines.append(f"## {SECTION_TITLES['npm_packages']}")
        lines.append("")
        for p in results["npm_packages"]:
            desc = f" — {p['description']}" if p.get("description") else ""
            lines.append(f"- [{p['name']}]({p['url']}){desc}")
        lines.append("")

    if "awesome_prs" in results and results["awesome_prs"]:
        lines.append(f"## {SECTION_TITLES['awesome_prs']}")
        lines.append("")
        for pr in results["awesome_prs"]:
            lines.append(f"- [{pr['title']}]({pr['url']}) （merged {pr['merged_at']}）")
        lines.append("")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ── メイン ────────────────────────────────────────────────────

def run(token: str):
    is_first_run = not os.path.exists(STATE_PATH)
    prev_state = {}
    if not is_first_run:
        with open(STATE_PATH, encoding="utf-8") as f:
            prev_state = json.load(f)

    print("=== MCPエコシステム動向 収集 ===\n")

    print("[1/6] GitHub topic検索...")
    gh_seen, gh_new = fetch_github_new_repos(token, prev_state.get("github_topics", {}))
    print(f"  → 新着 {len(gh_new)}件")

    print("[2/6] 公式org Releases...")
    rel_seen, rel_new = fetch_org_releases(token, prev_state.get("org_releases", {}))
    print(f"  → 新着 {len(rel_new)}件")

    print("[3/6] 公式MCPレジストリ...")
    reg_seen, reg_new = fetch_registry_servers(prev_state.get("registry_servers", {}))
    print(f"  → 新着 {len(reg_new)}件")

    print("[4/6] Glama.ai...")
    glama_seen, glama_new = fetch_glama_servers(prev_state.get("glama_servers", {}))
    print(f"  → 新着 {len(glama_new)}件")

    print("[5/6] npm registry...")
    npm_seen, npm_new = fetch_npm_packages(prev_state.get("npm_packages", {}))
    print(f"  → 新着 {len(npm_new)}件")

    print("[6/6] awesome-mcp-servers...")
    awesome_seen, awesome_new = fetch_awesome_prs(token, prev_state.get("awesome_prs", {}))
    print(f"  → 新着 {len(awesome_new)}件")

    results = {
        "github_topics": [] if is_first_run else gh_new,
        "org_releases": [] if is_first_run else rel_new,
        "registry_servers": [] if is_first_run else reg_new,
        "glama_servers": [] if is_first_run else glama_new,
        "npm_packages": [] if is_first_run else npm_new,
        "awesome_prs": [] if is_first_run else awesome_new,
    }

    write_markdown(results, is_first_run)

    new_state = {
        "generated": date.today().isoformat(),
        "github_topics": gh_seen,
        "org_releases": rel_seen,
        "registry_servers": reg_seen,
        "glama_servers": glama_seen,
        "npm_packages": npm_seen,
        "awesome_prs": awesome_seen,
    }
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(new_state, f, ensure_ascii=False, indent=2)

    has_new = (not is_first_run) and any(results.values())
    with open(HAS_NEW_PATH, "w", encoding="utf-8") as f:
        json.dump({"has_new": has_new}, f)

    print(f"\n完了。{'初回実行（ベースライン保存のみ）' if is_first_run else ('新着あり' if has_new else '新着なし')}")
    print(f"  → {OUT_PATH}")
    print(f"  → {STATE_PATH}")


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""),
                        help="GitHub Personal Access Token（省略可、あると rate limit 緩和）")
    args = parser.parse_args()
    run(args.token)


if __name__ == "__main__":
    main()
