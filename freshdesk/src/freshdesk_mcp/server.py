import os
import base64
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("freshdesk-mcp")


def _client() -> httpx.Client:
    api_key = os.environ.get("FRESHDESK_API_KEY")
    subdomain = os.environ.get("FRESHDESK_SUBDOMAIN")
    if not api_key:
        raise ValueError("FRESHDESK_API_KEY が設定されていません")
    if not subdomain:
        raise ValueError("FRESHDESK_SUBDOMAIN が設定されていません")
    credentials = base64.b64encode(f"{api_key}:X".encode()).decode()
    return httpx.Client(
        base_url=f"https://{subdomain}.freshdesk.com/api/v2",
        headers={"Authorization": f"Basic {credentials}", "Content-Type": "application/json"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_tickets",
            description="チケット一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "integer", "description": "ステータス: 2=Open, 3=Pending, 4=Resolved, 5=Closed"},
                    "priority": {"type": "integer", "description": "優先度: 1=Low, 2=Medium, 3=High, 4=Urgent"},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（デフォルト30）"},
                    "page": {"type": "integer", "description": "ページ番号（デフォルト1）"},
                },
            },
        ),
        types.Tool(
            name="get_ticket",
            description="チケットの詳細を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "integer", "description": "チケットID"},
                },
                "required": ["ticket_id"],
            },
        ),
        types.Tool(
            name="create_ticket",
            description="新しいチケットを作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "subject": {"type": "string", "description": "チケットの件名"},
                    "description": {"type": "string", "description": "チケットの内容（HTML可）"},
                    "email": {"type": "string", "description": "問い合わせ元のメールアドレス"},
                    "priority": {"type": "integer", "description": "優先度: 1=Low, 2=Medium, 3=High, 4=Urgent"},
                    "status": {"type": "integer", "description": "ステータス: 2=Open, 3=Pending, 4=Resolved, 5=Closed"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "タグ一覧"},
                },
                "required": ["subject", "description", "email"],
            },
        ),
        types.Tool(
            name="list_contacts",
            description="コンタクト（顧客）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "メールアドレスで検索"},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（デフォルト30）"},
                    "page": {"type": "integer", "description": "ページ番号（デフォルト1）"},
                },
            },
        ),
        types.Tool(
            name="get_contact",
            description="コンタクトの詳細を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "integer", "description": "コンタクトID"},
                },
                "required": ["contact_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_tickets":
                params = {
                    "per_page": arguments.get("per_page", 30),
                    "page": arguments.get("page", 1),
                }
                if arguments.get("status"):
                    params["status"] = arguments["status"]
                if arguments.get("priority"):
                    params["priority"] = arguments["priority"]
                r = client.get("/tickets", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_ticket":
                ticket_id = arguments["ticket_id"]
                r = client.get(f"/tickets/{ticket_id}")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "create_ticket":
                payload = {
                    "subject": arguments["subject"],
                    "description": arguments["description"],
                    "email": arguments["email"],
                    "priority": arguments.get("priority", 2),
                    "status": arguments.get("status", 2),
                }
                if arguments.get("tags"):
                    payload["tags"] = arguments["tags"]
                r = client.post("/tickets", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_contacts":
                params = {
                    "per_page": arguments.get("per_page", 30),
                    "page": arguments.get("page", 1),
                }
                if arguments.get("email"):
                    params["email"] = arguments["email"]
                r = client.get("/contacts", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_contact":
                contact_id = arguments["contact_id"]
                r = client.get(f"/contacts/{contact_id}")
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
