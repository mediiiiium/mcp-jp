import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("yappli-crm-mcp")

_token_cache: str | None = None


def _base_url() -> str:
    url = os.environ.get("YAPPLI_CRM_APP_URL")
    if not url:
        raise ValueError("YAPPLI_CRM_APP_URL が設定されていません")
    return url.rstrip("/")


def _get_token() -> str:
    global _token_cache
    if _token_cache:
        return _token_cache
    client_id = os.environ.get("YAPPLI_CRM_CLIENT_ID")
    client_secret = os.environ.get("YAPPLI_CRM_CLIENT_SECRET")
    if not client_id:
        raise ValueError("YAPPLI_CRM_CLIENT_ID が設定されていません")
    if not client_secret:
        raise ValueError("YAPPLI_CRM_CLIENT_SECRET が設定されていません")
    r = httpx.post(
        f"{_base_url()}/api/ext/token",
        json={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={"Content-Type": "application/json", "User-Agent": "yappli-crm-mcp/0.1.0"},
        timeout=30,
    )
    r.raise_for_status()
    _token_cache = r.json()["access_token"]
    return _token_cache


def _client() -> httpx.Client:
    return httpx.Client(
        base_url=f"{_base_url()}/api/ext",
        headers={
            "Authorization": f"Bearer {_get_token()}",
            "Content-Type": "application/json",
            "User-Agent": "yappli-crm-mcp/0.1.0",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_users",
            description="CRM ユーザー（会員）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数", "default": 20},
                },
            },
        ),
        types.Tool(
            name="get_user",
            description="会員IDで特定のユーザー情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "会員ID"},
                },
                "required": ["user_id"],
            },
        ),
        types.Tool(
            name="create_user",
            description="新規会員を登録する",
            inputSchema={
                "type": "object",
                "properties": {
                    "unique_id": {"type": "string", "description": "一意な会員識別子"},
                    "name": {"type": "string", "description": "会員名"},
                    "email": {"type": "string", "description": "メールアドレス"},
                    "birthday": {"type": "string", "description": "生年月日（YYYY-MM-DD形式）"},
                    "gender": {"type": "integer", "description": "性別（1:男性, 2:女性, 3:その他）"},
                },
            },
        ),
        types.Tool(
            name="get_user_points",
            description="会員のポイント付与・利用履歴を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "会員ID"},
                    "page": {"type": "integer", "description": "ページ番号", "default": 1},
                },
                "required": ["user_id"],
            },
        ),
        types.Tool(
            name="add_user_points",
            description="会員にポイントを付与または減算する",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "会員ID"},
                    "point": {"type": "integer", "description": "付与ポイント数（負の値で減算）"},
                    "reason": {"type": "string", "description": "付与・減算理由（履歴に表示）"},
                    "expire_date": {"type": "string", "description": "ポイント有効期限（YYYY-MM-DD形式）"},
                },
                "required": ["user_id", "point"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "list_users":
        params: dict = {}
        if arguments.get("page"):
            params["page"] = arguments["page"]
        if arguments.get("per_page"):
            params["per_page"] = arguments["per_page"]
        r = client.get("/users", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_user":
        r = client.get(f"/users/{arguments['user_id']}")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "create_user":
        body: dict = {}
        for key in ("unique_id", "name", "email", "birthday", "gender"):
            if arguments.get(key) is not None:
                body[key] = arguments[key]
        r = client.post("/users", json=body)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_user_points":
        params = {}
        if arguments.get("page"):
            params["page"] = arguments["page"]
        r = client.get(f"/users/{arguments['user_id']}/points", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "add_user_points":
        body = {"point": arguments["point"]}
        if arguments.get("reason"):
            body["reason"] = arguments["reason"]
        if arguments.get("expire_date"):
            body["expire_date"] = arguments["expire_date"]
        r = client.post(f"/users/{arguments['user_id']}/points", json=body)
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
