import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("typeform-mcp")
BASE_URL = "https://api.typeform.com"


def _client() -> httpx.Client:
    access_token = os.environ.get("TYPEFORM_ACCESS_TOKEN")
    if not access_token:
        raise ValueError("TYPEFORM_ACCESS_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_forms",
            description="フォーム一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（デフォルト1）"},
                    "page_size": {"type": "integer", "description": "1ページあたりの件数（デフォルト10）"},
                    "search": {"type": "string", "description": "フォームタイトルで検索"},
                },
            },
        ),
        types.Tool(
            name="get_form",
            description="フォームの詳細を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "form_id": {"type": "string", "description": "フォームID"},
                },
                "required": ["form_id"],
            },
        ),
        types.Tool(
            name="get_responses",
            description="フォームの回答一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "form_id": {"type": "string", "description": "フォームID"},
                    "page_size": {"type": "integer", "description": "1ページあたりの件数（デフォルト25）"},
                    "since": {"type": "string", "description": "この日時以降の回答（ISO8601形式）"},
                    "until": {"type": "string", "description": "この日時以前の回答（ISO8601形式）"},
                },
                "required": ["form_id"],
            },
        ),
        types.Tool(
            name="list_workspaces",
            description="ワークスペース一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（デフォルト1）"},
                    "page_size": {"type": "integer", "description": "1ページあたりの件数（デフォルト10）"},
                },
            },
        ),
        types.Tool(
            name="get_response_summary",
            description="フォーム回答のサマリー統計を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "form_id": {"type": "string", "description": "フォームID"},
                },
                "required": ["form_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_forms":
                params = {
                    "page": arguments.get("page", 1),
                    "page_size": arguments.get("page_size", 10),
                }
                if arguments.get("search"):
                    params["search"] = arguments["search"]
                r = client.get("/forms", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_form":
                form_id = arguments["form_id"]
                r = client.get(f"/forms/{form_id}")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_responses":
                form_id = arguments["form_id"]
                params = {"page_size": arguments.get("page_size", 25)}
                if arguments.get("since"):
                    params["since"] = arguments["since"]
                if arguments.get("until"):
                    params["until"] = arguments["until"]
                r = client.get(f"/forms/{form_id}/responses", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_workspaces":
                params = {
                    "page": arguments.get("page", 1),
                    "page_size": arguments.get("page_size", 10),
                }
                r = client.get("/workspaces", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_response_summary":
                form_id = arguments["form_id"]
                r = client.get(f"/forms/{form_id}/insights/summary")
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
