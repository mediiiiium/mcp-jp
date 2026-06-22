import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("base-ec-mcp")

BASE_URL = "https://api.thebase.in/1"


def _client() -> httpx.Client:
    token = os.environ.get("BASE_ACCESS_TOKEN")
    if not token:
        raise ValueError("BASE_ACCESS_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_shop",
            description="BASEショップ情報（ショップ名、URL、説明等）を取得する",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="list_items",
            description="BASEショップの商品一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "取得件数（最大100、デフォルト20）",
                        "default": 20,
                    },
                    "offset": {
                        "type": "integer",
                        "description": "取得開始位置（デフォルト0）",
                        "default": 0,
                    },
                    "order": {
                        "type": "string",
                        "description": "ソート項目（list_order: 並び順, created: 作成日）",
                        "enum": ["list_order", "created"],
                    },
                    "sort": {
                        "type": "string",
                        "description": "ソート方向（asc: 昇順, desc: 降順）",
                        "enum": ["asc", "desc"],
                    },
                },
            },
        ),
        types.Tool(
            name="list_orders",
            description="BASEショップの注文一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "取得件数（最大100、デフォルト20）",
                        "default": 20,
                    },
                    "offset": {
                        "type": "integer",
                        "description": "取得開始位置（デフォルト0）",
                        "default": 0,
                    },
                    "start_modified": {
                        "type": "string",
                        "description": "更新日時の開始（YYYY-MM-DD形式）",
                    },
                    "end_modified": {
                        "type": "string",
                        "description": "更新日時の終了（YYYY-MM-DD形式）",
                    },
                    "status": {
                        "type": "string",
                        "description": "注文ステータスで絞り込み（ordered: 注文確定, shipped: 発送済み, unshipped: 未発送, cancel: キャンセル）",
                        "enum": ["ordered", "shipped", "unshipped", "cancel"],
                    },
                },
            },
        ),
        types.Tool(
            name="get_order",
            description="注文の詳細情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "unique_key": {
                        "type": "string",
                        "description": "注文の一意キー（注文一覧から取得）",
                    },
                },
                "required": ["unique_key"],
            },
        ),
        types.Tool(
            name="update_order_status",
            description="注文の発送ステータスを更新する",
            inputSchema={
                "type": "object",
                "properties": {
                    "unique_key": {
                        "type": "string",
                        "description": "注文の一意キー",
                    },
                    "status": {
                        "type": "string",
                        "description": "更新後のステータス（shipped: 発送済みに変更）",
                        "enum": ["shipped"],
                    },
                },
                "required": ["unique_key", "status"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "get_shop":
                r = client.get("/users/me")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_items":
                params: dict = {
                    "limit": arguments.get("limit", 20),
                    "offset": arguments.get("offset", 0),
                }
                if arguments.get("order"):
                    params["order"] = arguments["order"]
                if arguments.get("sort"):
                    params["sort"] = arguments["sort"]
                r = client.get("/items", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_orders":
                params = {
                    "limit": arguments.get("limit", 20),
                    "offset": arguments.get("offset", 0),
                }
                if arguments.get("start_modified"):
                    params["start_modified"] = arguments["start_modified"]
                if arguments.get("end_modified"):
                    params["end_modified"] = arguments["end_modified"]
                if arguments.get("status"):
                    params["status"] = arguments["status"]
                r = client.get("/orders", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_order":
                key = arguments["unique_key"]
                r = client.get(f"/orders/detail/{key}")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "update_order_status":
                data = {
                    "unique_key": arguments["unique_key"],
                    "status": arguments["status"],
                }
                r = client.post("/orders/edit_status", data=data)
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
