import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("hrmos-kintai-mcp")

_token_cache: str | None = None


def _base_url() -> str:
    company_url = os.environ.get("HRMOS_COMPANY_URL")
    if not company_url:
        raise ValueError("HRMOS_COMPANY_URL が設定されていません")
    return f"https://ieyasu.co/api/{company_url}/v1"


def _get_token() -> str:
    global _token_cache
    if _token_cache:
        return _token_cache
    api_key = os.environ.get("HRMOS_API_KEY")
    if not api_key:
        raise ValueError("HRMOS_API_KEY が設定されていません")
    r = httpx.get(
        f"{_base_url()}/authentication/token",
        auth=(api_key, ""),
        timeout=30,
    )
    r.raise_for_status()
    _token_cache = r.json()["token"]
    return _token_cache


def _client() -> httpx.Client:
    token = _get_token()
    return httpx.Client(
        base_url=_base_url(),
        headers={
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_monthly_attendance",
            description="指定月の月次勤怠データを取得する（全社員分）",
            inputSchema={
                "type": "object",
                "properties": {
                    "month": {"type": "string", "description": "対象月（YYYY-MM形式。例: 2026-06）"},
                    "page": {"type": "integer", "description": "ページ番号", "default": 1},
                    "limit": {"type": "integer", "description": "1ページあたりの件数", "default": 50},
                },
                "required": ["month"],
            },
        ),
        types.Tool(
            name="get_daily_attendance",
            description="指定日の日次勤怠データを取得する（全社員分）",
            inputSchema={
                "type": "object",
                "properties": {
                    "day": {"type": "string", "description": "対象日（YYYY-MM-DD形式。例: 2026-06-15）"},
                    "page": {"type": "integer", "description": "ページ番号", "default": 1},
                    "limit": {"type": "integer", "description": "1ページあたりの件数", "default": 50},
                },
                "required": ["day"],
            },
        ),
        types.Tool(
            name="list_users",
            description="会社に登録されているユーザー（社員）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号", "default": 1},
                    "limit": {"type": "integer", "description": "1ページあたりの件数", "default": 50},
                },
            },
        ),
        types.Tool(
            name="list_departments",
            description="部署一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="get_user_stamps",
            description="指定ユーザーの打刻履歴を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ユーザーID"},
                    "from": {"type": "string", "description": "取得開始日（YYYY-MM-DD形式）"},
                    "to": {"type": "string", "description": "取得終了日（YYYY-MM-DD形式）"},
                    "page": {"type": "integer", "description": "ページ番号", "default": 1},
                    "limit": {"type": "integer", "description": "1ページあたりの件数", "default": 50},
                },
                "required": ["user_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    global _token_cache
    try:
        try:
            client = _client()
        except Exception:
            _token_cache = None
            client = _client()

        with client:
            if name == "get_monthly_attendance":
                month = arguments["month"]
                params: dict = {
                    "page": arguments.get("page", 1),
                    "limit": arguments.get("limit", 50),
                }
                r = client.get(f"/work_outputs/monthly/{month}", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_daily_attendance":
                day = arguments["day"]
                params = {
                    "page": arguments.get("page", 1),
                    "limit": arguments.get("limit", 50),
                }
                r = client.get(f"/work_outputs/daily/{day}", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_users":
                params = {
                    "page": arguments.get("page", 1),
                    "limit": arguments.get("limit", 50),
                }
                r = client.get("/users", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_departments":
                r = client.get("/departments")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_user_stamps":
                user_id = arguments["user_id"]
                params = {
                    "page": arguments.get("page", 1),
                    "limit": arguments.get("limit", 50),
                }
                if arguments.get("from"):
                    params["from"] = arguments["from"]
                if arguments.get("to"):
                    params["to"] = arguments["to"]
                r = client.get(f"/stamp_logs/user/{user_id}", params=params)
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
