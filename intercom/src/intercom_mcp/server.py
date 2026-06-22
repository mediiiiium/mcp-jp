import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("intercom-mcp")
BASE_URL = "https://api.intercom.io"
INTERCOM_VERSION = "2.11"


def _client() -> httpx.Client:
    access_token = os.environ.get("INTERCOM_ACCESS_TOKEN")
    if not access_token:
        raise ValueError("INTERCOM_ACCESS_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Intercom-Version": INTERCOM_VERSION,
        },
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
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（デフォルト50）"},
                },
            },
        ),
        types.Tool(
            name="search_contacts",
            description="コンタクトをメール・名前で検索する",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "メールアドレスまたは名前で検索"},
                },
                "required": ["query"],
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
                    "name": {"type": "string", "description": "名前"},
                    "phone": {"type": "string", "description": "電話番号"},
                    "role": {"type": "string", "description": "役割: user / lead（デフォルト: user）"},
                },
                "required": ["email"],
            },
        ),
        types.Tool(
            name="list_conversations",
            description="カンバセーション（チャット）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（デフォルト20）"},
                    "open": {"type": "boolean", "description": "オープンな会話のみ取得（デフォルトtrue）"},
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "list_contacts":
        params = {"per_page": arguments.get("per_page", 50)}
        r = client.get("/contacts", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "search_contacts":
        payload = {
            "query": {
                "operator": "OR",
                "value": [
                    {"field": "email", "operator": "~", "value": arguments["query"]},
                    {"field": "name", "operator": "~", "value": arguments["query"]},
                ],
            }
        }
        r = client.post("/contacts/search", json=payload)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_contact":
        contact_id = arguments["contact_id"]
        r = client.get(f"/contacts/{contact_id}")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "create_contact":
        payload = {
            "email": arguments["email"],
            "role": arguments.get("role", "user"),
        }
        if arguments.get("name"):
            payload["name"] = arguments["name"]
        if arguments.get("phone"):
            payload["phone"] = arguments["phone"]
        r = client.post("/contacts", json=payload)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_conversations":
        params = {"per_page": arguments.get("per_page", 20)}
        if arguments.get("open", True):
            params["open"] = True
        r = client.get("/conversations", params=params)
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
