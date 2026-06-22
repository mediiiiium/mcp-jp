import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("notion-mcp")

BASE_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _client() -> httpx.Client:
    token = os.environ.get("NOTION_API_TOKEN")
    if not token:
        raise ValueError("NOTION_API_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="search",
            description="Notion のページ・データベースをキーワードで検索する",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "検索キーワード",
                    },
                    "filter_type": {
                        "type": "string",
                        "description": "絞り込む対象（page: ページのみ, database: DBのみ）",
                        "enum": ["page", "database"],
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "取得件数（最大100、デフォルト10）",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="get_page",
            description="ページIDを指定して Notion ページの情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "ページID（UUID形式、例: 550e8400-e29b-41d4-a716-446655440000）",
                    },
                },
                "required": ["page_id"],
            },
        ),
        types.Tool(
            name="get_page_content",
            description="ページのコンテンツ（ブロック）を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "ページID",
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "取得するブロック数（最大100、デフォルト100）",
                        "default": 100,
                    },
                },
                "required": ["page_id"],
            },
        ),
        types.Tool(
            name="query_database",
            description="Notion データベースのレコードを取得・フィルタリングする",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_id": {
                        "type": "string",
                        "description": "データベースID",
                    },
                    "filter": {
                        "type": "object",
                        "description": "フィルター条件（Notion filter object形式）",
                    },
                    "sorts": {
                        "type": "array",
                        "description": "ソート条件（例: [{\"property\": \"Name\", \"direction\": \"ascending\"}]）",
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "取得件数（最大100、デフォルト20）",
                        "default": 20,
                    },
                    "start_cursor": {
                        "type": "string",
                        "description": "ページネーション用カーソル（レスポンスの next_cursor から取得）",
                    },
                },
                "required": ["database_id"],
            },
        ),
        types.Tool(
            name="create_page",
            description="Notion にページまたはデータベースのレコードを作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "parent_id": {
                        "type": "string",
                        "description": "親のID（ページIDまたはデータベースID）",
                    },
                    "parent_type": {
                        "type": "string",
                        "description": "親の種別（page: ページ内に作成, database: DBにレコード追加）",
                        "enum": ["page", "database"],
                        "default": "page",
                    },
                    "title": {
                        "type": "string",
                        "description": "ページタイトル",
                    },
                    "properties": {
                        "type": "object",
                        "description": "DBレコードの場合のプロパティ（Notion properties object形式）",
                    },
                    "content": {
                        "type": "string",
                        "description": "ページ本文テキスト（段落として追加）",
                    },
                },
                "required": ["parent_id", "title"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "search":
        body: dict = {
            "query": arguments["query"],
            "page_size": arguments.get("page_size", 10),
        }
        if arguments.get("filter_type"):
            body["filter"] = {"value": arguments["filter_type"], "property": "object"}
        r = client.post("/search", content=json.dumps(body))
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_page":
        page_id = arguments["page_id"]
        r = client.get(f"/pages/{page_id}")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_page_content":
        page_id = arguments["page_id"]
        params = {"page_size": arguments.get("page_size", 100)}
        r = client.get(f"/blocks/{page_id}/children", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "query_database":
        db_id = arguments["database_id"]
        body = {"page_size": arguments.get("page_size", 20)}
        if arguments.get("filter"):
            body["filter"] = arguments["filter"]
        if arguments.get("sorts"):
            body["sorts"] = arguments["sorts"]
        if arguments.get("start_cursor"):
            body["start_cursor"] = arguments["start_cursor"]
        r = client.post(f"/databases/{db_id}/query", content=json.dumps(body))
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "create_page":
        parent_type = arguments.get("parent_type", "page")
        if parent_type == "database":
            parent = {"database_id": arguments["parent_id"]}
        else:
            parent = {"page_id": arguments["parent_id"]}

        props: dict = arguments.get("properties") or {
            "title": {
                "title": [{"type": "text", "text": {"content": arguments["title"]}}]
            }
        }

        body: dict = {"parent": parent, "properties": props}

        if arguments.get("content"):
            body["children"] = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": arguments["content"]}}]
                    },
                }
            ]

        r = client.post("/pages", content=json.dumps(body))
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
