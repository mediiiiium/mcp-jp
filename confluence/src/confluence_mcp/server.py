import os
import json
import base64
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("confluence-mcp")


def _client() -> httpx.Client:
    email = os.environ.get("CONFLUENCE_EMAIL")
    api_token = os.environ.get("CONFLUENCE_API_TOKEN")
    subdomain = os.environ.get("CONFLUENCE_SUBDOMAIN")
    if not email:
        raise ValueError("CONFLUENCE_EMAIL が設定されていません")
    if not api_token:
        raise ValueError("CONFLUENCE_API_TOKEN が設定されていません")
    if not subdomain:
        raise ValueError("CONFLUENCE_SUBDOMAIN が設定されていません")
    credentials = base64.b64encode(f"{email}:{api_token}".encode()).decode()
    return httpx.Client(
        base_url=f"https://{subdomain}.atlassian.net/wiki/rest/api",
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_spaces",
            description="スペース一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（デフォルト25）"},
                    "type": {"type": "string", "description": "スペースタイプ: global / personal"},
                },
            },
        ),
        types.Tool(
            name="search",
            description="Confluence コンテンツを全文検索する（CQL使用）",
            inputSchema={
                "type": "object",
                "properties": {
                    "cql": {"type": "string", "description": "CQL クエリ（例: text~\"keyword\" AND space.key=\"DS\"）"},
                    "limit": {"type": "integer", "description": "取得件数（デフォルト10）"},
                },
                "required": ["cql"],
            },
        ),
        types.Tool(
            name="get_page",
            description="ページの詳細を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {"type": "string", "description": "ページID"},
                },
                "required": ["page_id"],
            },
        ),
        types.Tool(
            name="create_page",
            description="新しいページを作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "space_key": {"type": "string", "description": "スペースキー"},
                    "title": {"type": "string", "description": "ページタイトル"},
                    "body": {"type": "string", "description": "ページ本文（プレーンテキスト）"},
                    "parent_id": {"type": "string", "description": "親ページのID（省略でルートに作成）"},
                },
                "required": ["space_key", "title", "body"],
            },
        ),
        types.Tool(
            name="update_page",
            description="既存ページを更新する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {"type": "string", "description": "更新するページのID"},
                    "title": {"type": "string", "description": "新しいタイトル"},
                    "body": {"type": "string", "description": "新しい本文（プレーンテキスト）"},
                },
                "required": ["page_id", "title", "body"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "list_spaces":
        params = {"limit": arguments.get("limit", 25)}
        if arguments.get("type"):
            params["type"] = arguments["type"]
        r = client.get("/space", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "search":
        params = {
            "cql": arguments["cql"],
            "limit": arguments.get("limit", 10),
        }
        r = client.get("/search", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_page":
        page_id = arguments["page_id"]
        r = client.get(f"/content/{page_id}", params={"expand": "body.storage,version,space"})
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "create_page":
        payload = {
            "type": "page",
            "title": arguments["title"],
            "space": {"key": arguments["space_key"]},
            "body": {
                "storage": {
                    "value": arguments["body"],
                    "representation": "wiki",
                }
            },
        }
        if arguments.get("parent_id"):
            payload["ancestors"] = [{"id": arguments["parent_id"]}]
        r = client.post("/content", json=payload)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "update_page":
        page_id = arguments["page_id"]
        current = client.get(f"/content/{page_id}", params={"expand": "version"})
        current.raise_for_status()
        current_version = current.json()["version"]["number"]
        payload = {
            "type": "page",
            "title": arguments["title"],
            "version": {"number": current_version + 1},
            "body": {
                "storage": {
                    "value": arguments["body"],
                    "representation": "wiki",
                }
            },
        }
        r = client.put(f"/content/{page_id}", json=payload)
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
