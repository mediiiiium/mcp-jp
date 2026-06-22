import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("square-mcp")
BASE_URL = "https://connect.squareup.com/v2"


def _client() -> httpx.Client:
    access_token = os.environ.get("SQUARE_ACCESS_TOKEN")
    if not access_token:
        raise ValueError("SQUARE_ACCESS_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Square-Version": "2024-04-17",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_locations",
            description="店舗ロケーション一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="list_customers",
            description="顧客一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（デフォルト100）"},
                    "sort_field": {"type": "string", "description": "ソートフィールド: DEFAULT / CREATED_AT"},
                },
            },
        ),
        types.Tool(
            name="search_customers",
            description="顧客をメール・電話番号で検索する",
            inputSchema={
                "type": "object",
                "properties": {
                    "email_address": {"type": "string", "description": "メールアドレスで検索"},
                    "phone_number": {"type": "string", "description": "電話番号で検索"},
                },
            },
        ),
        types.Tool(
            name="list_payments",
            description="決済一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "location_id": {"type": "string", "description": "ロケーションIDでフィルタ"},
                    "begin_time": {"type": "string", "description": "この日時以降の決済（RFC 3339形式）"},
                    "end_time": {"type": "string", "description": "この日時以前の決済（RFC 3339形式）"},
                    "limit": {"type": "integer", "description": "取得件数（デフォルト100）"},
                },
            },
        ),
        types.Tool(
            name="list_orders",
            description="注文一覧を取得する（ロケーション指定必須）",
            inputSchema={
                "type": "object",
                "properties": {
                    "location_ids": {"type": "array", "items": {"type": "string"}, "description": "ロケーションIDのリスト"},
                    "limit": {"type": "integer", "description": "取得件数（デフォルト100）"},
                },
                "required": ["location_ids"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "list_locations":
        r = client.get("/locations")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_customers":
        params = {"limit": arguments.get("limit", 100)}
        if arguments.get("sort_field"):
            params["sort_field"] = arguments["sort_field"]
        r = client.get("/customers", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "search_customers":
        filter_data = {}
        if arguments.get("email_address"):
            filter_data["email_address"] = {"exact": arguments["email_address"]}
        if arguments.get("phone_number"):
            filter_data["phone_number"] = {"exact": arguments["phone_number"]}
        payload = {"query": {"filter": filter_data}} if filter_data else {}
        r = client.post("/customers/search", json=payload)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_payments":
        params = {"limit": arguments.get("limit", 100)}
        if arguments.get("location_id"):
            params["location_id"] = arguments["location_id"]
        if arguments.get("begin_time"):
            params["begin_time"] = arguments["begin_time"]
        if arguments.get("end_time"):
            params["end_time"] = arguments["end_time"]
        r = client.get("/payments", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_orders":
        payload = {
            "location_ids": arguments["location_ids"],
            "limit": arguments.get("limit", 100),
        }
        r = client.post("/orders/search", json=payload)
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
