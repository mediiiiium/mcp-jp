import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("airtable-mcp")

BASE_URL = "https://api.airtable.com/v0"


def _client() -> httpx.Client:
    token = os.environ.get("AIRTABLE_API_TOKEN")
    if not token:
        raise ValueError("AIRTABLE_API_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_records",
            description="Airtable テーブルのレコード一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_id": {
                        "type": "string",
                        "description": "ベースID（app で始まるID、AirtableのURLから取得）",
                    },
                    "table_name": {
                        "type": "string",
                        "description": "テーブル名またはテーブルID",
                    },
                    "view": {
                        "type": "string",
                        "description": "ビュー名（例: Grid view）",
                    },
                    "max_records": {
                        "type": "integer",
                        "description": "最大取得件数（デフォルト20）",
                        "default": 20,
                    },
                    "filter_formula": {
                        "type": "string",
                        "description": "フィルター式（例: {Status}='完了', NOT({Name}='')）",
                    },
                    "sort_field": {
                        "type": "string",
                        "description": "ソートするフィールド名",
                    },
                    "sort_direction": {
                        "type": "string",
                        "description": "ソート方向（asc: 昇順, desc: 降順）",
                        "enum": ["asc", "desc"],
                        "default": "asc",
                    },
                    "offset": {
                        "type": "string",
                        "description": "ページネーション用オフセット（レスポンスの offset から取得）",
                    },
                },
                "required": ["base_id", "table_name"],
            },
        ),
        types.Tool(
            name="get_record",
            description="レコードIDを指定して Airtable のレコードを取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_id": {
                        "type": "string",
                        "description": "ベースID",
                    },
                    "table_name": {
                        "type": "string",
                        "description": "テーブル名またはテーブルID",
                    },
                    "record_id": {
                        "type": "string",
                        "description": "レコードID（rec で始まるID）",
                    },
                },
                "required": ["base_id", "table_name", "record_id"],
            },
        ),
        types.Tool(
            name="create_record",
            description="Airtable テーブルに新しいレコードを作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_id": {
                        "type": "string",
                        "description": "ベースID",
                    },
                    "table_name": {
                        "type": "string",
                        "description": "テーブル名またはテーブルID",
                    },
                    "fields": {
                        "type": "object",
                        "description": "レコードのフィールド値（例: {\"名前\": \"田中太郎\", \"ステータス\": \"進行中\"}）",
                    },
                },
                "required": ["base_id", "table_name", "fields"],
            },
        ),
        types.Tool(
            name="update_record",
            description="Airtable のレコードを更新する",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_id": {
                        "type": "string",
                        "description": "ベースID",
                    },
                    "table_name": {
                        "type": "string",
                        "description": "テーブル名またはテーブルID",
                    },
                    "record_id": {
                        "type": "string",
                        "description": "レコードID",
                    },
                    "fields": {
                        "type": "object",
                        "description": "更新するフィールド値",
                    },
                },
                "required": ["base_id", "table_name", "record_id", "fields"],
            },
        ),
        types.Tool(
            name="list_bases",
            description="アクセス可能な Airtable ベース（データベース）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "list_records":
        base_id = arguments["base_id"]
        table = arguments["table_name"]
        params: dict = {"maxRecords": arguments.get("max_records", 20)}
        if arguments.get("view"):
            params["view"] = arguments["view"]
        if arguments.get("filter_formula"):
            params["filterByFormula"] = arguments["filter_formula"]
        if arguments.get("sort_field"):
            params["sort[0][field]"] = arguments["sort_field"]
            params["sort[0][direction]"] = arguments.get("sort_direction", "asc")
        if arguments.get("offset"):
            params["offset"] = arguments["offset"]
        r = client.get(f"/{base_id}/{table}", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_record":
        base_id = arguments["base_id"]
        table = arguments["table_name"]
        rid = arguments["record_id"]
        r = client.get(f"/{base_id}/{table}/{rid}")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "create_record":
        base_id = arguments["base_id"]
        table = arguments["table_name"]
        body = {"fields": arguments["fields"]}
        r = client.post(f"/{base_id}/{table}", content=json.dumps(body))
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "update_record":
        base_id = arguments["base_id"]
        table = arguments["table_name"]
        rid = arguments["record_id"]
        body = {"fields": arguments["fields"]}
        r = client.patch(f"/{base_id}/{table}/{rid}", content=json.dumps(body))
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_bases":
        r = client.get("/meta/bases")
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
