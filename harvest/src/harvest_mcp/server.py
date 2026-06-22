import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("harvest-mcp")
BASE_URL = "https://api.harvestapp.com/v2"


def _client() -> httpx.Client:
    access_token = os.environ.get("HARVEST_ACCESS_TOKEN")
    account_id = os.environ.get("HARVEST_ACCOUNT_ID")
    if not access_token:
        raise ValueError("HARVEST_ACCESS_TOKEN が設定されていません")
    if not account_id:
        raise ValueError("HARVEST_ACCOUNT_ID が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Harvest-Account-Id": account_id,
            "Content-Type": "application/json",
            "User-Agent": "harvest-mcp/0.1.0",
        },
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
                    "is_active": {"type": "boolean", "description": "アクティブなプロジェクトのみ取得"},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（デフォルト100）"},
                },
            },
        ),
        types.Tool(
            name="list_time_entries",
            description="時間計測エントリー一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer", "description": "プロジェクトIDでフィルタ"},
                    "from_date": {"type": "string", "description": "開始日（YYYY-MM-DD形式）"},
                    "to_date": {"type": "string", "description": "終了日（YYYY-MM-DD形式）"},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（デフォルト100）"},
                },
            },
        ),
        types.Tool(
            name="create_time_entry",
            description="新しい時間計測エントリーを作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer", "description": "プロジェクトID"},
                    "task_id": {"type": "integer", "description": "タスクID"},
                    "spent_date": {"type": "string", "description": "作業日（YYYY-MM-DD形式）"},
                    "hours": {"type": "number", "description": "作業時間（例: 1.5）"},
                    "notes": {"type": "string", "description": "メモ"},
                },
                "required": ["project_id", "task_id", "spent_date"],
            },
        ),
        types.Tool(
            name="list_clients",
            description="クライアント一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "is_active": {"type": "boolean", "description": "アクティブなクライアントのみ取得"},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（デフォルト100）"},
                },
            },
        ),
        types.Tool(
            name="list_invoices",
            description="請求書一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "client_id": {"type": "integer", "description": "クライアントIDでフィルタ"},
                    "state": {"type": "string", "description": "ステータス: draft / open / paid / closed"},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（デフォルト100）"},
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_projects":
                params = {"per_page": arguments.get("per_page", 100)}
                if arguments.get("is_active") is not None:
                    params["is_active"] = arguments["is_active"]
                r = client.get("/projects", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_time_entries":
                params = {"per_page": arguments.get("per_page", 100)}
                if arguments.get("project_id"):
                    params["project_id"] = arguments["project_id"]
                if arguments.get("from_date"):
                    params["from"] = arguments["from_date"]
                if arguments.get("to_date"):
                    params["to"] = arguments["to_date"]
                r = client.get("/time_entries", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "create_time_entry":
                payload = {
                    "project_id": arguments["project_id"],
                    "task_id": arguments["task_id"],
                    "spent_date": arguments["spent_date"],
                }
                if arguments.get("hours"):
                    payload["hours"] = arguments["hours"]
                if arguments.get("notes"):
                    payload["notes"] = arguments["notes"]
                r = client.post("/time_entries", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_clients":
                params = {"per_page": arguments.get("per_page", 100)}
                if arguments.get("is_active") is not None:
                    params["is_active"] = arguments["is_active"]
                r = client.get("/clients", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_invoices":
                params = {"per_page": arguments.get("per_page", 100)}
                if arguments.get("client_id"):
                    params["client_id"] = arguments["client_id"]
                if arguments.get("state"):
                    params["state"] = arguments["state"]
                r = client.get("/invoices", params=params)
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
