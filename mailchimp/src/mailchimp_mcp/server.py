import os
import json
import base64
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("mailchimp-mcp")


def _client() -> httpx.Client:
    api_key = os.environ.get("MAILCHIMP_API_KEY")
    server_prefix = os.environ.get("MAILCHIMP_SERVER_PREFIX")
    if not api_key:
        raise ValueError("MAILCHIMP_API_KEY が設定されていません")
    if not server_prefix:
        # Extract server prefix from API key (format: key-us1)
        if "-" in api_key:
            server_prefix = api_key.split("-")[-1]
        else:
            raise ValueError("MAILCHIMP_SERVER_PREFIX が設定されていません（例: us1）")
    credentials = base64.b64encode(f"anystring:{api_key}".encode()).decode()
    return httpx.Client(
        base_url=f"https://{server_prefix}.api.mailchimp.com/3.0",
        headers={"Authorization": f"Basic {credentials}", "Content-Type": "application/json"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_account_info",
            description="アカウント情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="list_audiences",
            description="オーディエンス（メーリングリスト）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "count": {"type": "integer", "description": "取得件数（デフォルト10）"},
                },
            },
        ),
        types.Tool(
            name="list_members",
            description="オーディエンスのメンバー一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_id": {"type": "string", "description": "オーディエンス（リスト）ID"},
                    "status": {"type": "string", "description": "ステータス: subscribed / unsubscribed / cleaned / pending"},
                    "count": {"type": "integer", "description": "取得件数（デフォルト50）"},
                },
                "required": ["list_id"],
            },
        ),
        types.Tool(
            name="add_member",
            description="オーディエンスにメンバーを追加する",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_id": {"type": "string", "description": "オーディエンス（リスト）ID"},
                    "email_address": {"type": "string", "description": "メールアドレス"},
                    "status": {"type": "string", "description": "ステータス: subscribed / pending（デフォルト: subscribed）"},
                    "first_name": {"type": "string", "description": "名"},
                    "last_name": {"type": "string", "description": "姓"},
                },
                "required": ["list_id", "email_address"],
            },
        ),
        types.Tool(
            name="list_campaigns",
            description="キャンペーン一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "ステータス: save / paused / schedule / sending / sent"},
                    "count": {"type": "integer", "description": "取得件数（デフォルト10）"},
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "get_account_info":
        r = client.get("/")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_audiences":
        params = {"count": arguments.get("count", 10)}
        r = client.get("/lists", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_members":
        list_id = arguments["list_id"]
        params = {"count": arguments.get("count", 50)}
        if arguments.get("status"):
            params["status"] = arguments["status"]
        r = client.get(f"/lists/{list_id}/members", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "add_member":
        list_id = arguments["list_id"]
        payload = {
            "email_address": arguments["email_address"],
            "status": arguments.get("status", "subscribed"),
        }
        merge_fields = {}
        if arguments.get("first_name"):
            merge_fields["FNAME"] = arguments["first_name"]
        if arguments.get("last_name"):
            merge_fields["LNAME"] = arguments["last_name"]
        if merge_fields:
            payload["merge_fields"] = merge_fields
        r = client.post(f"/lists/{list_id}/members", json=payload)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_campaigns":
        params = {"count": arguments.get("count", 10)}
        if arguments.get("status"):
            params["status"] = arguments["status"]
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
