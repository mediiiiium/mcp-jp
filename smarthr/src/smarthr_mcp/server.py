import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("smarthr-mcp")


def get_client() -> httpx.Client:
    token = os.environ.get("SMARTHR_ACCESS_TOKEN")
    tenant = os.environ.get("SMARTHR_TENANT_ID")
    if not token:
        raise ValueError("SMARTHR_ACCESS_TOKEN が設定されていません")
    if not tenant:
        raise ValueError("SMARTHR_TENANT_ID が設定されていません")
    return httpx.Client(
        base_url=f"https://{tenant}.smarthr.jp/api/v1",
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
            name="list_crews",
            description="従業員（crew）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり）", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（最大100）", "default": 20},
                    "employment_type_id": {"type": "string", "description": "雇用形態IDで絞り込み"},
                    "department_id": {"type": "string", "description": "部署IDで絞り込み"},
                },
            },
        ),
        types.Tool(
            name="get_crew",
            description="特定の従業員（crew）の詳細情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "従業員ID（UUIDまたは社員番号）"},
                },
                "required": ["id"],
            },
        ),
        types.Tool(
            name="list_departments",
            description="部署一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数", "default": 50},
                },
            },
        ),
        types.Tool(
            name="list_employment_types",
            description="雇用形態一覧を取得する（正社員・パート・契約社員等）",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数", "default": 50},
                },
            },
        ),
        types.Tool(
            name="update_crew",
            description="従業員情報を更新する（部署・雇用形態・カスタム項目等）",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "従業員ID"},
                    "department_id": {"type": "string", "description": "異動先部署ID"},
                    "employment_type_id": {"type": "string", "description": "変更後の雇用形態ID"},
                    "last_name": {"type": "string", "description": "姓"},
                    "first_name": {"type": "string", "description": "名"},
                    "email": {"type": "string", "description": "メールアドレス"},
                },
                "required": ["id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = get_client()

    if name == "list_crews":
        params = {
            "page": arguments.get("page", 1),
            "per_page": arguments.get("per_page", 20),
        }
        if arguments.get("employment_type_id"):
            params["employment_type_id"] = arguments["employment_type_id"]
        if arguments.get("department_id"):
            params["department_id"] = arguments["department_id"]
        r = client.get("/crews", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_crew":
        r = client.get(f"/crews/{arguments['id']}")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_departments":
        params = {
            "page": arguments.get("page", 1),
            "per_page": arguments.get("per_page", 50),
        }
        r = client.get("/departments", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_employment_types":
        params = {
            "page": arguments.get("page", 1),
            "per_page": arguments.get("per_page", 50),
        }
        r = client.get("/employment_types", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "update_crew":
        crew_id = arguments.pop("id")
        payload = {k: v for k, v in arguments.items() if v is not None}
        r = client.patch(f"/crews/{crew_id}", json=payload)
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
