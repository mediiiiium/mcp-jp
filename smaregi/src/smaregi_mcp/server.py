import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("smaregi-mcp")

BASE_URL = "https://api.smaregi.jp"


def _client() -> httpx.Client:
    token = os.environ.get("SMAREGI_ACCESS_TOKEN")
    contract_id = os.environ.get("SMAREGI_CONTRACT_ID")
    if not token:
        raise ValueError("SMAREGI_ACCESS_TOKEN が設定されていません")
    if not contract_id:
        raise ValueError("SMAREGI_CONTRACT_ID が設定されていません")
    return httpx.Client(
        base_url=f"{BASE_URL}/{contract_id}/pos",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_products",
            description="商品一覧を取得する（商品名・価格・在庫での絞り込み可）",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（最大1000）", "default": 100},
                    "page": {"type": "integer", "description": "ページ番号（1始まり）", "default": 1},
                    "product_name": {"type": "string", "description": "商品名で絞り込み（部分一致）"},
                    "category_id": {"type": "string", "description": "部門IDで絞り込み"},
                },
            },
        ),
        types.Tool(
            name="get_product",
            description="商品の詳細情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "商品ID"},
                },
                "required": ["product_id"],
            },
        ),
        types.Tool(
            name="list_transactions",
            description="売上取引一覧を取得する（日付・店舗・会員で絞り込み可）",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（最大1000）", "default": 100},
                    "page": {"type": "integer", "description": "ページ番号（1始まり）", "default": 1},
                    "store_id": {"type": "string", "description": "店舗IDで絞り込み"},
                    "transaction_date_from": {"type": "string", "description": "取引日（開始）YYYY-MM-DD"},
                    "transaction_date_to": {"type": "string", "description": "取引日（終了）YYYY-MM-DD"},
                    "customer_id": {"type": "string", "description": "会員IDで絞り込み"},
                },
            },
        ),
        types.Tool(
            name="list_customers",
            description="会員一覧を取得する（名前・ランクで絞り込み可）",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（最大1000）", "default": 100},
                    "page": {"type": "integer", "description": "ページ番号（1始まり）", "default": 1},
                    "customer_name": {"type": "string", "description": "会員名で絞り込み（部分一致）"},
                    "rank_id": {"type": "string", "description": "ランクIDで絞り込み"},
                },
            },
        ),
        types.Tool(
            name="list_stores",
            description="店舗一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数", "default": 100},
                    "page": {"type": "integer", "description": "ページ番号（1始まり）", "default": 1},
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_products":
                params: dict = {
                    "limit": arguments.get("limit", 100),
                    "page": arguments.get("page", 1),
                }
                if arguments.get("product_name"):
                    params["product_name"] = arguments["product_name"]
                if arguments.get("category_id"):
                    params["category_id"] = arguments["category_id"]
                r = client.get("/products/", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_product":
                r = client.get(f"/products/{arguments['product_id']}")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_transactions":
                params = {
                    "limit": arguments.get("limit", 100),
                    "page": arguments.get("page", 1),
                }
                if arguments.get("store_id"):
                    params["store_id"] = arguments["store_id"]
                if arguments.get("transaction_date_from"):
                    params["transaction_date_from"] = arguments["transaction_date_from"]
                if arguments.get("transaction_date_to"):
                    params["transaction_date_to"] = arguments["transaction_date_to"]
                if arguments.get("customer_id"):
                    params["customer_id"] = arguments["customer_id"]
                r = client.get("/transactions/", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_customers":
                params = {
                    "limit": arguments.get("limit", 100),
                    "page": arguments.get("page", 1),
                }
                if arguments.get("customer_name"):
                    params["customer_name"] = arguments["customer_name"]
                if arguments.get("rank_id"):
                    params["rank_id"] = arguments["rank_id"]
                r = client.get("/customers/", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_stores":
                params = {
                    "limit": arguments.get("limit", 100),
                    "page": arguments.get("page", 1),
                }
                r = client.get("/stores/", params=params)
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
