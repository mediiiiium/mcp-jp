import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("calendly-mcp")
BASE_URL = "https://api.calendly.com"


def _client() -> httpx.Client:
    access_token = os.environ.get("CALENDLY_ACCESS_TOKEN")
    if not access_token:
        raise ValueError("CALENDLY_ACCESS_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_current_user",
            description="現在のユーザー情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="list_event_types",
            description="イベントタイプ（予約ページ）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "organization": {"type": "string", "description": "組織URI（省略で個人アカウント）"},
                    "count": {"type": "integer", "description": "取得件数（デフォルト20）"},
                },
            },
        ),
        types.Tool(
            name="list_scheduled_events",
            description="スケジュール済みイベント（予約）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "organization": {"type": "string", "description": "組織URI"},
                    "min_start_time": {"type": "string", "description": "この日時以降のイベント（ISO8601形式）"},
                    "max_start_time": {"type": "string", "description": "この日時以前のイベント（ISO8601形式）"},
                    "status": {"type": "string", "description": "ステータス: active / canceled"},
                    "count": {"type": "integer", "description": "取得件数（デフォルト20）"},
                },
            },
        ),
        types.Tool(
            name="get_event",
            description="イベントの詳細を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_uuid": {"type": "string", "description": "イベントのUUID"},
                },
                "required": ["event_uuid"],
            },
        ),
        types.Tool(
            name="list_invitees",
            description="イベントの招待者一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_uuid": {"type": "string", "description": "イベントのUUID"},
                    "count": {"type": "integer", "description": "取得件数（デフォルト20）"},
                },
                "required": ["event_uuid"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "get_current_user":
        r = client.get("/users/me")
        r.raise_for_status()
        user_data = r.json()
        user_uri = user_data.get("resource", {}).get("uri", "")
        return [types.TextContent(type="text", text=json.dumps(user_data, ensure_ascii=False, indent=2))]

    elif name == "list_event_types":
        me_r = client.get("/users/me")
        me_r.raise_for_status()
        user_uri = me_r.json()["resource"]["uri"]
        params = {
            "user": user_uri,
            "count": arguments.get("count", 20),
        }
        if arguments.get("organization"):
            params["organization"] = arguments["organization"]
            del params["user"]
        r = client.get("/event_types", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_scheduled_events":
        me_r = client.get("/users/me")
        me_r.raise_for_status()
        user_uri = me_r.json()["resource"]["uri"]
        params = {
            "user": user_uri,
            "count": arguments.get("count", 20),
        }
        if arguments.get("organization"):
            params["organization"] = arguments["organization"]
            del params["user"]
        if arguments.get("min_start_time"):
            params["min_start_time"] = arguments["min_start_time"]
        if arguments.get("max_start_time"):
            params["max_start_time"] = arguments["max_start_time"]
        if arguments.get("status"):
            params["status"] = arguments["status"]
        r = client.get("/scheduled_events", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_event":
        event_uuid = arguments["event_uuid"]
        r = client.get(f"/scheduled_events/{event_uuid}")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_invitees":
        event_uuid = arguments["event_uuid"]
        params = {"count": arguments.get("count", 20)}
        r = client.get(f"/scheduled_events/{event_uuid}/invitees", params=params)
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
