import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("mazrica-mcp")

BASE_URL = "https://senses-open-api.mazrica.com/v1"


def _client() -> httpx.Client:
    api_key = os.environ.get("MAZRICA_API_KEY")
    if not api_key:
        raise ValueError("MAZRICA_API_KEY が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "X-Api-Key": api_key,
            "Content-Type": "application/json",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_customers",
            description="取引先（顧客企業）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり）", "default": 1},
                    "name": {"type": "string", "description": "取引先名で絞り込み（部分一致）"},
                },
            },
        ),
        types.Tool(
            name="create_customer",
            description="新しい取引先を登録する",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "取引先名（必須）"},
                    "phone": {"type": "string", "description": "電話番号"},
                    "website": {"type": "string", "description": "Webサイト URL"},
                    "address": {"type": "string", "description": "住所"},
                    "memo": {"type": "string", "description": "メモ"},
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="list_deals",
            description="案件（商談）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり）", "default": 1},
                    "name": {"type": "string", "description": "案件名で絞り込み（部分一致）"},
                    "customer_id": {"type": "string", "description": "取引先IDで絞り込み"},
                },
            },
        ),
        types.Tool(
            name="create_deal",
            description="新しい案件（商談）を登録する",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "案件名（必須）"},
                    "customer_id": {"type": "string", "description": "取引先ID"},
                    "expected_amount": {"type": "number", "description": "受注予定金額"},
                    "expected_close_date": {"type": "string", "description": "受注予定日（YYYY-MM-DD）"},
                    "memo": {"type": "string", "description": "メモ"},
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="list_users",
            description="ユーザー（営業担当者）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり）", "default": 1},
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_customers":
                params: dict = {"page": arguments.get("page", 1)}
                if arguments.get("name"):
                    params["name"] = arguments["name"]
                r = client.get("/customers", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "create_customer":
                payload = {k: v for k, v in arguments.items() if v is not None}
                r = client.post("/customers", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_deals":
                params = {"page": arguments.get("page", 1)}
                if arguments.get("name"):
                    params["name"] = arguments["name"]
                if arguments.get("customer_id"):
                    params["customer_id"] = arguments["customer_id"]
                r = client.get("/deals", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "create_deal":
                payload = {k: v for k, v in arguments.items() if v is not None}
                r = client.post("/deals", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_users":
                params = {"page": arguments.get("page", 1)}
                r = client.get("/users", params=params)
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
