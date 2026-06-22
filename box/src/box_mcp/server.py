import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("box-mcp")
BASE_URL = "https://api.box.com/2.0"


def _client() -> httpx.Client:
    access_token = os.environ.get("BOX_ACCESS_TOKEN")
    if not access_token:
        raise ValueError("BOX_ACCESS_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_folder",
            description="フォルダの内容（ファイル・サブフォルダ）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_id": {"type": "string", "description": "フォルダID（ルートは '0'）"},
                    "limit": {"type": "integer", "description": "取得件数（デフォルト100）"},
                },
                "required": ["folder_id"],
            },
        ),
        types.Tool(
            name="get_folder",
            description="フォルダの詳細情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_id": {"type": "string", "description": "フォルダID"},
                },
                "required": ["folder_id"],
            },
        ),
        types.Tool(
            name="get_file_info",
            description="ファイルの詳細情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_id": {"type": "string", "description": "ファイルID"},
                },
                "required": ["file_id"],
            },
        ),
        types.Tool(
            name="search",
            description="Box 内のファイル・フォルダを検索する",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "検索キーワード"},
                    "type": {"type": "string", "description": "検索対象タイプ: file / folder / web_link"},
                    "limit": {"type": "integer", "description": "取得件数（デフォルト20）"},
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="create_folder",
            description="新しいフォルダを作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "フォルダ名"},
                    "parent_id": {"type": "string", "description": "親フォルダID（ルートは '0'）"},
                },
                "required": ["name", "parent_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "list_folder":
        folder_id = arguments["folder_id"]
        params = {"limit": arguments.get("limit", 100)}
        r = client.get(f"/folders/{folder_id}/items", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_folder":
        folder_id = arguments["folder_id"]
        r = client.get(f"/folders/{folder_id}")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_file_info":
        file_id = arguments["file_id"]
        r = client.get(f"/files/{file_id}")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "search":
        params = {
            "query": arguments["query"],
            "limit": arguments.get("limit", 20),
        }
        if arguments.get("type"):
            params["type"] = arguments["type"]
        r = client.get("/search", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "create_folder":
        payload = {
            "name": arguments["name"],
            "parent": {"id": arguments["parent_id"]},
        }
        r = client.post("/folders", json=payload)
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
