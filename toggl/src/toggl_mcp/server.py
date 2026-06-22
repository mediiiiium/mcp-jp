import os
import base64
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("toggl-mcp")
BASE_URL = "https://api.track.toggl.com/api/v9"


def _client() -> httpx.Client:
    api_token = os.environ.get("TOGGL_API_TOKEN")
    if not api_token:
        raise ValueError("TOGGL_API_TOKEN が設定されていません")
    credentials = base64.b64encode(f"{api_token}:api_token".encode()).decode()
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Basic {credentials}", "Content-Type": "application/json"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_profile",
            description="現在のユーザープロファイルを取得する",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
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
                    "workspace_id": {"type": "integer", "description": "ワークスペースID"},
                    "active": {"type": "boolean", "description": "アクティブなプロジェクトのみ取得（デフォルトtrue）"},
                },
                "required": ["workspace_id"],
            },
        ),
        types.Tool(
            name="list_time_entries",
            description="時間計測エントリー一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "開始日（YYYY-MM-DD形式）"},
                    "end_date": {"type": "string", "description": "終了日（YYYY-MM-DD形式）"},
                    "meta": {"type": "boolean", "description": "追加メタデータを含む（デフォルトfalse）"},
                },
            },
        ),
        types.Tool(
            name="create_time_entry",
            description="新しい時間計測エントリーを作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "integer", "description": "ワークスペースID"},
                    "description": {"type": "string", "description": "作業内容の説明"},
                    "project_id": {"type": "integer", "description": "プロジェクトID"},
                    "start": {"type": "string", "description": "開始時刻（ISO8601形式、例: 2024-04-01T10:00:00+09:00）"},
                    "duration": {"type": "integer", "description": "作業時間（秒、実行中の場合は -1）"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "タグ一覧"},
                },
                "required": ["workspace_id", "start", "duration"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "get_profile":
                r = client.get("/me")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_workspaces":
                r = client.get("/workspaces")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_projects":
                workspace_id = arguments["workspace_id"]
                params = {"active": str(arguments.get("active", True)).lower()}
                r = client.get(f"/workspaces/{workspace_id}/projects", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_time_entries":
                params = {}
                if arguments.get("start_date"):
                    params["start_date"] = arguments["start_date"]
                if arguments.get("end_date"):
                    params["end_date"] = arguments["end_date"]
                if arguments.get("meta"):
                    params["meta"] = arguments["meta"]
                r = client.get("/me/time_entries", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "create_time_entry":
                workspace_id = arguments["workspace_id"]
                payload = {
                    "start": arguments["start"],
                    "duration": arguments["duration"],
                    "created_with": "toggl-mcp",
                    "workspace_id": workspace_id,
                }
                if arguments.get("description"):
                    payload["description"] = arguments["description"]
                if arguments.get("project_id"):
                    payload["project_id"] = arguments["project_id"]
                if arguments.get("tags"):
                    payload["tags"] = arguments["tags"]
                r = client.post(f"/workspaces/{workspace_id}/time_entries", json=payload)
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
