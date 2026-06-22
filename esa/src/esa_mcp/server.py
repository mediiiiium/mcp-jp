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
            description="esa の記事一覧を取得する（キーワード・カテゴリ・タグで絞り込み可）",
            inputSchema={
                "type": "object",
                "properties": {
                    "q": {
                        "type": "string",
                        "description": "検索クエリ（例: 'keyword', 'category:開発', 'tag:API', 'wip:false'）",
                    },
                    "sort": {
                        "type": "string",
                        "description": "ソート項目（updated: 更新順, created: 作成順, number: 番号順, stars: スター順）",
                        "enum": ["updated", "created", "number", "stars", "watches", "comments", "best_match"],
                        "default": "updated",
                    },
                    "order": {
                        "type": "string",
                        "description": "ソート方向（desc: 降順, asc: 昇順）",
                        "enum": ["desc", "asc"],
                        "default": "desc",
                    },
                    "page": {
                        "type": "integer",
                        "description": "ページ番号（デフォルト: 1）",
                        "default": 1,
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "1ページあたりの件数（最大100、デフォルト20）",
                        "default": 20,
                    },
                },
            },
        ),
        types.Tool(
            name="get_post",
            description="記事番号を指定して esa の記事を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "post_number": {
                        "type": "integer",
                        "description": "記事番号（URLの #123 の数字）",
                    },
                    "include": {
                        "type": "string",
                        "description": "追加取得するデータ（comments: コメント, stargazers: スター）",
                    },
                },
                "required": ["post_number"],
            },
        ),
        types.Tool(
            name="create_post",
            description="esa に新しい記事を投稿する",
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
                        "description": "WIP（作業中）状態にするか（デフォルト: true）",
                        "default": True,
                    },
                    "message": {
                        "type": "string",
                        "description": "変更メモ",
                    },
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="update_post",
            description="esa の記事を更新する",
            inputSchema={
                "type": "object",
                "properties": {
                    "post_number": {
                        "type": "integer",
                        "description": "更新する記事番号",
                    },
                    "name": {
                        "type": "string",
                        "description": "新しいタイトル",
                    },
                    "body_md": {
                        "type": "string",
                        "description": "新しい本文（Markdown形式）",
                    },
                    "category": {
                        "type": "string",
                        "description": "カテゴリ",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "タグのリスト",
                    },
                    "wip": {
                        "type": "boolean",
                        "description": "WIP状態",
                    },
                    "message": {
                        "type": "string",
                        "description": "変更メモ",
                    },
                },
                "required": ["post_number"],
            },
        ),
        types.Tool(
            name="list_comments",
            description="チーム全体またはダッシュボードのコメント一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer",
                        "description": "ページ番号（デフォルト: 1）",
                        "default": 1,
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "1ページあたりの件数（最大100、デフォルト20）",
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
