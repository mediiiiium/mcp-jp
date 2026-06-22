import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("talentio-mcp")
BASE_URL = "https://talentio.com/api/v1"


def _client() -> httpx.Client:
    token = os.environ.get("TALENTIO_ACCESS_TOKEN")
    if not token:
        raise ValueError("TALENTIO_ACCESS_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_candidates",
            description="候補者一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり）", "default": 1},
                },
            },
        ),
        types.Tool(
            name="get_candidate",
            description="候補者の詳細情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "candidate_id": {"type": "string", "description": "候補者ID"},
                },
                "required": ["candidate_id"],
            },
        ),
        types.Tool(
            name="list_jobs",
            description="求人（ポジション）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり）", "default": 1},
                    "status": {"type": "string", "description": "ステータス: open / closed / draft"},
                },
            },
        ),
        types.Tool(
            name="list_applications",
            description="応募一覧を取得する（候補者と求人の紐付け）",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり）", "default": 1},
                    "job_id": {"type": "string", "description": "求人IDで絞り込み"},
                },
            },
        ),
        types.Tool(
            name="list_pipeline_stages",
            description="選考パイプラインのステージ一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "list_candidates":
        params = {"page": arguments.get("page", 1)}
        r = client.get("/candidates", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_candidate":
        r = client.get(f"/candidates/{arguments['candidate_id']}")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_jobs":
        params: dict = {"page": arguments.get("page", 1)}
        if arguments.get("status"):
            params["status"] = arguments["status"]
        r = client.get("/jobs", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_applications":
        params = {"page": arguments.get("page", 1)}
        if arguments.get("job_id"):
            params["job_id"] = arguments["job_id"]
        r = client.get("/applications", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_pipeline_stages":
        r = client.get("/pipeline_stages")
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
