import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("jooto-mcp")
BASE_URL = "https://app.jooto.com"


def _client() -> httpx.Client:
    api_key = os.environ.get("JOOTO_API_KEY")
    if not api_key:
        raise ValueError("JOOTO_API_KEY が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "X-Jooto-Api-Key": api_key,
            "Content-Type": "application/json",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_organizations",
            description="所属するオーガニゼーション（組織）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="list_boards",
            description="オーガニゼーション内のボード（プロジェクト）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "organization_id": {"type": "string", "description": "オーガニゼーションID"},
                    "page": {"type": "integer", "description": "ページ番号", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数", "default": 20},
                },
                "required": ["organization_id"],
            },
        ),
        types.Tool(
            name="list_tasks",
            description="ボード内のタスク一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "organization_id": {"type": "string", "description": "オーガニゼーションID"},
                    "board_id": {"type": "string", "description": "ボードID"},
                    "page": {"type": "integer", "description": "ページ番号", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数", "default": 20},
                    "assigned_user_id": {"type": "string", "description": "担当者IDで絞り込み"},
                },
                "required": ["organization_id", "board_id"],
            },
        ),
        types.Tool(
            name="create_task",
            description="新しいタスクを作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "organization_id": {"type": "string", "description": "オーガニゼーションID"},
                    "board_id": {"type": "string", "description": "ボードID"},
                    "name": {"type": "string", "description": "タスク名"},
                    "description": {"type": "string", "description": "タスクの詳細説明"},
                    "due_date": {"type": "string", "description": "期限日（YYYY-MM-DD形式）"},
                    "assigned_user_id": {"type": "string", "description": "担当者のユーザーID"},
                },
                "required": ["organization_id", "board_id", "name"],
            },
        ),
        types.Tool(
            name="get_task",
            description="タスクの詳細情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "organization_id": {"type": "string", "description": "オーガニゼーションID"},
                    "board_id": {"type": "string", "description": "ボードID"},
                    "task_id": {"type": "string", "description": "タスクID"},
                },
                "required": ["organization_id", "board_id", "task_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "list_organizations":
        r = client.get("/organizations")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_boards":
        org_id = arguments["organization_id"]
        params: dict = {
            "page": arguments.get("page", 1),
            "per_page": arguments.get("per_page", 20),
        }
        r = client.get(f"/organizations/{org_id}/boards", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_tasks":
        org_id = arguments["organization_id"]
        board_id = arguments["board_id"]
        params = {
            "page": arguments.get("page", 1),
            "per_page": arguments.get("per_page", 20),
        }
        if arguments.get("assigned_user_id"):
            params["assigned_user_id"] = arguments["assigned_user_id"]
        r = client.get(f"/organizations/{org_id}/boards/{board_id}/tasks", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "create_task":
        org_id = arguments["organization_id"]
        board_id = arguments["board_id"]
        payload: dict = {"name": arguments["name"]}
        if arguments.get("description"):
            payload["description"] = arguments["description"]
        if arguments.get("due_date"):
            payload["due_date"] = arguments["due_date"]
        if arguments.get("assigned_user_id"):
            payload["assigned_user_id"] = arguments["assigned_user_id"]
        r = client.post(f"/organizations/{org_id}/boards/{board_id}/tasks", json=payload)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_task":
        org_id = arguments["organization_id"]
        board_id = arguments["board_id"]
        task_id = arguments["task_id"]
        r = client.get(f"/organizations/{org_id}/boards/{board_id}/tasks/{task_id}")
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
