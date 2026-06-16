import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

BASE_URL = "https://lineml.jp/v2/api"

app = Server("lstep-mcp")


def get_client() -> httpx.Client:
    token = os.environ.get("LSTEP_API_TOKEN")
    if not token:
        raise ValueError("LSTEP_API_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_tags",
            description="Lステップのタグ一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（最大50）", "default": 50},
                },
            },
        ),
        types.Tool(
            name="list_friends",
            description="友だち一覧を取得する（タグ・友だち情報付き）",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（最大50）", "default": 50},
                    "cursor": {"type": "string", "description": "ページネーション用カーソル"},
                },
            },
        ),
        types.Tool(
            name="list_friends_by_tag",
            description="指定タグを持つ友だち一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "tag_id": {"type": "string", "description": "タグID"},
                    "limit": {"type": "integer", "description": "取得件数（最大50）", "default": 50},
                    "cursor": {"type": "string", "description": "ページネーション用カーソル"},
                },
                "required": ["tag_id"],
            },
        ),
        types.Tool(
            name="bulk_add_tag",
            description="複数の友だちに一括でタグを付与する",
            inputSchema={
                "type": "object",
                "properties": {
                    "tag_id": {"type": "string", "description": "付与するタグID"},
                    "friend_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "対象の友だちIDリスト",
                    },
                },
                "required": ["tag_id", "friend_ids"],
            },
        ),
        types.Tool(
            name="bulk_remove_tag",
            description="複数の友だちから一括でタグを削除する",
            inputSchema={
                "type": "object",
                "properties": {
                    "tag_id": {"type": "string", "description": "削除するタグID"},
                    "friend_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "対象の友だちIDリスト",
                    },
                },
                "required": ["tag_id", "friend_ids"],
            },
        ),
        types.Tool(
            name="get_message_history",
            description="メッセージ履歴を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（最大50）", "default": 50},
                    "cursor": {"type": "string", "description": "ページネーション用カーソル"},
                    "direction": {
                        "type": "string",
                        "enum": ["inbound", "outbound", "system"],
                        "description": "メッセージ方向（受信/送信/システム）",
                    },
                },
            },
        ),
        types.Tool(
            name="set_response_mark",
            description="友だちの対応マークを設定する",
            inputSchema={
                "type": "object",
                "properties": {
                    "friend_id": {"type": "string", "description": "友だちID"},
                    "taiou_mark_id": {"type": "string", "description": "対応マークID"},
                },
                "required": ["friend_id", "taiou_mark_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    with get_client() as client:
        if name == "list_tags":
            params = {"limit": arguments.get("limit", 50)}
            r = client.get("/tags", params=params)
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "list_friends":
            params = {"limit": arguments.get("limit", 50)}
            if cursor := arguments.get("cursor"):
                params["cursor"] = cursor
            r = client.get("/friends", params=params)
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "list_friends_by_tag":
            tag_id = arguments["tag_id"]
            params = {"limit": arguments.get("limit", 50)}
            if cursor := arguments.get("cursor"):
                params["cursor"] = cursor
            r = client.get(f"/tags/{tag_id}/friends", params=params)
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "bulk_add_tag":
            tag_id = arguments["tag_id"]
            r = client.post(f"/tags/{tag_id}/friends", json={"friend_ids": arguments["friend_ids"]})
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "bulk_remove_tag":
            tag_id = arguments["tag_id"]
            r = client.request("DELETE", f"/tags/{tag_id}/friends", json={"friend_ids": arguments["friend_ids"]})
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "get_message_history":
            params = {"limit": arguments.get("limit", 50)}
            if cursor := arguments.get("cursor"):
                params["cursor"] = cursor
            if direction := arguments.get("direction"):
                params["direction"] = direction
            r = client.get("/messages", params=params)
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "set_response_mark":
            friend_id = arguments["friend_id"]
            r = client.post(
                f"/friends/{friend_id}/taiou-mark",
                json={"taiou_mark_id": arguments["taiou_mark_id"]},
            )
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        else:
            raise ValueError(f"未知のツール: {name}")


def main():
    import asyncio
    asyncio.run(stdio_server(app))


if __name__ == "__main__":
    main()
