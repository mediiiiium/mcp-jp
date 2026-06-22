import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("dropbox-mcp")
API_BASE = "https://api.dropboxapi.com/2"


def _client() -> httpx.Client:
    access_token = os.environ.get("DROPBOX_ACCESS_TOKEN")
    if not access_token:
        raise ValueError("DROPBOX_ACCESS_TOKEN が設定されていません")
    return httpx.Client(
        base_url=API_BASE,
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_folder",
            description="フォルダの内容一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "フォルダのパス（ルートは空文字 ''）"},
                    "recursive": {"type": "boolean", "description": "サブフォルダを再帰的に取得するか（デフォルトfalse）"},
                    "limit": {"type": "integer", "description": "取得件数（デフォルト100）"},
                },
                "required": ["path"],
            },
        ),
        types.Tool(
            name="get_metadata",
            description="ファイルまたはフォルダのメタデータを取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "ファイル/フォルダのパス"},
                },
                "required": ["path"],
            },
        ),
        types.Tool(
            name="search",
            description="Dropbox 内のファイル・フォルダを検索する",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "検索キーワード"},
                    "path": {"type": "string", "description": "検索範囲のパス（省略でルートから）"},
                    "max_results": {"type": "integer", "description": "最大取得件数（デフォルト20）"},
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
                    "path": {"type": "string", "description": "作成するフォルダのパス（例: /新しいフォルダ）"},
                    "autorename": {"type": "boolean", "description": "同名フォルダが存在する場合に自動リネームするか"},
                },
                "required": ["path"],
            },
        ),
        types.Tool(
            name="get_temporary_link",
            description="ファイルの一時ダウンロードリンクを取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "ファイルのパス"},
                },
                "required": ["path"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "list_folder":
        payload = {
            "path": arguments["path"],
            "recursive": arguments.get("recursive", False),
            "limit": arguments.get("limit", 100),
        }
        r = client.post("/files/list_folder", json=payload)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_metadata":
        payload = {"path": arguments["path"]}
        r = client.post("/files/get_metadata", json=payload)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "search":
        payload = {
            "query": arguments["query"],
            "options": {"max_results": arguments.get("max_results", 20)},
        }
        if arguments.get("path"):
            payload["options"]["path"] = arguments["path"]
        r = client.post("/files/search_v2", json=payload)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "create_folder":
        payload = {
            "path": arguments["path"],
            "autorename": arguments.get("autorename", False),
        }
        r = client.post("/files/create_folder_v2", json=payload)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_temporary_link":
        payload = {"path": arguments["path"]}
        r = client.post("/files/get_temporary_link", json=payload)
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
