import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("pipedrive-mcp")
BASE_URL = "https://api.pipedrive.com/v1"


def _client() -> httpx.Client:
    api_token = os.environ.get("PIPEDRIVE_API_TOKEN")
    if not api_token:
        raise ValueError("PIPEDRIVE_API_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Content-Type": "application/json"},
        params={"api_token": api_token},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_persons",
            description="人物（コンタクト）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（デフォルト100）"},
                    "start": {"type": "integer", "description": "オフセット（デフォルト0）"},
                },
            },
        ),
        types.Tool(
            name="search_persons",
            description="人物（コンタクト）を名前やメールで検索する",
            inputSchema={
                "type": "object",
                "properties": {
                    "term": {"type": "string", "description": "検索キーワード（名前、メールなど）"},
                    "fields": {"type": "string", "description": "検索対象フィールド（例: name, email）"},
                    "limit": {"type": "integer", "description": "取得件数（デフォルト10）"},
                },
                "required": ["term"],
            },
        ),
        types.Tool(
            name="list_deals",
            description="案件（Deal）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "ステータス: open / won / lost / all_not_deleted"},
                    "limit": {"type": "integer", "description": "取得件数（デフォルト100）"},
                    "start": {"type": "integer", "description": "オフセット（デフォルト0）"},
                },
            },
        ),
        types.Tool(
            name="create_deal",
            description="新しい案件（Deal）を作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "案件のタイトル"},
                    "value": {"type": "number", "description": "案件の金額"},
                    "currency": {"type": "string", "description": "通貨（例: JPY, USD）"},
                    "person_id": {"type": "integer", "description": "担当者（Person）のID"},
                    "org_id": {"type": "integer", "description": "組織（Organization）のID"},
                    "stage_id": {"type": "integer", "description": "パイプラインステージのID"},
                },
                "required": ["title"],
            },
        ),
        types.Tool(
            name="list_activities",
            description="アクティビティ（商談活動）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "done": {"type": "integer", "description": "0=未完了, 1=完了"},
                    "limit": {"type": "integer", "description": "取得件数（デフォルト100）"},
                    "start": {"type": "integer", "description": "オフセット（デフォルト0）"},
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_persons":
                params = {
                    "limit": arguments.get("limit", 100),
                    "start": arguments.get("start", 0),
                }
                r = client.get("/persons", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "search_persons":
                params = {
                    "term": arguments["term"],
                    "limit": arguments.get("limit", 10),
                    "item_type": "person",
                }
                if arguments.get("fields"):
                    params["fields"] = arguments["fields"]
                r = client.get("/persons/search", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_deals":
                params = {
                    "status": arguments.get("status", "open"),
                    "limit": arguments.get("limit", 100),
                    "start": arguments.get("start", 0),
                }
                r = client.get("/deals", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "create_deal":
                payload = {"title": arguments["title"]}
                for field in ("value", "currency", "person_id", "org_id", "stage_id"):
                    if arguments.get(field) is not None:
                        payload[field] = arguments[field]
                r = client.post("/deals", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_activities":
                params = {
                    "limit": arguments.get("limit", 100),
                    "start": arguments.get("start", 0),
                }
                if arguments.get("done") is not None:
                    params["done"] = arguments["done"]
                r = client.get("/activities", params=params)
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
