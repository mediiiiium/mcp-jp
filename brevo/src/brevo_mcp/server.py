import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("brevo-mcp")
BASE_URL = "https://api.brevo.com/v3"


def _client() -> httpx.Client:
    api_key = os.environ.get("BREVO_API_KEY")
    if not api_key:
        raise ValueError("BREVO_API_KEY が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={"api-key": api_key, "Content-Type": "application/json", "Accept": "application/json"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_account",
            description="アカウント情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="send_email",
            description="メールを送信する",
            inputSchema={
                "type": "object",
                "properties": {
                    "to_email": {"type": "string", "description": "宛先メールアドレス"},
                    "to_name": {"type": "string", "description": "宛先名"},
                    "from_email": {"type": "string", "description": "送信元メールアドレス"},
                    "from_name": {"type": "string", "description": "送信元名"},
                    "subject": {"type": "string", "description": "件名"},
                    "html_content": {"type": "string", "description": "HTMLメール本文"},
                    "text_content": {"type": "string", "description": "テキストメール本文"},
                },
                "required": ["to_email", "subject"],
            },
        ),
        types.Tool(
            name="list_contacts",
            description="コンタクト一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（デフォルト50、最大1000）"},
                    "offset": {"type": "integer", "description": "オフセット（デフォルト0）"},
                    "sort": {"type": "string", "description": "ソート: asc / desc（更新日時）"},
                },
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
                    "list_ids": {"type": "array", "items": {"type": "integer"}, "description": "追加するリストのID一覧"},
                },
                "required": ["email"],
            },
        ),
        types.Tool(
            name="get_email_stats",
            description="メールキャンペーンの統計を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（デフォルト10）"},
                    "offset": {"type": "integer", "description": "オフセット（デフォルト0）"},
                    "status": {"type": "string", "description": "ステータス: draft / sent / queued / suspended / archive"},
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "get_account":
        r = client.get("/account")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "send_email":
        payload = {
            "to": [{"email": arguments["to_email"], "name": arguments.get("to_name", "")}],
            "subject": arguments["subject"],
            "sender": {
                "email": arguments.get("from_email", "noreply@example.com"),
                "name": arguments.get("from_name", ""),
            },
        }
        if arguments.get("html_content"):
            payload["htmlContent"] = arguments["html_content"]
        if arguments.get("text_content"):
            payload["textContent"] = arguments["text_content"]
        r = client.post("/smtp/email", json=payload)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_contacts":
        params = {
            "limit": arguments.get("limit", 50),
            "offset": arguments.get("offset", 0),
        }
        if arguments.get("sort"):
            params["sort"] = arguments["sort"]
        r = client.get("/contacts", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "create_contact":
        payload = {"email": arguments["email"]}
        attributes = {}
        if arguments.get("first_name"):
            attributes["FIRSTNAME"] = arguments["first_name"]
        if arguments.get("last_name"):
            attributes["LASTNAME"] = arguments["last_name"]
        if attributes:
            payload["attributes"] = attributes
        if arguments.get("list_ids"):
            payload["listIds"] = arguments["list_ids"]
        r = client.post("/contacts", json=payload)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_email_stats":
        params = {
            "limit": arguments.get("limit", 10),
            "offset": arguments.get("offset", 0),
        }
        if arguments.get("status"):
            params["status"] = arguments["status"]
        r = client.get("/emailCampaigns", params=params)
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
