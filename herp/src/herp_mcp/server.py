import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("herp-mcp")
BASE_URL = "https://public-api.herp.cloud/hire/v1"


def _client() -> httpx.Client:
    token = os.environ.get("HERP_API_KEY")
    if not token:
        raise ValueError("HERP_API_KEY が設定されていません")
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
            name="list_candidacies",
            description="応募者（選考）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（最大100）", "default": 20},
                    "offset": {"type": "integer", "description": "取得開始位置", "default": 0},
                    "requisition_id": {"type": "string", "description": "求人IDで絞り込み"},
                },
            },
        ),
        types.Tool(
            name="get_candidacy",
            description="応募者（選考）の詳細情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "candidacy_id": {"type": "string", "description": "応募ID"},
                },
                "required": ["candidacy_id"],
            },
        ),
        types.Tool(
            name="list_requisitions",
            description="求人（ポジション）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（最大100）", "default": 20},
                    "offset": {"type": "integer", "description": "取得開始位置", "default": 0},
                },
            },
        ),
        types.Tool(
            name="list_timeline_comments",
            description="応募者のタイムラインコメント一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "candidacy_id": {"type": "string", "description": "応募ID"},
                },
                "required": ["candidacy_id"],
            },
        ),
        types.Tool(
            name="add_timeline_comment",
            description="応募者のタイムラインにコメントを追加する",
            inputSchema={
                "type": "object",
                "properties": {
                    "candidacy_id": {"type": "string", "description": "応募ID"},
                    "body": {"type": "string", "description": "コメント本文"},
                },
                "required": ["candidacy_id", "body"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_candidacies":
                params: dict = {
                    "limit": arguments.get("limit", 20),
                    "offset": arguments.get("offset", 0),
                }
                if arguments.get("requisition_id"):
                    params["requisitionId"] = arguments["requisition_id"]
                r = client.get("/candidacies", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_candidacy":
                r = client.get(f"/candidacies/{arguments['candidacy_id']}")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_requisitions":
                params = {
                    "limit": arguments.get("limit", 20),
                    "offset": arguments.get("offset", 0),
                }
                r = client.get("/requisitions", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_timeline_comments":
                r = client.get(f"/candidacies/{arguments['candidacy_id']}/timeline-comments")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "add_timeline_comment":
                payload = {"body": arguments["body"]}
                r = client.post(f"/candidacies/{arguments['candidacy_id']}/timeline-comments", json=payload)
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
