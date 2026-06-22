import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("shopify-mcp")
API_VERSION = "2024-04"


def _client() -> httpx.Client:
    access_token = os.environ.get("SHOPIFY_ACCESS_TOKEN")
    store = os.environ.get("SHOPIFY_STORE")
    if not access_token:
        raise ValueError("SHOPIFY_ACCESS_TOKEN が設定されていません")
    if not store:
        raise ValueError("SHOPIFY_STORE が設定されていません")
    return httpx.Client(
        base_url=f"https://{store}.myshopify.com/admin/api/{API_VERSION}",
        headers={
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_products",
            description="商品一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（デフォルト50、最大250）"},
                    "status": {"type": "string", "description": "ステータス: active / archived / draft"},
                    "title": {"type": "string", "description": "商品名でフィルタ"},
                },
            },
        ),
        types.Tool(
            name="list_orders",
            description="注文一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（デフォルト50、最大250）"},
                    "status": {"type": "string", "description": "ステータス: open / closed / cancelled / any"},
                    "created_at_min": {"type": "string", "description": "この日時以降に作成された注文（ISO8601形式）"},
                    "created_at_max": {"type": "string", "description": "この日時以前に作成された注文（ISO8601形式）"},
                },
            },
        ),
        types.Tool(
            name="get_order",
            description="注文の詳細を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "integer", "description": "注文ID"},
                },
                "required": ["order_id"],
            },
        ),
        types.Tool(
            name="list_customers",
            description="顧客一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（デフォルト50、最大250）"},
                    "email": {"type": "string", "description": "メールアドレスで検索"},
                    "created_at_min": {"type": "string", "description": "この日時以降に登録された顧客（ISO8601形式）"},
                },
            },
        ),
        types.Tool(
            name="get_customer",
            description="顧客の詳細を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "integer", "description": "顧客ID"},
                },
                "required": ["customer_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "list_products":
        params = {"limit": arguments.get("limit", 50)}
        if arguments.get("status"):
            params["status"] = arguments["status"]
        if arguments.get("title"):
            params["title"] = arguments["title"]
        r = client.get("/products.json", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_orders":
        params = {
            "limit": arguments.get("limit", 50),
            "status": arguments.get("status", "any"),
        }
        if arguments.get("created_at_min"):
            params["created_at_min"] = arguments["created_at_min"]
        if arguments.get("created_at_max"):
            params["created_at_max"] = arguments["created_at_max"]
        r = client.get("/orders.json", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_order":
        order_id = arguments["order_id"]
        r = client.get(f"/orders/{order_id}.json")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_customers":
        params = {"limit": arguments.get("limit", 50)}
        if arguments.get("email"):
            params["email"] = arguments["email"]
        if arguments.get("created_at_min"):
            params["created_at_min"] = arguments["created_at_min"]
        r = client.get("/customers.json", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_customer":
        customer_id = arguments["customer_id"]
        r = client.get(f"/customers/{customer_id}.json")
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
