import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("kintone-mcp")


def get_client() -> httpx.Client:
    subdomain = os.environ.get("KINTONE_SUBDOMAIN")
    token = os.environ.get("KINTONE_API_TOKEN")
    if not subdomain:
        raise ValueError("KINTONE_SUBDOMAIN が設定されていません（例: mycompany）")
    if not token:
        raise ValueError("KINTONE_API_TOKEN が設定されていません")
    return httpx.Client(
        base_url=f"https://{subdomain}.cybozu.com",
        headers={
            "X-Cybozu-API-Token": token,
            "Content-Type": "application/json",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_apps",
            description="kintoneのアプリ一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "アプリ名で絞り込み（部分一致）"},
                    "limit": {"type": "integer", "description": "取得件数（最大100）", "default": 100},
                    "offset": {"type": "integer", "description": "オフセット", "default": 0},
                },
            },
        ),
        types.Tool(
            name="get_app",
            description="アプリの詳細情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {"type": "integer", "description": "アプリID"},
                },
                "required": ["app_id"],
            },
        ),
        types.Tool(
            name="list_fields",
            description="アプリのフィールド一覧を取得する（レコード操作前に確認するとよい）",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {"type": "integer", "description": "アプリID"},
                },
                "required": ["app_id"],
            },
        ),
        types.Tool(
            name="get_record",
            description="指定したレコードIDのレコードを取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {"type": "integer", "description": "アプリID"},
                    "record_id": {"type": "integer", "description": "レコードID"},
                },
                "required": ["app_id", "record_id"],
            },
        ),
        types.Tool(
            name="search_records",
            description="クエリ条件でレコードを検索・一覧取得する（最大500件）",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {"type": "integer", "description": "アプリID"},
                    "query": {
                        "type": "string",
                        "description": "kintoneクエリ文字列（例: 'フィールドコード = \"値\"'、空欄で全件）",
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "取得するフィールドコード一覧（省略で全フィールド）",
                    },
                    "total_count": {
                        "type": "boolean",
                        "description": "マッチ件数を取得するか",
                        "default": False,
                    },
                    "limit": {"type": "integer", "description": "取得件数（最大500）", "default": 100},
                    "offset": {"type": "integer", "description": "オフセット（最大10000）", "default": 0},
                },
                "required": ["app_id"],
            },
        ),
        types.Tool(
            name="create_record",
            description="レコードを1件作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {"type": "integer", "description": "アプリID"},
                    "record": {
                        "type": "object",
                        "description": "フィールドコードをキー、{'value': 値} を値とするオブジェクト（例: {'社名': {'value': '株式会社〇〇'}}）",
                    },
                },
                "required": ["app_id", "record"],
            },
        ),
        types.Tool(
            name="update_record",
            description="レコードを1件更新する",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {"type": "integer", "description": "アプリID"},
                    "record_id": {"type": "integer", "description": "レコードID"},
                    "record": {
                        "type": "object",
                        "description": "更新するフィールドコードをキー、{'value': 値} を値とするオブジェクト",
                    },
                },
                "required": ["app_id", "record_id", "record"],
            },
        ),
        types.Tool(
            name="delete_records",
            description="レコードを複数件削除する",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {"type": "integer", "description": "アプリID"},
                    "record_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "削除するレコードIDのリスト",
                    },
                },
                "required": ["app_id", "record_ids"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    with get_client() as client:
        if name == "list_apps":
            params: dict = {
                "limit": arguments.get("limit", 100),
                "offset": arguments.get("offset", 0),
            }
            if n := arguments.get("name"):
                params["name"] = n
            r = client.get("/k/v1/apps.json", params=params)
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "get_app":
            r = client.get("/k/v1/app.json", params={"id": arguments["app_id"]})
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "list_fields":
            r = client.get("/k/v1/app/form/fields.json", params={"app": arguments["app_id"]})
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "get_record":
            r = client.get(
                "/k/v1/record.json",
                params={"app": arguments["app_id"], "id": arguments["record_id"]},
            )
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "search_records":
            limit = arguments.get("limit", 100)
            offset = arguments.get("offset", 0)
            base_query = arguments.get("query", "")
            query = f"{base_query} limit {limit} offset {offset}".strip()

            # kintone expects fields[0]=..&fields[1]=.. as a list of tuples
            params: list[tuple[str, object]] = [
                ("app", arguments["app_id"]),
                ("totalCount", str(arguments.get("total_count", False)).lower()),
                ("query", query),
            ]
            for i, f in enumerate(arguments.get("fields") or []):
                params.append((f"fields[{i}]", f))

            r = client.get("/k/v1/records.json", params=params)
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "create_record":
            r = client.post(
                "/k/v1/record.json",
                json={"app": arguments["app_id"], "record": arguments["record"]},
            )
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "update_record":
            r = client.put(
                "/k/v1/record.json",
                json={
                    "app": arguments["app_id"],
                    "id": arguments["record_id"],
                    "record": arguments["record"],
                },
            )
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "delete_records":
            r = client.request(
                "DELETE",
                "/k/v1/records.json",
                json={"app": arguments["app_id"], "ids": arguments["record_ids"]},
            )
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text or "{}")]

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
