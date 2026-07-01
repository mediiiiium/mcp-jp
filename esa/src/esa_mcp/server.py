import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("esa-mcp")

BASE_URL = "https://api.esa.io"


def _client() -> tuple[httpx.Client, str]:
    token = os.environ.get("ESA_ACCESS_TOKEN")
    team = os.environ.get("ESA_TEAM_NAME")
    if not token:
        raise ValueError("ESA_ACCESS_TOKEN が設定されていません")
    if not team:
        raise ValueError("ESA_TEAM_NAME が設定されていません")
    client = httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=30,
    )
    return client, team


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_posts",
            description=(
                "esa チーム内の記事を検索・一覧取得する。記事番号が既に分かっている場合は get_post の方が"
                "効率的で、こちらは「条件で絞り込みたい／候補を探したい」場面向き。q パラメータで esa 独自の"
                "検索クエリ構文が使え、スペース区切りで複数条件をAND指定できる（例: 'category:開発 tag:API "
                "wip:false'）。既定ソートは updated（更新日時の降順）。ページングは page/per_page 方式"
                "（カーソル方式ではない）で、レスポンスの total_count・next_page・prev_page を見て次ページの"
                "有無や総件数を判定する。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "q": {
                        "type": "string",
                        "description": (
                            "esa検索クエリ構文。主な指定子: title:キーワード / body:キーワード / "
                            "category:カテゴリパス（例: category:開発/API） / tag:タグ名 / wip:true|false"
                            "（作業中のみ／共有済みのみ） / kind:stock|flow（ストック/フロー記事） / "
                            "sharing:true（限定共有記事） / starred:true（自分がスターした記事） / "
                            "@screen_name（投稿者で絞り込み） / created:>=YYYY-MM-DD, updated:<YYYY-MM-DD"
                            "（日付範囲） / stars:>=N, comments:>=N, backlinks:>=N（件数条件） / "
                            "!in:\"カテゴリ名\"（指定カテゴリを除外）。複数指定子はスペース区切りでAND結合"
                            "される。省略時は全記事が対象。"
                        ),
                    },
                    "sort": {
                        "type": "string",
                        "description": (
                            "並び替え項目。updated=更新日時順（既定）、created=作成日時順、number=記事番号順、"
                            "stars=スター数順、watches=Watch数順、comments=コメント数順、"
                            "best_match=検索の関連度順（q を指定した検索時に意味を持つ）。"
                        ),
                        "enum": ["updated", "created", "number", "stars", "watches", "comments", "best_match"],
                        "default": "updated",
                    },
                    "order": {
                        "type": "string",
                        "description": "ソート方向（desc: 降順, asc: 昇順、既定 desc）",
                        "enum": ["desc", "asc"],
                        "default": "desc",
                    },
                    "page": {
                        "type": "integer",
                        "description": "ページ番号（1始まり、既定1）",
                        "default": 1,
                    },
                    "per_page": {
                        "type": "integer",
                        "description": (
                            "1ページあたりの件数（最大100、既定20）。総件数・次/前ページの有無はレスポンスの"
                            "total_count / next_page / prev_page で確認する。"
                        ),
                        "default": 20,
                    },
                },
            },
        ),
        types.Tool(
            name="get_post",
            description=(
                "記事番号を指定して1件の記事本文とメタデータを取得する。条件で候補を探す場合は list_posts を"
                "先に使う。include パラメータで関連データ（コメント・スター等）を同時に取得でき、esa APIへの"
                "追加リクエストを省ける。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "post_number": {
                        "type": "integer",
                        "description": "記事番号（URLの #123 の数字）",
                    },
                    "include": {
                        "type": "string",
                        "description": (
                            "追加取得するデータ。カンマ区切り（スペースなし）で複数指定可"
                            "（例: 'comments,comments.stargazers'）。comments=コメント一覧、"
                            "comments.stargazers=各コメントへのスター、stargazers=記事へのスター一覧、"
                            "backlinks=この記事にリンクしている他記事（最大15件まで）。省略時はいずれも含まれない。"
                        ),
                    },
                },
                "required": ["post_number"],
            },
        ),
        types.Tool(
            name="create_post",
            description=(
                "esa に新しい記事を投稿する。呼び出すたびに新しい記事番号を持つ別記事が作成され、esa API側に"
                "重複防止の仕組みはない（べき等ではない。同じ内容で複数回呼ぶと同じ記事が複数作成される）。"
                "wip を省略すると既定で true（作業中）として作成される。message は変更履歴に残る一言メモ"
                "（Gitのコミットメッセージに近い）。作成後に内容を直したい場合は update_post を使う。"
                "esa API自体には記事削除エンドポイント（DELETE .../posts/:post_number）が存在するが、"
                "誤削除防止のため本コネクタには削除ツールを実装していない（削除は esa の Web UI から行う）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "記事タイトル",
                    },
                    "body_md": {
                        "type": "string",
                        "description": "記事本文（Markdown形式）",
                    },
                    "category": {
                        "type": "string",
                        "description": "カテゴリ（例: 開発/API）",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "タグのリスト",
                    },
                    "wip": {
                        "type": "boolean",
                        "description": "WIP（作業中）状態にするか（省略時は true）",
                        "default": True,
                    },
                    "message": {
                        "type": "string",
                        "description": "変更履歴に残る一言メモ（Gitのコミットメッセージに相当）",
                    },
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="update_post",
            description=(
                "既存記事を部分更新する。name/body_md/category/tags/wip/message のうち指定した項目のみが"
                "変更され、省略した項目は変更されない。複数人が同時に編集する可能性がある場合は "
                "original_revision（直前に取得した body_md・revision番号・編集者のscreen_name）を渡すと、"
                "esa側で3-way mergeを試み、他者の変更との衝突があればレスポンスの overlapped フラグで検知できる"
                "（省略時は無条件に上書きされ、他者の変更を意図せず消す可能性がある）。esa API自体には記事削除"
                "エンドポイントが存在するが、誤削除防止のため本コネクタには削除ツールを実装していない"
                "（削除は esa の Web UI から行う）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "post_number": {
                        "type": "integer",
                        "description": "更新する記事番号",
                    },
                    "name": {
                        "type": "string",
                        "description": "新しいタイトル（省略時は変更しない）",
                    },
                    "body_md": {
                        "type": "string",
                        "description": "新しい本文（Markdown形式、省略時は変更しない）",
                    },
                    "category": {
                        "type": "string",
                        "description": "カテゴリ（省略時は変更しない）",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "タグのリスト（省略時は変更しない）",
                    },
                    "wip": {
                        "type": "boolean",
                        "description": "WIP状態（省略時は変更しない）",
                    },
                    "message": {
                        "type": "string",
                        "description": "変更履歴に残る一言メモ（省略時は変更しない）",
                    },
                    "original_revision": {
                        "type": "object",
                        "description": (
                            "他ユーザーとの同時編集による上書き事故を防ぐための3-way mergeパラメータ。"
                            "前回取得時点の内容を渡すと、esa側で他者による変更との衝突を検知し、"
                            "overlapped フラグ付きでマージ結果を返す。省略時はこのチェックを行わず単純上書きする。"
                        ),
                        "properties": {
                            "body_md": {"type": "string", "description": "前回取得時点の本文（Markdown）"},
                            "number": {"type": "integer", "description": "前回取得時点のrevision番号"},
                            "user": {"type": "string", "description": "前回更新者のscreen_name"},
                        },
                    },
                },
                "required": ["post_number"],
            },
        ),
        types.Tool(
            name="list_comments",
            description=(
                "チーム全体の最新コメントを横断的に一覧取得する（esa Web UIの「みんなの新着」に相当）。"
                "特定の記事に絞ったコメントではなく、チーム全体の会話の流れを把握したい場合に使う。"
                "ページングは page/per_page 方式（既定20、最大100）。esa APIには記事単位のコメント取得"
                "（GET .../posts/:post_number/comments）やコメントの投稿・更新・削除エンドポイントも"
                "存在するが、本コネクタではチーム全体のコメント閲覧のみに対応しており、それらは未実装。"
                "書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer",
                        "description": "ページ番号（1始まり、既定1）",
                        "default": 1,
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "1ページあたりの件数（最大100、既定20）",
                        "default": 20,
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        client, team = _client()
        with client:
            if name == "list_posts":
                params: dict = {
                    "sort": arguments.get("sort", "updated"),
                    "order": arguments.get("order", "desc"),
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 20),
                }
                if arguments.get("q"):
                    params["q"] = arguments["q"]
                r = client.get(f"/v1/teams/{team}/posts", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_post":
                num = arguments["post_number"]
                params = {}
                if arguments.get("include"):
                    params["include"] = arguments["include"]
                r = client.get(f"/v1/teams/{team}/posts/{num}", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "create_post":
                post_data: dict = {
                    "name": arguments["name"],
                    "wip": arguments.get("wip", True),
                }
                if arguments.get("body_md"):
                    post_data["body_md"] = arguments["body_md"]
                if arguments.get("category"):
                    post_data["category"] = arguments["category"]
                if arguments.get("tags"):
                    post_data["tags"] = arguments["tags"]
                if arguments.get("message"):
                    post_data["message"] = arguments["message"]
                r = client.post(f"/v1/teams/{team}/posts", content=json.dumps({"post": post_data}))
                r.raise_for_status()
                return format_response(r.json())

            elif name == "update_post":
                num = arguments["post_number"]
                post_data = {}
                for field in ["name", "body_md", "category", "tags", "wip", "message"]:
                    if arguments.get(field) is not None:
                        post_data[field] = arguments[field]
                if arguments.get("original_revision") is not None:
                    post_data["original_revision"] = arguments["original_revision"]
                r = client.patch(f"/v1/teams/{team}/posts/{num}", content=json.dumps({"post": post_data}))
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_comments":
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 20),
                }
                r = client.get(f"/v1/teams/{team}/comments", params=params)
                r.raise_for_status()
                return format_response(r.json())

            else:
                raise ValueError(f"未知のツール: {name}")
    except Exception as exc:  # noqa: BLE001
        return error_response(exc)


def main():
    import asyncio

    async def _run():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

    asyncio.run(_run())


if __name__ == "__main__":
    main()
