import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("clickup-mcp")
BASE_URL = "https://api.clickup.com/api/v2"


def _client() -> httpx.Client:
    api_token = os.environ.get("CLICKUP_API_TOKEN")
    if not api_token:
        raise ValueError("CLICKUP_API_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": api_token, "Content-Type": "application/json"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_teams",
            description="チーム（ワークスペース）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="list_spaces",
            description="チーム内のスペース一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "team_id": {"type": "string", "description": "チームID"},
                },
                "required": ["team_id"],
            },
        ),
        types.Tool(
            name="list_lists",
            description="スペース内のリスト一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "space_id": {"type": "string", "description": "スペースID"},
                },
                "required": ["space_id"],
            },
        ),
        types.Tool(
            name="list_tasks",
            description="リスト内のタスク一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_id": {"type": "string", "description": "リストID"},
                    "statuses": {"type": "array", "items": {"type": "string"}, "description": "ステータスでフィルタ"},
                    "assignees": {"type": "array", "items": {"type": "string"}, "description": "担当者IDでフィルタ"},
                    "page": {"type": "integer", "description": "ページ番号（デフォルト0）"},
                },
                "required": ["list_id"],
            },
        ),
        types.Tool(
            name="create_task",
            description="新しいタスクを作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_id": {"type": "string", "description": "リストID"},
                    "name": {"type": "string", "description": "タスク名"},
                    "description": {"type": "string", "description": "タスクの説明"},
                    "status": {"type": "string", "description": "ステータス"},
                    "priority": {"type": "integer", "description": "優先度: 1=Urgent, 2=High, 3=Normal, 4=Low"},
                    "due_date": {"type": "integer", "description": "期限日（Unixミリ秒タイムスタンプ）"},
                },
                "required": ["list_id", "name"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "get_teams":
        r = client.get("/team")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_spaces":
        team_id = arguments["team_id"]
        r = client.get(f"/team/{team_id}/space")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_lists":
        space_id = arguments["space_id"]
        r = client.get(f"/space/{space_id}/list")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_tasks":
        list_id = arguments["list_id"]
        params = {"page": arguments.get("page", 0)}
        if arguments.get("statuses"):
            params["statuses[]"] = arguments["statuses"]
        if arguments.get("assignees"):
            params["assignees[]"] = arguments["assignees"]
        r = client.get(f"/list/{list_id}/task", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "create_task":
        list_id = arguments["list_id"]
        payload = {"name": arguments["name"]}
        if arguments.get("description"):
            payload["description"] = arguments["description"]
        if arguments.get("status"):
            payload["status"] = arguments["status"]
        if arguments.get("priority"):
            payload["priority"] = arguments["priority"]
        if arguments.get("due_date"):
            payload["due_date"] = arguments["due_date"]
        r = client.post(f"/list/{list_id}/task", json=payload)
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
