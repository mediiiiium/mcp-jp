import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("activecampaign-mcp")


def _client() -> httpx.Client:
    api_key = os.environ.get("ACTIVECAMPAIGN_API_KEY")
    base_url = os.environ.get("ACTIVECAMPAIGN_BASE_URL")
    if not api_key:
        raise ValueError("ACTIVECAMPAIGN_API_KEY が設定されていません")
    if not base_url:
        raise ValueError("ACTIVECAMPAIGN_BASE_URL が設定されていません（例: https://myaccount.api-us1.com）")
    return httpx.Client(
        base_url=f"{base_url.rstrip('/')}/api/3",
        headers={"Api-Token": api_key, "Content-Type": "application/json"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_contacts",
            description="コンタクト一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "メールアドレスで検索"},
                    "limit": {"type": "integer", "description": "取得件数（デフォルト20）"},
                    "offset": {"type": "integer", "description": "オフセット（デフォルト0）"},
                },
            },
        ),
        types.Tool(
            name="get_contact",
            description="コンタクトの詳細を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string", "description": "コンタクトID"},
                },
                "required": ["contact_id"],
            },
        ),
        types.Tool(
            name="create_contact",
            description="新しいコンタクトを作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "メールアドレス"},
                    "first_name": {"type": "string", "description": "名"},
                    "last_name": {"type": "string", "description": "姓"},
                    "phone": {"type": "string", "description": "電話番号"},
                },
                "required": ["email"],
            },
        ),
        types.Tool(
            name="list_lists",
            description="メーリングリスト一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（デフォルト20）"},
                },
            },
        ),
        types.Tool(
            name="list_campaigns",
            description="キャンペーン一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（デフォルト20）"},
                    "status": {"type": "integer", "description": "ステータス: 0=draft, 1=scheduled, 2=sending, 3=paused, 4=stopped, 5=complete"},
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "list_contacts":
        params = {
            "limit": arguments.get("limit", 20),
            "offset": arguments.get("offset", 0),
        }
        if arguments.get("email"):
            params["email"] = arguments["email"]
        r = client.get("/contacts", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_contact":
        contact_id = arguments["contact_id"]
        r = client.get(f"/contacts/{contact_id}")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "create_contact":
        contact_data = {"email": arguments["email"]}
        if arguments.get("first_name"):
            contact_data["firstName"] = arguments["first_name"]
        if arguments.get("last_name"):
            contact_data["lastName"] = arguments["last_name"]
        if arguments.get("phone"):
            contact_data["phone"] = arguments["phone"]
        r = client.post("/contacts", json={"contact": contact_data})
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_lists":
        params = {"limit": arguments.get("limit", 20)}
        r = client.get("/lists", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_campaigns":
        params = {"limit": arguments.get("limit", 20)}
        if arguments.get("status") is not None:
            params["filters[status]"] = arguments["status"]
        r = client.get("/campaigns", params=params)
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
