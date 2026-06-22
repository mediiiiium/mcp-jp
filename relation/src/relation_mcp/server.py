import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("relation-mcp")


def _client() -> httpx.Client:
    subdomain = os.environ.get("RELATION_SUBDOMAIN")
    access_token = os.environ.get("RELATION_ACCESS_TOKEN")
    if not subdomain:
        raise ValueError("RELATION_SUBDOMAIN が設定されていません")
    if not access_token:
        raise ValueError("RELATION_ACCESS_TOKEN が設定されていません")
    return httpx.Client(
        base_url=f"https://{subdomain}.relationapp.jp/api/v2",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_message_boxes",
            description="受信箱（メールボックス）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="search_tickets",
            description="チケット（問い合わせ）を検索する",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_box_id": {"type": "integer", "description": "受信箱ID"},
                    "status": {"type": "string", "description": "ステータス: open（対応中）、resolved（解決済み）、pending（保留）"},
                    "keyword": {"type": "string", "description": "キーワード検索（件名・本文）"},
                    "assignee_id": {"type": "integer", "description": "担当者IDで絞り込み"},
                    "page": {"type": "integer", "description": "ページ番号", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（最大50）", "default": 20},
                },
                "required": ["message_box_id"],
            },
        ),
        types.Tool(
            name="get_ticket",
            description="チケットの詳細情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_box_id": {"type": "integer", "description": "受信箱ID"},
                    "ticket_id": {"type": "integer", "description": "チケットID"},
                },
                "required": ["message_box_id", "ticket_id"],
            },
        ),
        types.Tool(
            name="create_reply_memo",
            description="チケットに対応メモ（内部メモ）を作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_box_id": {"type": "integer", "description": "受信箱ID"},
                    "ticket_id": {"type": "integer", "description": "チケットID"},
                    "body": {"type": "string", "description": "メモの本文"},
                },
                "required": ["message_box_id", "ticket_id", "body"],
            },
        ),
        types.Tool(
            name="list_users",
            description="ユーザー（オペレーター）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_message_boxes":
                r = client.get("/message_boxes")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "search_tickets":
                mb_id = arguments["message_box_id"]
                payload: dict = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 20),
                }
                if arguments.get("status"):
                    payload["status"] = arguments["status"]
                if arguments.get("keyword"):
                    payload["keyword"] = arguments["keyword"]
                if arguments.get("assignee_id"):
                    payload["assignee_id"] = arguments["assignee_id"]
                r = client.post(f"/{mb_id}/tickets/search", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_ticket":
                mb_id = arguments["message_box_id"]
                ticket_id = arguments["ticket_id"]
                r = client.get(f"/{mb_id}/tickets/{ticket_id}")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "create_reply_memo":
                mb_id = arguments["message_box_id"]
                payload = {
                    "ticket_id": arguments["ticket_id"],
                    "body": arguments["body"],
                    "record_type": "memo",
                }
                r = client.post(f"/{mb_id}/records", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_users":
                r = client.get("/users")
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
