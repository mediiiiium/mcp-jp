import os
import base64
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("twilio-mcp")

BASE_URL = "https://api.twilio.com/2010-04-01"


def _client() -> tuple[httpx.Client, str]:
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    if not account_sid:
        raise ValueError("TWILIO_ACCOUNT_SID が設定されていません")
    if not auth_token:
        raise ValueError("TWILIO_AUTH_TOKEN が設定されていません")
    credentials = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()
    client = httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Basic {credentials}"},
        timeout=30,
    )
    return client, account_sid


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="send_sms",
            description="Twilio で SMS メッセージを送信する",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "送信先電話番号（E.164形式、例: +819012345678）",
                    },
                    "from_number": {
                        "type": "string",
                        "description": "送信元 Twilio 電話番号（E.164形式）",
                    },
                    "body": {
                        "type": "string",
                        "description": "SMS 本文",
                    },
                },
                "required": ["to", "from_number", "body"],
            },
        ),
        types.Tool(
            name="list_messages",
            description="送受信した SMS メッセージ一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "宛先番号で絞り込み",
                    },
                    "from_number": {
                        "type": "string",
                        "description": "送信元番号で絞り込み",
                    },
                    "date_sent": {
                        "type": "string",
                        "description": "送信日で絞り込み（YYYY-MM-DD形式）",
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "取得件数（最大1000、デフォルト20）",
                        "default": 20,
                    },
                },
            },
        ),
        types.Tool(
            name="get_message",
            description="メッセージSIDを指定してSMSの詳細を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_sid": {
                        "type": "string",
                        "description": "メッセージSID（SM で始まるID）",
                    },
                },
                "required": ["message_sid"],
            },
        ),
        types.Tool(
            name="list_phone_numbers",
            description="Twilio アカウントの電話番号一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_size": {
                        "type": "integer",
                        "description": "取得件数（デフォルト20）",
                        "default": 20,
                    },
                },
            },
        ),
        types.Tool(
            name="get_account",
            description="Twilio アカウント情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client, account_sid = _client()

    if name == "send_sms":
        data = {
            "To": arguments["to"],
            "From": arguments["from_number"],
            "Body": arguments["body"],
        }
        r = client.post(
            f"/Accounts/{account_sid}/Messages.json",
            data=data,
        )
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_messages":
        params: dict = {"PageSize": arguments.get("page_size", 20)}
        if arguments.get("to"):
            params["To"] = arguments["to"]
        if arguments.get("from_number"):
            params["From"] = arguments["from_number"]
        if arguments.get("date_sent"):
            params["DateSent"] = arguments["date_sent"]
        r = client.get(f"/Accounts/{account_sid}/Messages.json", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_message":
        sid = arguments["message_sid"]
        r = client.get(f"/Accounts/{account_sid}/Messages/{sid}.json")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_phone_numbers":
        params = {"PageSize": arguments.get("page_size", 20)}
        r = client.get(f"/Accounts/{account_sid}/IncomingPhoneNumbers.json", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_account":
        r = client.get(f"/Accounts/{account_sid}.json")
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
