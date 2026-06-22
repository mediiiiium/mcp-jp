import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("heroku-mcp")
BASE_URL = "https://api.heroku.com"
HEROKU_ACCEPT = "application/vnd.heroku+json; version=3"


def _client() -> httpx.Client:
    api_token = os.environ.get("HEROKU_API_TOKEN")
    if not api_token:
        raise ValueError("HEROKU_API_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "Authorization": f"Bearer {api_token}",
            "Accept": HEROKU_ACCEPT,
            "Content-Type": "application/json",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_apps",
            description="アプリ一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="get_app",
            description="アプリの詳細を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "アプリ名またはID"},
                },
                "required": ["app_name"],
            },
        ),
        types.Tool(
            name="list_dynos",
            description="アプリのダイノ（実行インスタンス）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "アプリ名またはID"},
                },
                "required": ["app_name"],
            },
        ),
        types.Tool(
            name="list_addons",
            description="アプリのアドオン一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "アプリ名（省略で全アドオン取得）"},
                },
            },
        ),
        types.Tool(
            name="get_account",
            description="アカウント情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "list_apps":
        r = client.get("/apps")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_app":
        app_name = arguments["app_name"]
        r = client.get(f"/apps/{app_name}")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_dynos":
        app_name = arguments["app_name"]
        r = client.get(f"/apps/{app_name}/dynos")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_addons":
        if arguments.get("app_name"):
            r = client.get(f"/apps/{arguments['app_name']}/addons")
        else:
            r = client.get("/addons")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_account":
        r = client.get("/account")
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
