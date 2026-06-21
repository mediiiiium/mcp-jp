import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("sansan-mcp")

BASE_URL = "https://api.sansan.com/v6.0"


def _client() -> httpx.Client:
    api_key = os.environ.get("SANSAN_API_KEY")
    if not api_key:
        raise ValueError("SANSAN_API_KEY が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={"X-Sansan-Api-Key": api_key},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_biz_cards",
            description="Sansan の名刺一覧を期間指定で取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "updated_from": {
                        "type": "string",
                        "description": "取得開始日時（RFC3339形式、例: 2024-01-01T00:00:00+09:00）",
                    },
                    "updated_to": {
                        "type": "string",
                        "description": "取得終了日時（RFC3339形式、例: 2024-12-31T23:59:59+09:00）",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "取得件数（最大100、デフォルト100）",
                        "default": 100,
                    },
                    "next_page_token": {
                        "type": "string",
                        "description": "次ページのトークン（hasMore=trueのときレスポンスから取得）",
                    },
                    "include_tags": {
                        "type": "boolean",
                        "description": "タグ情報を含める（デフォルト: false）",
                        "default": False,
                    },
                },
                "required": ["updated_from", "updated_to"],
            },
        ),
        types.Tool(
            name="search_biz_cards",
            description="Sansan の名刺を条件で検索する",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "会社名で検索（部分一致）",
                    },
                    "name": {
                        "type": "string",
                        "description": "氏名で検索（部分一致）",
                    },
                    "email": {
                        "type": "string",
                        "description": "メールアドレスで検索",
                    },
                    "tel": {
                        "type": "string",
                        "description": "電話番号で検索",
                    },
                    "mobile": {
                        "type": "string",
                        "description": "携帯電話番号で検索",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "取得件数（最大100、デフォルト20）",
                        "default": 20,
                    },
                    "next_page_token": {
                        "type": "string",
                        "description": "次ページのトークン",
                    },
                },
            },
        ),
        types.Tool(
            name="get_biz_card",
            description="名刺IDを指定して名刺の詳細情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "biz_card_id": {
                        "type": "string",
                        "description": "名刺ID",
                    },
                },
                "required": ["biz_card_id"],
            },
        ),
        types.Tool(
            name="get_person",
            description="人物IDを指定して人物の詳細情報を取得する（同一人物の複数名刺を統合した情報）",
            inputSchema={
                "type": "object",
                "properties": {
                    "person_id": {
                        "type": "string",
                        "description": "人物ID（名刺情報内のpersonIdフィールドから取得）",
                    },
                },
                "required": ["person_id"],
            },
        ),
        types.Tool(
            name="list_tags",
            description="Sansan のタグ一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "タグ名で絞り込み",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "取得件数（最大100、デフォルト50）",
                        "default": 50,
                    },
                    "next_page_token": {
                        "type": "string",
                        "description": "次ページのトークン",
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "list_biz_cards":
        params: dict = {
            "updatedFrom": arguments["updated_from"],
            "updatedTo": arguments["updated_to"],
            "limit": arguments.get("limit", 100),
        }
        if arguments.get("next_page_token"):
            params["nextPageToken"] = arguments["next_page_token"]
        if arguments.get("include_tags"):
            params["includeTags"] = "true"
        r = client.get("/bizCards", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "search_biz_cards":
        params = {"limit": arguments.get("limit", 20)}
        for field, param in [
            ("company_name", "companyName"),
            ("name", "name"),
            ("email", "email"),
            ("tel", "tel"),
            ("mobile", "mobile"),
        ]:
            if arguments.get(field):
                params[param] = arguments[field]
        if arguments.get("next_page_token"):
            params["nextPageToken"] = arguments["next_page_token"]
        r = client.get("/bizCards/search", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_biz_card":
        card_id = arguments["biz_card_id"]
        r = client.get(f"/bizCards/{card_id}")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_person":
        person_id = arguments["person_id"]
        r = client.get(f"/persons/{person_id}")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_tags":
        params = {"limit": arguments.get("limit", 50)}
        if arguments.get("name"):
            params["name"] = arguments["name"]
        if arguments.get("next_page_token"):
            params["nextPageToken"] = arguments["next_page_token"]
        r = client.get("/tags", params=params)
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
