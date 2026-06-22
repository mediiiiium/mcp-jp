import os
import time
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("kaonavi-mcp")

BASE_URL = "https://api.kaonavi.jp/api/v2.0"

# Simple in-process token cache
_token_cache: dict = {}


def _get_token() -> str:
    now = time.time()
    if _token_cache.get("token") and _token_cache.get("expires_at", 0) > now + 60:
        return _token_cache["token"]

    consumer_key = os.environ.get("KAONAVI_CONSUMER_KEY")
    consumer_secret = os.environ.get("KAONAVI_CONSUMER_SECRET")
    if not consumer_key or not consumer_secret:
        raise ValueError("KAONAVI_CONSUMER_KEY と KAONAVI_CONSUMER_SECRET が設定されていません")

    r = httpx.post(
        f"{BASE_URL}/token",
        auth=(consumer_key, consumer_secret),
        headers={"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
        data={"grant_type": "client_credentials"},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    _token_cache["token"] = data["access_token"]
    # カオナビトークンの有効期限は expires_in 秒（通常3600）
    _token_cache["expires_at"] = now + data.get("expires_in", 3600)
    return _token_cache["token"]


def _client() -> httpx.Client:
    token = _get_token()
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "Kaonavi-Token": token,
            "Content-Type": "application/json",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_members",
            description="メンバー（従業員）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり）", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数", "default": 20},
                },
            },
        ),
        types.Tool(
            name="get_member",
            description="特定のメンバーの詳細情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "社員コード"},
                },
                "required": ["code"],
            },
        ),
        types.Tool(
            name="list_departments",
            description="所属ツリー（部署階層）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="list_layouts",
            description="シートレイアウト（カスタムシート定義）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="get_sheet",
            description="特定シートのメンバーデータを取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "layout_id": {"type": "integer", "description": "レイアウトID（list_layoutsで確認）"},
                },
                "required": ["layout_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_members":
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 20),
                }
                r = client.get("/members", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_member":
                r = client.get(f"/members/{arguments['code']}")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_departments":
                r = client.get("/departments")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_layouts":
                r = client.get("/layouts")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_sheet":
                layout_id = arguments["layout_id"]
                r = client.get(f"/sheets/{layout_id}")
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
