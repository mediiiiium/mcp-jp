import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("sentry-mcp")
BASE_URL = "https://sentry.io/api/0"


def _client() -> httpx.Client:
    auth_token = os.environ.get("SENTRY_AUTH_TOKEN")
    if not auth_token:
        raise ValueError("SENTRY_AUTH_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
        timeout=30,
    )


def _org() -> str:
    org = os.environ.get("SENTRY_ORG")
    if not org:
        raise ValueError("SENTRY_ORG が設定されていません")
    return org


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_projects",
            description="プロジェクト一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="list_issues",
            description="イシュー（エラー）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_slug": {"type": "string", "description": "プロジェクトスラッグ"},
                    "query": {"type": "string", "description": "検索クエリ（例: is:unresolved）"},
                    "limit": {"type": "integer", "description": "取得件数（デフォルト25）"},
                },
                "required": ["project_slug"],
            },
        ),
        types.Tool(
            name="get_issue",
            description="イシューの詳細を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_id": {"type": "string", "description": "イシューID"},
                },
                "required": ["issue_id"],
            },
        ),
        types.Tool(
            name="update_issue",
            description="イシューのステータスを更新する",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_id": {"type": "string", "description": "イシューID"},
                    "status": {"type": "string", "description": "新しいステータス: resolved / ignored / unresolved"},
                },
                "required": ["issue_id", "status"],
            },
        ),
        types.Tool(
            name="list_events",
            description="イシューに関連するイベント一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_id": {"type": "string", "description": "イシューID"},
                    "limit": {"type": "integer", "description": "取得件数（デフォルト10）"},
                },
                "required": ["issue_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()
    org = _org()

    if name == "list_projects":
        r = client.get(f"/organizations/{org}/projects/")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_issues":
        project_slug = arguments["project_slug"]
        params = {"limit": arguments.get("limit", 25)}
        if arguments.get("query"):
            params["query"] = arguments["query"]
        r = client.get(f"/projects/{org}/{project_slug}/issues/", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_issue":
        issue_id = arguments["issue_id"]
        r = client.get(f"/issues/{issue_id}/")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "update_issue":
        issue_id = arguments["issue_id"]
        payload = {"status": arguments["status"]}
        r = client.put(f"/issues/{issue_id}/", json=payload)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_events":
        issue_id = arguments["issue_id"]
        params = {"limit": arguments.get("limit", 10)}
        r = client.get(f"/issues/{issue_id}/events/", params=params)
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
