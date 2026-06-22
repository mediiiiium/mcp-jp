import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("sendgrid-mcp")

BASE_URL = "https://api.sendgrid.com/v3"


def _client() -> httpx.Client:
    api_key = os.environ.get("SENDGRID_API_KEY")
    if not api_key:
        raise ValueError("SENDGRID_API_KEY が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="send_email",
            description="SendGrid でメールを送信する",
            inputSchema={
                "type": "object",
                "properties": {
                    "to_email": {
                        "type": "string",
                        "description": "送信先メールアドレス",
                    },
                    "to_name": {
                        "type": "string",
                        "description": "送信先の名前（任意）",
                    },
                    "from_email": {
                        "type": "string",
                        "description": "送信元メールアドレス（送信者確認済みのアドレス）",
                    },
                    "from_name": {
                        "type": "string",
                        "description": "送信元の名前（任意）",
                    },
                    "subject": {
                        "type": "string",
                        "description": "件名",
                    },
                    "text_content": {
                        "type": "string",
                        "description": "テキスト形式の本文",
                    },
                    "html_content": {
                        "type": "string",
                        "description": "HTML形式の本文（任意）",
                    },
                },
                "required": ["to_email", "from_email", "subject", "text_content"],
            },
        ),
        types.Tool(
            name="get_stats",
            description="SendGrid のメール送信統計を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "開始日（YYYY-MM-DD形式）",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "終了日（YYYY-MM-DD形式）",
                    },
                    "aggregated_by": {
                        "type": "string",
                        "description": "集計単位（day: 日別, week: 週別, month: 月別）",
                        "enum": ["day", "week", "month"],
                        "default": "day",
                    },
                },
                "required": ["start_date"],
            },
        ),
        types.Tool(
            name="list_bounces",
            description="バウンス（送信失敗）メールアドレス一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_time": {
                        "type": "integer",
                        "description": "開始日時（Unixタイムスタンプ）",
                    },
                    "end_time": {
                        "type": "integer",
                        "description": "終了日時（Unixタイムスタンプ）",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "取得件数（デフォルト25）",
                        "default": 25,
                    },
                    "offset": {
                        "type": "integer",
                        "description": "取得開始位置",
                        "default": 0,
                    },
                },
            },
        ),
        types.Tool(
            name="list_unsubscribes",
            description="配信停止（グローバル配信停止）メールアドレス一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_time": {
                        "type": "integer",
                        "description": "開始日時（Unixタイムスタンプ）",
                    },
                    "end_time": {
                        "type": "integer",
                        "description": "終了日時（Unixタイムスタンプ）",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "取得件数（デフォルト25）",
                        "default": 25,
                    },
                    "offset": {
                        "type": "integer",
                        "description": "取得開始位置",
                        "default": 0,
                    },
                },
            },
        ),
        types.Tool(
            name="list_templates",
            description="SendGrid の動的テンプレート一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "generations": {
                        "type": "string",
                        "description": "テンプレート世代（dynamic: 動的テンプレートのみ）",
                        "default": "dynamic",
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "取得件数（デフォルト10）",
                        "default": 10,
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "send_email":
                to_addr: dict = {"email": arguments["to_email"]}
                if arguments.get("to_name"):
                    to_addr["name"] = arguments["to_name"]
                from_addr: dict = {"email": arguments["from_email"]}
                if arguments.get("from_name"):
                    from_addr["name"] = arguments["from_name"]
                content = [{"type": "text/plain", "value": arguments["text_content"]}]
                if arguments.get("html_content"):
                    content.append({"type": "text/html", "value": arguments["html_content"]})
                body = {
                    "personalizations": [{"to": [to_addr]}],
                    "from": from_addr,
                    "subject": arguments["subject"],
                    "content": content,
                }
                r = client.post("/mail/send", content=json.dumps(body))
                r.raise_for_status()
                return format_response({"status": "sent", "status_code": r.status_code})

            elif name == "get_stats":
                params: dict = {
                    "start_date": arguments["start_date"],
                    "aggregated_by": arguments.get("aggregated_by", "day"),
                }
                if arguments.get("end_date"):
                    params["end_date"] = arguments["end_date"]
                r = client.get("/stats", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_bounces":
                params = {
                    "limit": arguments.get("limit", 25),
                    "offset": arguments.get("offset", 0),
                }
                if arguments.get("start_time"):
                    params["start_time"] = arguments["start_time"]
                if arguments.get("end_time"):
                    params["end_time"] = arguments["end_time"]
                r = client.get("/suppression/bounces", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_unsubscribes":
                params = {
                    "limit": arguments.get("limit", 25),
                    "offset": arguments.get("offset", 0),
                }
                if arguments.get("start_time"):
                    params["start_time"] = arguments["start_time"]
                if arguments.get("end_time"):
                    params["end_time"] = arguments["end_time"]
                r = client.get("/suppression/unsubscribes", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_templates":
                params = {
                    "generations": arguments.get("generations", "dynamic"),
                    "page_size": arguments.get("page_size", 10),
                }
                r = client.get("/templates", params=params)
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
