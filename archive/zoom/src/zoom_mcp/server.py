import os
import json
import base64
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("zoom-mcp")
ZOOM_API_BASE = "https://api.zoom.us/v2"
ZOOM_TOKEN_URL = "https://zoom.us/oauth/token"


def _get_access_token() -> str:
    account_id = os.environ.get("ZOOM_ACCOUNT_ID")
    client_id = os.environ.get("ZOOM_CLIENT_ID")
    client_secret = os.environ.get("ZOOM_CLIENT_SECRET")
    if not account_id:
        raise ValueError("ZOOM_ACCOUNT_ID が設定されていません")
    if not client_id:
        raise ValueError("ZOOM_CLIENT_ID が設定されていません")
    if not client_secret:
        raise ValueError("ZOOM_CLIENT_SECRET が設定されていません")
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    r = httpx.post(
        ZOOM_TOKEN_URL,
        params={"grant_type": "account_credentials", "account_id": account_id},
        headers={"Authorization": f"Basic {credentials}"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def _client() -> httpx.Client:
    token = _get_access_token()
    return httpx.Client(
        base_url=ZOOM_API_BASE,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_meetings",
            description="ミーティング一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ユーザーID（省略で 'me'）"},
                    "type": {"type": "string", "description": "ミーティングタイプ: scheduled / live / upcoming"},
                    "page_size": {"type": "integer", "description": "1ページあたりの件数（デフォルト30）"},
                },
            },
        ),
        types.Tool(
            name="get_meeting",
            description="ミーティングの詳細を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "meeting_id": {"type": "string", "description": "ミーティングID"},
                },
                "required": ["meeting_id"],
            },
        ),
        types.Tool(
            name="create_meeting",
            description="新しいミーティングを作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "ミーティングのタイトル"},
                    "start_time": {"type": "string", "description": "開始時刻（ISO8601形式、例: 2024-04-01T10:00:00Z）"},
                    "duration": {"type": "integer", "description": "会議時間（分）"},
                    "agenda": {"type": "string", "description": "ミーティングのアジェンダ"},
                    "user_id": {"type": "string", "description": "ホストのユーザーID（省略で 'me'）"},
                },
                "required": ["topic"],
            },
        ),
        types.Tool(
            name="list_recordings",
            description="クラウドレコーディング一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ユーザーID（省略で 'me'）"},
                    "from_date": {"type": "string", "description": "開始日（YYYY-MM-DD形式）"},
                    "to_date": {"type": "string", "description": "終了日（YYYY-MM-DD形式）"},
                },
            },
        ),
        types.Tool(
            name="list_users",
            description="アカウント内のユーザー一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "ステータス: active / inactive / pending"},
                    "page_size": {"type": "integer", "description": "1ページあたりの件数（デフォルト30）"},
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "list_meetings":
        user_id = arguments.get("user_id", "me")
        params = {"page_size": arguments.get("page_size", 30)}
        if arguments.get("type"):
            params["type"] = arguments["type"]
        r = client.get(f"/users/{user_id}/meetings", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_meeting":
        meeting_id = arguments["meeting_id"]
        r = client.get(f"/meetings/{meeting_id}")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "create_meeting":
        user_id = arguments.get("user_id", "me")
        payload = {
            "topic": arguments["topic"],
            "type": 2,  # scheduled meeting
        }
        if arguments.get("start_time"):
            payload["start_time"] = arguments["start_time"]
        if arguments.get("duration"):
            payload["duration"] = arguments["duration"]
        if arguments.get("agenda"):
            payload["agenda"] = arguments["agenda"]
        r = client.post(f"/users/{user_id}/meetings", json=payload)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_recordings":
        user_id = arguments.get("user_id", "me")
        params = {}
        if arguments.get("from_date"):
            params["from"] = arguments["from_date"]
        if arguments.get("to_date"):
            params["to"] = arguments["to_date"]
        r = client.get(f"/users/{user_id}/recordings", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_users":
        params = {"page_size": arguments.get("page_size", 30)}
        if arguments.get("status"):
            params["status"] = arguments["status"]
        r = client.get("/users", params=params)
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
