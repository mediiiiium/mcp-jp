import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("akashi-mcp")

BASE_URL = "https://atnd.ak4.jp/api/cooperation"


def _company_id() -> str:
    cid = os.environ.get("AKASHI_COMPANY_ID")
    if not cid:
        raise ValueError("AKASHI_COMPANY_ID が設定されていません")
    return cid


def _token() -> str:
    tok = os.environ.get("AKASHI_TOKEN")
    if not tok:
        raise ValueError("AKASHI_TOKEN が設定されていません")
    return tok


def _get(path: str, params: dict | None = None) -> dict:
    p = params or {}
    p["token"] = _token()
    r = httpx.get(f"{BASE_URL}{path}", params=p, timeout=30)
    r.raise_for_status()
    return r.json()


def _post(path: str, body: dict) -> dict:
    body["token"] = _token()
    r = httpx.post(f"{BASE_URL}{path}", json=body, timeout=30)
    r.raise_for_status()
    return r.json()


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_stamps",
            description="指定期間の打刻記録を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "取得開始日時（yyyymmddHHMMSS 形式、例: 20240101000000）",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "取得終了日時（yyyymmddHHMMSS 形式、例: 20240131235959）",
                    },
                    "staff_id": {
                        "type": "integer",
                        "description": "取得対象の従業員ID（省略時は全従業員）",
                    },
                },
                "required": ["start_date", "end_date"],
            },
        ),
        types.Tool(
            name="post_stamp",
            description="打刻を記録する（出勤・退勤・休憩など）",
            inputSchema={
                "type": "object",
                "properties": {
                    "stamp_type": {
                        "type": "integer",
                        "description": (
                            "打刻種別: 11=出勤, 12=退勤, 21=直行, 22=直帰, 31=休憩入, 32=休憩戻"
                        ),
                    },
                    "stamped_at": {
                        "type": "string",
                        "description": "打刻日時（yyyy/mm/dd HH:MM:SS 形式、省略時はサーバー時刻）",
                    },
                },
                "required": ["stamp_type"],
            },
        ),
        types.Tool(
            name="list_staffs",
            description="従業員一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer",
                        "description": "ページ番号（1から開始）",
                        "default": 1,
                    },
                },
            },
        ),
        types.Tool(
            name="get_staff",
            description="特定の従業員の詳細情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "staff_id": {
                        "type": "integer",
                        "description": "取得対象の従業員ID",
                    },
                },
                "required": ["staff_id"],
            },
        ),
        types.Tool(
            name="get_alerts",
            description="勤怠アラート一覧を取得する（未打刻・残業超過など）",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        company_id = _company_id()

        if name == "get_stamps":
            params: dict = {
                "start_date": arguments["start_date"],
                "end_date": arguments["end_date"],
            }
            if arguments.get("staff_id"):
                path = f"/{company_id}/stamps/{arguments['staff_id']}"
            else:
                path = f"/{company_id}/stamps"
            result = _get(path, params)
            return format_response(result)

        elif name == "post_stamp":
            body: dict = {"type": arguments["stamp_type"]}
            if arguments.get("stamped_at"):
                body["stampedAt"] = arguments["stamped_at"]
            result = _post(f"/{company_id}/stamps", body)
            return format_response(result)

        elif name == "list_staffs":
            params = {"page": arguments.get("page", 1)}
            result = _get(f"/{company_id}/staffs", params)
            return format_response(result)

        elif name == "get_staff":
            result = _get(f"/{company_id}/staffs/{arguments['staff_id']}")
            return format_response(result)

        elif name == "get_alerts":
            result = _get(f"/{company_id}/alerts")
            return format_response(result)

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
