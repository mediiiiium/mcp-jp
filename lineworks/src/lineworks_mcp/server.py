import os
import json
import time
import httpx
import jwt
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("lineworks-mcp")
BASE_URL = "https://www.worksapis.com/v1.0"
AUTH_URL = "https://auth.worksmobile.com/oauth2/v2.0/token"


def _get_access_token() -> str:
    client_id = os.environ.get("LINEWORKS_CLIENT_ID")
    client_secret = os.environ.get("LINEWORKS_CLIENT_SECRET")
    service_account_id = os.environ.get("LINEWORKS_SERVICE_ACCOUNT_ID")
    private_key = os.environ.get("LINEWORKS_PRIVATE_KEY", "").replace("\\n", "\n")

    if not all([client_id, client_secret, service_account_id, private_key]):
        raise ValueError(
            "LINEWORKS_CLIENT_ID, LINEWORKS_CLIENT_SECRET, "
            "LINEWORKS_SERVICE_ACCOUNT_ID, LINEWORKS_PRIVATE_KEY が必要です"
        )

    now = int(time.time())
    payload = {
        "iss": client_id,
        "sub": service_account_id,
        "iat": now,
        "exp": now + 3600,
    }
    assertion = jwt.encode(payload, private_key, algorithm="RS256")

    r = httpx.post(
        AUTH_URL,
        data={
            "assertion": assertion,
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "bot user.read",
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def _client() -> httpx.Client:
    token = _get_access_token()
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )


def _bot_id() -> str:
    bot_id = os.environ.get("LINEWORKS_BOT_ID")
    if not bot_id:
        raise ValueError("LINEWORKS_BOT_ID が設定されていません")
    return bot_id


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_channels",
            description="Bot が参加しているトークルーム（チャンネル）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（最大100）", "default": 20},
                },
            },
        ),
        types.Tool(
            name="send_channel_message",
            description="トークルームにテキストメッセージを送信する",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {"type": "string", "description": "トークルームID"},
                    "text": {"type": "string", "description": "送信するメッセージ本文"},
                },
                "required": ["channel_id", "text"],
            },
        ),
        types.Tool(
            name="send_user_message",
            description="特定のユーザーにダイレクトメッセージを送信する",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "送信先ユーザーID"},
                    "text": {"type": "string", "description": "送信するメッセージ本文"},
                },
                "required": ["user_id", "text"],
            },
        ),
        types.Tool(
            name="list_members",
            description="テナントのメンバー（ユーザー）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（最大100）", "default": 20},
                    "cursor": {"type": "string", "description": "ページネーションカーソル"},
                },
            },
        ),
        types.Tool(
            name="get_member",
            description="特定のメンバー（ユーザー）の詳細情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ユーザーID"},
                },
                "required": ["user_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()
    bot_id = _bot_id()

    if name == "list_channels":
        params = {"limit": arguments.get("limit", 20)}
        r = client.get(f"/bots/{bot_id}/channels", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "send_channel_message":
        payload = {
            "content": {
                "type": "text",
                "text": arguments["text"],
            }
        }
        r = client.post(f"/bots/{bot_id}/channels/{arguments['channel_id']}/messages", json=payload)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "send_user_message":
        payload = {
            "content": {
                "type": "text",
                "text": arguments["text"],
            }
        }
        r = client.post(f"/bots/{bot_id}/users/{arguments['user_id']}/messages", json=payload)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_members":
        params: dict = {"limit": arguments.get("limit", 20)}
        if arguments.get("cursor"):
            params["cursor"] = arguments["cursor"]
        r = client.get("/users", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_member":
        r = client.get(f"/users/{arguments['user_id']}")
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
