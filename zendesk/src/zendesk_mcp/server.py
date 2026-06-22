import os
import base64
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("zendesk-mcp")


def _client() -> tuple[httpx.Client, str]:
    email = os.environ.get("ZENDESK_EMAIL")
    api_token = os.environ.get("ZENDESK_API_TOKEN")
    subdomain = os.environ.get("ZENDESK_SUBDOMAIN")
    if not email:
        raise ValueError("ZENDESK_EMAIL が設定されていません")
    if not api_token:
        raise ValueError("ZENDESK_API_TOKEN が設定されていません")
    if not subdomain:
        raise ValueError("ZENDESK_SUBDOMAIN が設定されていません")
    credentials = base64.b64encode(f"{email}/token:{api_token}".encode()).decode()
    client = httpx.Client(
        base_url=f"https://{subdomain}.zendesk.com/api/v2",
        headers={"Authorization": f"Basic {credentials}", "Content-Type": "application/json"},
        timeout=30,
    )
    return client, subdomain


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_tickets",
            description="Zendesk のチケット一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "sort_by": {
                        "type": "string",
                        "description": "ソート項目（created_at, updated_at, status, priority）",
                        "enum": ["created_at", "updated_at", "status", "priority", "id"],
                        "default": "updated_at",
                    },
                    "sort_order": {
                        "type": "string",
                        "description": "ソート方向（asc: 昇順, desc: 降順）",
                        "enum": ["asc", "desc"],
                        "default": "desc",
                    },
                    "page": {
                        "type": "integer",
                        "description": "ページ番号（デフォルト: 1）",
                        "default": 1,
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "1ページあたりの件数（最大100、デフォルト25）",
                        "default": 25,
                    },
                },
            },
        ),
        types.Tool(
            name="get_ticket",
            description="チケットIDを指定して Zendesk チケットの詳細を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "integer",
                        "description": "チケットID",
                    },
                },
                "required": ["ticket_id"],
            },
        ),
        types.Tool(
            name="create_ticket",
            description="Zendesk に新しいサポートチケットを作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "subject": {
                        "type": "string",
                        "description": "チケットの件名",
                    },
                    "comment_body": {
                        "type": "string",
                        "description": "最初のコメント（問い合わせ内容）",
                    },
                    "priority": {
                        "type": "string",
                        "description": "優先度（urgent: 緊急, high: 高, normal: 通常, low: 低）",
                        "enum": ["urgent", "high", "normal", "low"],
                        "default": "normal",
                    },
                    "type": {
                        "type": "string",
                        "description": "チケット種別（question: 質問, problem: 問題, incident: インシデント, task: タスク）",
                        "enum": ["question", "problem", "incident", "task"],
                    },
                    "assignee_id": {
                        "type": "integer",
                        "description": "担当エージェントのID",
                    },
                    "group_id": {
                        "type": "integer",
                        "description": "グループID",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "タグのリスト",
                    },
                },
                "required": ["subject", "comment_body"],
            },
        ),
        types.Tool(
            name="search_tickets",
            description="Zendesk のチケットをキーワードやステータスで検索する",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "検索クエリ（例: 'status:open priority:high', 'type:ticket 問い合わせ', 'created>2024-01-01'）",
                    },
                    "sort_by": {
                        "type": "string",
                        "description": "ソート項目（created_at, updated_at, priority, status）",
                        "default": "updated_at",
                    },
                    "sort_order": {
                        "type": "string",
                        "description": "ソート方向（asc / desc）",
                        "enum": ["asc", "desc"],
                        "default": "desc",
                    },
                    "page": {
                        "type": "integer",
                        "description": "ページ番号",
                        "default": 1,
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="list_users",
            description="Zendesk のユーザー（エージェント・エンドユーザー）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "role": {
                        "type": "string",
                        "description": "ロールで絞り込み（agent: エージェント, end-user: エンドユーザー, admin: 管理者）",
                        "enum": ["agent", "end-user", "admin"],
                    },
                    "page": {
                        "type": "integer",
                        "description": "ページ番号（デフォルト: 1）",
                        "default": 1,
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "1ページあたりの件数（最大100、デフォルト25）",
                        "default": 25,
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client, _ = _client()

    if name == "list_tickets":
        params: dict = {
            "sort_by": arguments.get("sort_by", "updated_at"),
            "sort_order": arguments.get("sort_order", "desc"),
            "page": arguments.get("page", 1),
            "per_page": arguments.get("per_page", 25),
        }
        r = client.get("/tickets.json", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_ticket":
        tid = arguments["ticket_id"]
        r = client.get(f"/tickets/{tid}.json")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "create_ticket":
        ticket: dict = {
            "subject": arguments["subject"],
            "comment": {"body": arguments["comment_body"]},
            "priority": arguments.get("priority", "normal"),
        }
        if arguments.get("type"):
            ticket["type"] = arguments["type"]
        if arguments.get("assignee_id"):
            ticket["assignee_id"] = arguments["assignee_id"]
        if arguments.get("group_id"):
            ticket["group_id"] = arguments["group_id"]
        if arguments.get("tags"):
            ticket["tags"] = arguments["tags"]
        r = client.post("/tickets.json", content=json.dumps({"ticket": ticket}))
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "search_tickets":
        params = {
            "query": arguments["query"],
            "sort_by": arguments.get("sort_by", "updated_at"),
            "sort_order": arguments.get("sort_order", "desc"),
            "page": arguments.get("page", 1),
        }
        r = client.get("/search.json", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_users":
        params = {
            "page": arguments.get("page", 1),
            "per_page": arguments.get("per_page", 25),
        }
        if arguments.get("role"):
            params["role"] = arguments["role"]
        r = client.get("/users.json", params=params)
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
