import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("circleci-mcp")
BASE_URL = "https://circleci.com/api/v2"


def _client() -> httpx.Client:
    token = os.environ.get("CIRCLECI_TOKEN")
    if not token:
        raise ValueError("CIRCLECI_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Circle-Token": token, "Content-Type": "application/json"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_current_user",
            description="現在のユーザー情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="list_pipelines",
            description="プロジェクトのパイプライン一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_slug": {"type": "string", "description": "プロジェクトスラッグ（例: github/myorg/myrepo）"},
                    "branch": {"type": "string", "description": "ブランチでフィルタ"},
                    "page_token": {"type": "string", "description": "ページネーショントークン"},
                },
                "required": ["project_slug"],
            },
        ),
        types.Tool(
            name="list_workflows",
            description="パイプラインのワークフロー一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "pipeline_id": {"type": "string", "description": "パイプラインID"},
                },
                "required": ["pipeline_id"],
            },
        ),
        types.Tool(
            name="list_jobs",
            description="ワークフローのジョブ一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "string", "description": "ワークフローID"},
                },
                "required": ["workflow_id"],
            },
        ),
        types.Tool(
            name="get_job_details",
            description="ジョブの詳細を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_slug": {"type": "string", "description": "プロジェクトスラッグ（例: github/myorg/myrepo）"},
                    "job_number": {"type": "integer", "description": "ジョブ番号"},
                },
                "required": ["project_slug", "job_number"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "get_current_user":
        r = client.get("/me")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_pipelines":
        project_slug = arguments["project_slug"]
        params = {}
        if arguments.get("branch"):
            params["branch"] = arguments["branch"]
        if arguments.get("page_token"):
            params["page-token"] = arguments["page_token"]
        r = client.get(f"/project/{project_slug}/pipeline", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_workflows":
        pipeline_id = arguments["pipeline_id"]
        r = client.get(f"/pipeline/{pipeline_id}/workflow")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_jobs":
        workflow_id = arguments["workflow_id"]
        r = client.get(f"/workflow/{workflow_id}/job")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_job_details":
        project_slug = arguments["project_slug"]
        job_number = arguments["job_number"]
        r = client.get(f"/project/{project_slug}/job/{job_number}")
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
