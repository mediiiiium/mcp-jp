import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("asana-mcp")
BASE_URL = "https://app.asana.com/api/1.0"


def _client() -> httpx.Client:
    token = os.environ.get("ASANA_ACCESS_TOKEN")
    if not token:
        raise ValueError("ASANA_ACCESS_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_workspaces",
            description="ワークスペース一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="list_projects",
            description="ワークスペース内のプロジェクト一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_gid": {"type": "string", "description": "ワークスペースのGID"},
                    "archived": {"type": "boolean", "description": "アーカイブ済みを含む（デフォルトfalse）"},
                },
                "required": ["workspace_gid"],
            },
        ),
        types.Tool(
            name="list_tasks",
            description="プロジェクト内のタスク一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_gid": {"type": "string", "description": "プロジェクトのGID"},
                    "completed_since": {"type": "string", "description": "この日時以降に完了したタスクを含む（ISO8601形式）"},
                },
                "required": ["project_gid"],
            },
        ),
        types.Tool(
            name="get_task",
            description="タスクの詳細を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_gid": {"type": "string", "description": "タスクのGID"},
                },
                "required": ["task_gid"],
            },
        ),
        types.Tool(
            name="create_task",
            description="新しいタスクを作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_gid": {"type": "string", "description": "ワークスペースのGID"},
                    "name": {"type": "string", "description": "タスク名"},
                    "notes": {"type": "string", "description": "タスクの説明"},
                    "project_gid": {"type": "string", "description": "追加するプロジェクトのGID"},
                    "due_on": {"type": "string", "description": "期限日（YYYY-MM-DD形式）"},
                    "assignee": {"type": "string", "description": "担当者のGIDまたは'me'"},
                },
                "required": ["workspace_gid", "name"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "list_workspaces":
        r = client.get("/workspaces")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_projects":
        params = {
            "workspace": arguments["workspace_gid"],
            "archived": arguments.get("archived", False),
        }
        r = client.get("/projects", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_tasks":
        params = {"project": arguments["project_gid"]}
        if arguments.get("completed_since"):
            params["completed_since"] = arguments["completed_since"]
        r = client.get("/tasks", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_task":
        task_gid = arguments["task_gid"]
        r = client.get(f"/tasks/{task_gid}")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "create_task":
        task_data = {
            "workspace": arguments["workspace_gid"],
            "name": arguments["name"],
        }
        if arguments.get("notes"):
            task_data["notes"] = arguments["notes"]
        if arguments.get("project_gid"):
            task_data["projects"] = [arguments["project_gid"]]
        if arguments.get("due_on"):
            task_data["due_on"] = arguments["due_on"]
        if arguments.get("assignee"):
            task_data["assignee"] = arguments["assignee"]
        r = client.post("/tasks", json={"data": task_data})
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
