import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("stripe-mcp")

BASE_URL = "https://api.stripe.com/v1"


def _client() -> httpx.Client:
    secret_key = os.environ.get("STRIPE_SECRET_KEY")
    if not secret_key:
        raise ValueError("STRIPE_SECRET_KEY が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {secret_key}"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_customers",
            description="Stripe の顧客一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "取得件数（最大100、デフォルト20）",
                        "default": 20,
                    },
                    "email": {
                        "type": "string",
                        "description": "メールアドレスで絞り込み",
                    },
                    "starting_after": {
                        "type": "string",
                        "description": "ページネーション用カーソル（前ページの最後の顧客ID）",
                    },
                },
            },
        ),
        types.Tool(
            name="get_customer",
            description="顧客IDを指定して Stripe の顧客情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "顧客ID（cus_ で始まるID）",
                    },
                },
                "required": ["customer_id"],
            },
        ),
        types.Tool(
            name="list_charges",
            description="Stripe の決済一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "取得件数（最大100、デフォルト20）",
                        "default": 20,
                    },
                    "customer": {
                        "type": "string",
                        "description": "顧客IDで絞り込み",
                    },
                    "created_gte": {
                        "type": "integer",
                        "description": "作成日時の開始（Unixタイムスタンプ）",
                    },
                    "created_lte": {
                        "type": "integer",
                        "description": "作成日時の終了（Unixタイムスタンプ）",
                    },
                    "starting_after": {
                        "type": "string",
                        "description": "ページネーション用カーソル",
                    },
                },
            },
        ),
        types.Tool(
            name="list_invoices",
            description="Stripe の請求書一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "取得件数（最大100、デフォルト20）",
                        "default": 20,
                    },
                    "customer": {
                        "type": "string",
                        "description": "顧客IDで絞り込み",
                    },
                    "status": {
                        "type": "string",
                        "description": "ステータスで絞り込み（draft, open, paid, uncollectible, void）",
                        "enum": ["draft", "open", "paid", "uncollectible", "void"],
                    },
                    "starting_after": {
                        "type": "string",
                        "description": "ページネーション用カーソル",
                    },
                },
            },
        ),
        types.Tool(
            name="list_subscriptions",
            description="Stripe のサブスクリプション一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "取得件数（最大100、デフォルト20）",
                        "default": 20,
                    },
                    "customer": {
                        "type": "string",
                        "description": "顧客IDで絞り込み",
                    },
                    "status": {
                        "type": "string",
                        "description": "ステータスで絞り込み（active, canceled, incomplete, past_due, trialing）",
                        "enum": ["active", "canceled", "incomplete", "incomplete_expired", "past_due", "trialing", "unpaid"],
                    },
                    "starting_after": {
                        "type": "string",
                        "description": "ページネーション用カーソル",
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "list_customers":
        params: dict = {"limit": arguments.get("limit", 20)}
        if arguments.get("email"):
            params["email"] = arguments["email"]
        if arguments.get("starting_after"):
            params["starting_after"] = arguments["starting_after"]
        r = client.get("/customers", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_customer":
        cid = arguments["customer_id"]
        r = client.get(f"/customers/{cid}")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_charges":
        params = {"limit": arguments.get("limit", 20)}
        if arguments.get("customer"):
            params["customer"] = arguments["customer"]
        if arguments.get("created_gte"):
            params["created[gte]"] = arguments["created_gte"]
        if arguments.get("created_lte"):
            params["created[lte]"] = arguments["created_lte"]
        if arguments.get("starting_after"):
            params["starting_after"] = arguments["starting_after"]
        r = client.get("/charges", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_invoices":
        params = {"limit": arguments.get("limit", 20)}
        if arguments.get("customer"):
            params["customer"] = arguments["customer"]
        if arguments.get("status"):
            params["status"] = arguments["status"]
        if arguments.get("starting_after"):
            params["starting_after"] = arguments["starting_after"]
        r = client.get("/invoices", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_subscriptions":
        params = {"limit": arguments.get("limit", 20)}
        if arguments.get("customer"):
            params["customer"] = arguments["customer"]
        if arguments.get("status"):
            params["status"] = arguments["status"]
        if arguments.get("starting_after"):
            params["starting_after"] = arguments["starting_after"]
        r = client.get("/subscriptions", params=params)
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
