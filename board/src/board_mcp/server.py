import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("board-mcp")
BASE_URL = "https://api.the-board.jp/v1"


def _client() -> httpx.Client:
    api_key = os.environ.get("BOARD_API_KEY")
    api_token = os.environ.get("BOARD_API_TOKEN")
    if not api_key:
        raise ValueError("BOARD_API_KEY が設定されていません")
    if not api_token:
        raise ValueError("BOARD_API_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "x-api-key": api_key,
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_clients",
            description="顧客一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（最大100）", "default": 20},
                    "name": {"type": "string", "description": "顧客名で絞り込み"},
                },
            },
        ),
        types.Tool(
            name="list_projects",
            description="プロジェクト一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（最大100）", "default": 20},
                    "client_id": {"type": "integer", "description": "顧客IDで絞り込み"},
                    "status": {"type": "string", "description": "ステータス: active / complete / suspend"},
                },
            },
        ),
        types.Tool(
            name="get_project",
            description="プロジェクトの詳細情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer", "description": "プロジェクトID"},
                },
                "required": ["project_id"],
            },
        ),
        types.Tool(
            name="list_invoices",
            description="請求書一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（最大100）", "default": 20},
                    "client_id": {"type": "integer", "description": "顧客IDで絞り込み"},
                    "project_id": {"type": "integer", "description": "プロジェクトIDで絞り込み"},
                },
            },
        ),
        types.Tool(
            name="create_project",
            description="新しいプロジェクトを作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "プロジェクト名"},
                    "client_id": {"type": "integer", "description": "顧客ID"},
                    "start_date": {"type": "string", "description": "開始日（YYYY-MM-DD）"},
                    "end_date": {"type": "string", "description": "終了日（YYYY-MM-DD）"},
                    "budget": {"type": "integer", "description": "予算（円）"},
                },
                "required": ["name"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_clients":
                params: dict = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 20),
                }
                if arguments.get("name"):
                    params["name"] = arguments["name"]
                r = client.get("/clients", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_projects":
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 20),
                }
                if arguments.get("client_id"):
                    params["client_id"] = arguments["client_id"]
                if arguments.get("status"):
                    params["status"] = arguments["status"]
                r = client.get("/projects", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_project":
                r = client.get(f"/projects/{arguments['project_id']}")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_invoices":
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 20),
                }
                if arguments.get("client_id"):
                    params["client_id"] = arguments["client_id"]
                if arguments.get("project_id"):
                    params["project_id"] = arguments["project_id"]
                r = client.get("/invoices", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "create_project":
                payload: dict = {"name": arguments["name"]}
                if arguments.get("client_id"):
                    payload["client_id"] = arguments["client_id"]
                if arguments.get("start_date"):
                    payload["start_date"] = arguments["start_date"]
                if arguments.get("end_date"):
                    payload["end_date"] = arguments["end_date"]
                if arguments.get("budget") is not None:
                    payload["budget"] = arguments["budget"]
                r = client.post("/projects", json=payload)
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
