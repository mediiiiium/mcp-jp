import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("payjp-mcp")

BASE_URL = "https://api.pay.jp/v1"


def _client() -> httpx.Client:
    secret_key = os.environ.get("PAYJP_SECRET_KEY")
    if not secret_key:
        raise ValueError("PAYJP_SECRET_KEY が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        auth=(secret_key, ""),
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_charges",
            description="決済（課金）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（最大100）", "default": 10},
                    "offset": {"type": "integer", "description": "スキップ件数", "default": 0},
                    "customer": {"type": "string", "description": "顧客IDで絞り込み"},
                    "since": {"type": "integer", "description": "UNIX タイムスタンプ（この日時以降）"},
                    "until": {"type": "integer", "description": "UNIX タイムスタンプ（この日時以前）"},
                },
            },
        ),
        types.Tool(
            name="get_charge",
            description="特定の決済（課金）の詳細を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "charge_id": {"type": "string", "description": "課金ID（ch_ で始まる）"},
                },
                "required": ["charge_id"],
            },
        ),
        types.Tool(
            name="refund_charge",
            description="決済を返金する",
            inputSchema={
                "type": "object",
                "properties": {
                    "charge_id": {"type": "string", "description": "課金ID（ch_ で始まる）"},
                    "amount": {"type": "integer", "description": "返金額（省略時は全額返金）"},
                },
                "required": ["charge_id"],
            },
        ),
        types.Tool(
            name="list_customers",
            description="顧客一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（最大100）", "default": 10},
                    "offset": {"type": "integer", "description": "スキップ件数", "default": 0},
                    "since": {"type": "integer", "description": "UNIX タイムスタンプ（この日時以降に作成）"},
                },
            },
        ),
        types.Tool(
            name="list_subscriptions",
            description="サブスクリプション（定期課金）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（最大100）", "default": 10},
                    "offset": {"type": "integer", "description": "スキップ件数", "default": 0},
                    "customer": {"type": "string", "description": "顧客IDで絞り込み"},
                    "plan": {"type": "string", "description": "プランIDで絞り込み"},
                    "status": {
                        "type": "string",
                        "description": "ステータスで絞り込み: trial / active / canceled / paused",
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "list_charges":
        params: dict = {}
        if arguments.get("limit") is not None:
            params["limit"] = arguments["limit"]
        if arguments.get("offset") is not None:
            params["offset"] = arguments["offset"]
        if arguments.get("customer"):
            params["customer"] = arguments["customer"]
        if arguments.get("since"):
            params["since"] = arguments["since"]
        if arguments.get("until"):
            params["until"] = arguments["until"]
        r = client.get("/charges", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_charge":
        r = client.get(f"/charges/{arguments['charge_id']}")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "refund_charge":
        body: dict = {}
        if arguments.get("amount") is not None:
            body["amount"] = arguments["amount"]
        r = client.post(f"/charges/{arguments['charge_id']}/refund", data=body)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_customers":
        params = {}
        if arguments.get("limit") is not None:
            params["limit"] = arguments["limit"]
        if arguments.get("offset") is not None:
            params["offset"] = arguments["offset"]
        if arguments.get("since"):
            params["since"] = arguments["since"]
        r = client.get("/customers", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_subscriptions":
        params = {}
        if arguments.get("limit") is not None:
            params["limit"] = arguments["limit"]
        if arguments.get("offset") is not None:
            params["offset"] = arguments["offset"]
        if arguments.get("customer"):
            params["customer"] = arguments["customer"]
        if arguments.get("plan"):
            params["plan"] = arguments["plan"]
        if arguments.get("status"):
            params["status"] = arguments["status"]
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
