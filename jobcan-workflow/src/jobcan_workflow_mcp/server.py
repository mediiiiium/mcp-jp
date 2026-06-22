import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("jobcan-workflow-mcp")

BASE_URL = "https://ssl.wf.jobcan.jp/wf_api"


def _client() -> httpx.Client:
    token = os.environ.get("JOBCAN_API_TOKEN")
    if not token:
        raise ValueError("JOBCAN_API_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Token {token}", "Content-Type": "application/json"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_requests",
            description="ジョブカン経費精算/ワークフローの申請書一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "ステータスで絞り込み（in_progress: 進行中, completed: 完了, rejected: 却下, returned: 差し戻し, canceled: 取り消し）",
                        "enum": ["in_progress", "completed", "rejected", "returned", "canceled", "canceled_after_completion"],
                    },
                    "title": {
                        "type": "string",
                        "description": "タイトルで絞り込み（部分一致）",
                    },
                    "applicant_code": {
                        "type": "string",
                        "description": "申請者のユーザーコードで絞り込み",
                    },
                    "project_code": {
                        "type": "string",
                        "description": "プロジェクトコードで絞り込み",
                    },
                    "applied_after": {
                        "type": "string",
                        "description": "申請日の開始日（YYYY-MM-DD形式）",
                    },
                    "applied_before": {
                        "type": "string",
                        "description": "申請日の終了日（YYYY-MM-DD形式）",
                    },
                    "page": {
                        "type": "integer",
                        "description": "ページ番号（デフォルト: 1）",
                        "default": 1,
                    },
                },
            },
        ),
        types.Tool(
            name="get_request",
            description="申請書の詳細情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "request_id": {
                        "type": "integer",
                        "description": "申請書ID",
                    },
                },
                "required": ["request_id"],
            },
        ),
        types.Tool(
            name="list_users",
            description="ジョブカンのユーザー一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer",
                        "description": "ページ番号（デフォルト: 1）",
                        "default": 1,
                    },
                },
            },
        ),
        types.Tool(
            name="list_projects",
            description="プロジェクト一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer",
                        "description": "ページ番号（デフォルト: 1）",
                        "default": 1,
                    },
                },
            },
        ),
        types.Tool(
            name="list_companies",
            description="取引先一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer",
                        "description": "ページ番号（デフォルト: 1）",
                        "default": 1,
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_requests":
                params: dict = {"page": arguments.get("page", 1)}
                if arguments.get("status"):
                    params["status"] = arguments["status"]
                if arguments.get("title"):
                    params["title"] = arguments["title"]
                if arguments.get("applicant_code"):
                    params["applicant_code"] = arguments["applicant_code"]
                if arguments.get("project_code"):
                    params["project_code"] = arguments["project_code"]
                if arguments.get("applied_after"):
                    params["applied_after"] = arguments["applied_after"]
                if arguments.get("applied_before"):
                    params["applied_before"] = arguments["applied_before"]
                r = client.get("/v2/requests/", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_request":
                rid = arguments["request_id"]
                r = client.get(f"/v1/requests/{rid}/")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_users":
                params = {"page": arguments.get("page", 1)}
                r = client.get("/v3/users/", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_projects":
                params = {"page": arguments.get("page", 1)}
                r = client.get("/v1/projects/", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_companies":
                params = {"page": arguments.get("page", 1)}
                r = client.get("/v1/company/", params=params)
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
