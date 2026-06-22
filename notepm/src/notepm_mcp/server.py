import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("notepm-mcp")


def _client() -> httpx.Client:
    team_domain = os.environ.get("NOTEPM_TEAM_DOMAIN")
    access_token = os.environ.get("NOTEPM_ACCESS_TOKEN")
    if not team_domain:
        raise ValueError("NOTEPM_TEAM_DOMAIN が設定されていません")
    if not access_token:
        raise ValueError("NOTEPM_ACCESS_TOKEN が設定されていません")
    return httpx.Client(
        base_url=f"https://{team_domain}.notepm.jp/api/v1",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_notes",
            description="ノート（スペース）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（最大100）", "default": 20},
                    "include_archived": {"type": "boolean", "description": "アーカイブ済みを含むか", "default": False},
                },
            },
        ),
        types.Tool(
            name="search_pages",
            description="ページをキーワード検索する",
            inputSchema={
                "type": "object",
                "properties": {
                    "q": {"type": "string", "description": "検索キーワード"},
                    "note_code": {"type": "string", "description": "特定ノート内のみ検索する場合のノートコード"},
                    "tag_name": {"type": "string", "description": "タグで絞り込み"},
                    "only_title": {"type": "boolean", "description": "タイトルのみ検索するか"},
                    "page": {"type": "integer", "description": "ページ番号", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（最大100）", "default": 20},
                },
            },
        ),
        types.Tool(
            name="get_page",
            description="ページの詳細情報（本文を含む）を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_code": {"type": "string", "description": "ページコード"},
                },
                "required": ["page_code"],
            },
        ),
        types.Tool(
            name="create_page",
            description="新しいページを作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "note_code": {"type": "string", "description": "投稿先ノートのコード"},
                    "title": {"type": "string", "description": "ページタイトル"},
                    "body": {"type": "string", "description": "本文（Markdown形式）"},
                    "memo": {"type": "string", "description": "メモ（補足説明）"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "タグリスト"},
                },
                "required": ["note_code", "title"],
            },
        ),
        types.Tool(
            name="update_page",
            description="既存ページを更新する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_code": {"type": "string", "description": "更新するページのコード"},
                    "title": {"type": "string", "description": "新しいタイトル"},
                    "body": {"type": "string", "description": "新しい本文（Markdown形式）"},
                    "memo": {"type": "string", "description": "新しいメモ"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "新しいタグリスト"},
                },
                "required": ["page_code"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "list_notes":
        params: dict = {
            "page": arguments.get("page", 1),
            "per_page": arguments.get("per_page", 20),
            "include_archived": 1 if arguments.get("include_archived") else 0,
        }
        r = client.get("/notes", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "search_pages":
        params = {
            "page": arguments.get("page", 1),
            "per_page": arguments.get("per_page", 20),
        }
        if arguments.get("q"):
            params["q"] = arguments["q"]
        if arguments.get("note_code"):
            params["note_code"] = arguments["note_code"]
        if arguments.get("tag_name"):
            params["tag_name"] = arguments["tag_name"]
        if arguments.get("only_title"):
            params["only_title"] = 1
        r = client.get("/pages", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_page":
        r = client.get(f"/pages/{arguments['page_code']}")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "create_page":
        payload: dict = {
            "note_code": arguments["note_code"],
            "title": arguments["title"],
        }
        if arguments.get("body"):
            payload["body"] = arguments["body"]
        if arguments.get("memo"):
            payload["memo"] = arguments["memo"]
        if arguments.get("tags"):
            payload["tags"] = arguments["tags"]
        r = client.post("/pages", json=payload)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "update_page":
        payload = {}
        if arguments.get("title"):
            payload["title"] = arguments["title"]
        if arguments.get("body"):
            payload["body"] = arguments["body"]
        if arguments.get("memo"):
            payload["memo"] = arguments["memo"]
        if arguments.get("tags") is not None:
            payload["tags"] = arguments["tags"]
        r = client.patch(f"/pages/{arguments['page_code']}", json=payload)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    else:
        raise ValueError(f"未知のツール: {name}")


def main():
    import asyncio

    async def _run():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

    asyncio.run(_run())


if __name__ == "__main__":
    main()
