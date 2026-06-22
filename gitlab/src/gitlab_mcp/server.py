import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("gitlab-mcp")


def _client() -> httpx.Client:
    token = os.environ.get("GITLAB_ACCESS_TOKEN")
    if not token:
        raise ValueError("GITLAB_ACCESS_TOKEN が設定されていません")
    base_url = os.environ.get("GITLAB_BASE_URL", "https://gitlab.com/api/v4")
    return httpx.Client(
        base_url=base_url,
        headers={"PRIVATE-TOKEN": token, "Content-Type": "application/json"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_projects",
            description="プロジェクト一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": "プロジェクト名で検索"},
                    "owned": {"type": "boolean", "description": "自分が所有するプロジェクトのみ"},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（デフォルト20）"},
                },
            },
        ),
        types.Tool(
            name="list_issues",
            description="プロジェクトのイシュー一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "プロジェクトID（数値またはnamespace/projectの形式）"},
                    "state": {"type": "string", "description": "状態: opened / closed / all"},
                    "labels": {"type": "string", "description": "カンマ区切りのラベル"},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（デフォルト20）"},
                },
                "required": ["project_id"],
            },
        ),
        types.Tool(
            name="get_issue",
            description="イシューの詳細を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "プロジェクトID"},
                    "issue_iid": {"type": "integer", "description": "イシューの内部ID（IID）"},
                },
                "required": ["project_id", "issue_iid"],
            },
        ),
        types.Tool(
            name="create_issue",
            description="新しいイシューを作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "プロジェクトID"},
                    "title": {"type": "string", "description": "イシューのタイトル"},
                    "description": {"type": "string", "description": "イシューの説明"},
                    "labels": {"type": "string", "description": "カンマ区切りのラベル"},
                    "assignee_ids": {"type": "array", "items": {"type": "integer"}, "description": "担当者のユーザーID一覧"},
                },
                "required": ["project_id", "title"],
            },
        ),
        types.Tool(
            name="list_merge_requests",
            description="プロジェクトのマージリクエスト一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "プロジェクトID"},
                    "state": {"type": "string", "description": "状態: opened / closed / merged / all"},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（デフォルト20）"},
                },
                "required": ["project_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "list_projects":
        params = {"per_page": arguments.get("per_page", 20)}
        if arguments.get("search"):
            params["search"] = arguments["search"]
        if arguments.get("owned"):
            params["owned"] = arguments["owned"]
        r = client.get("/projects", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_issues":
        project_id = arguments["project_id"]
        params = {"per_page": arguments.get("per_page", 20)}
        if arguments.get("state"):
            params["state"] = arguments["state"]
        if arguments.get("labels"):
            params["labels"] = arguments["labels"]
        r = client.get(f"/projects/{project_id}/issues", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_issue":
        project_id = arguments["project_id"]
        issue_iid = arguments["issue_iid"]
        r = client.get(f"/projects/{project_id}/issues/{issue_iid}")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "create_issue":
        project_id = arguments["project_id"]
        payload = {"title": arguments["title"]}
        if arguments.get("description"):
            payload["description"] = arguments["description"]
        if arguments.get("labels"):
            payload["labels"] = arguments["labels"]
        if arguments.get("assignee_ids"):
            payload["assignee_ids"] = arguments["assignee_ids"]
        r = client.post(f"/projects/{project_id}/issues", json=payload)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_merge_requests":
        project_id = arguments["project_id"]
        params = {"per_page": arguments.get("per_page", 20)}
        if arguments.get("state"):
            params["state"] = arguments["state"]
        r = client.get(f"/projects/{project_id}/merge_requests", params=params)
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
