import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("chatwork-mcp")

BASE_URL = "https://api.chatwork.com/v2"


def _client() -> httpx.Client:
    token = os.environ.get("CHATWORK_API_TOKEN")
    if not token:
        raise ValueError("CHATWORK_API_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={"X-ChatWorkToken": token},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_me",
            description="自分のアカウント情報を取得する",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="list_rooms",
            description="参加しているチャットルーム一覧を取得する",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="get_room_messages",
            description="チャットルームのメッセージ一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "room_id": {"type": "string", "description": "ルームID"},
                    "force": {
                        "type": "integer",
                        "description": "1 を指定すると未読以外もすべて取得（デフォルト0=未読のみ）",
                        "default": 0,
                    },
                },
                "required": ["room_id"],
            },
        ),
        types.Tool(
            name="send_message",
            description="チャットルームにメッセージを送信する",
            inputSchema={
                "type": "object",
                "properties": {
                    "room_id": {"type": "string", "description": "送信先ルームID"},
                    "body": {"type": "string", "description": "メッセージ本文"},
                    "self_unread": {
                        "type": "integer",
                        "description": "送信したメッセージを自分の未読にする（1=未読、0=既読）",
                        "default": 0,
                    },
                },
                "required": ["room_id", "body"],
            },
        ),
        types.Tool(
            name="list_room_tasks",
            description="チャットルームのタスク一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "room_id": {"type": "string", "description": "ルームID"},
                    "status": {
                        "type": "string",
                        "description": "ステータス（open / done）",
                        "default": "open",
                    },
                },
                "required": ["room_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "get_me":
        r = client.get("/me")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_rooms":
        r = client.get("/rooms")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_room_messages":
        room_id = arguments["room_id"]
        params = {"force": arguments.get("force", 0)}
        r = client.get(f"/rooms/{room_id}/messages", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "send_message":
        room_id = arguments["room_id"]
        data = {
            "body": arguments["body"],
            "self_unread": arguments.get("self_unread", 0),
        }
        r = client.post(f"/rooms/{room_id}/messages", data=data)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_room_tasks":
        room_id = arguments["room_id"]
        params: dict = {}
        if arguments.get("status"):
            params["status"] = arguments["status"]
        r = client.get(f"/rooms/{room_id}/tasks", params=params)
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
