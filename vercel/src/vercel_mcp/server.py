import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("vercel-mcp")
BASE_URL = "https://api.vercel.com"


def _client() -> httpx.Client:
    api_token = os.environ.get("VERCEL_ACCESS_TOKEN")
    if not api_token:
        raise ValueError("VERCEL_ACCESS_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"},
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
                    "limit": {"type": "integer", "description": "取得件数（デフォルト20）"},
                    "search": {"type": "string", "description": "プロジェクト名で検索"},
                },
            },
        ),
        types.Tool(
            name="get_project",
            description="プロジェクトの詳細を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "id_or_name": {"type": "string", "description": "プロジェクトIDまたは名前"},
                },
                "required": ["id_or_name"],
            },
        ),
        types.Tool(
            name="list_deployments",
            description="デプロイメント一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "プロジェクトIDでフィルタ"},
                    "limit": {"type": "integer", "description": "取得件数（デフォルト20）"},
                    "state": {"type": "string", "description": "ステータス: BUILDING / ERROR / INITIALIZING / QUEUED / READY / CANCELED"},
                },
            },
        ),
        types.Tool(
            name="get_deployment",
            description="デプロイメントの詳細を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "deployment_id": {"type": "string", "description": "デプロイメントIDまたはURL"},
                },
                "required": ["deployment_id"],
            },
        ),
        types.Tool(
            name="list_domains",
            description="ドメイン一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（デフォルト20）"},
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "list_projects":
        params = {"limit": arguments.get("limit", 20)}
        if arguments.get("search"):
            params["search"] = arguments["search"]
        r = client.get("/v9/projects", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_project":
        id_or_name = arguments["id_or_name"]
        r = client.get(f"/v9/projects/{id_or_name}")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_deployments":
        params = {"limit": arguments.get("limit", 20)}
        if arguments.get("project_id"):
            params["projectId"] = arguments["project_id"]
        if arguments.get("state"):
            params["state"] = arguments["state"]
        r = client.get("/v6/deployments", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_deployment":
        deployment_id = arguments["deployment_id"]
        r = client.get(f"/v13/deployments/{deployment_id}")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_domains":
        params = {"limit": arguments.get("limit", 20)}
        r = client.get("/v5/domains", params=params)
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
