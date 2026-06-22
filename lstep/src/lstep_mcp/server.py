import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

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
        # ── 友だち ──
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
            name="add_tag_to_friend",
            description="特定の友だち1人にタグを追加する",
            inputSchema={
                "type": "object",
                "properties": {
                    "friend_id": {"type": "string", "description": "友だちID"},
                    "tag_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "追加するタグIDのリスト",
                    },
                },
                "required": ["friend_id", "tag_ids"],
            },
        ),
        types.Tool(
            name="remove_tag_from_friend",
            description="特定の友だち1人からタグを削除する",
            inputSchema={
                "type": "object",
                "properties": {
                    "friend_id": {"type": "string", "description": "友だちID"},
                    "tag_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "削除するタグIDのリスト",
                    },
                },
                "required": ["friend_id", "tag_ids"],
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
        # ── 友だち情報 ──
        types.Tool(
            name="create_friend_info_folder",
            description="友だち情報フォルダを新規作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "フォルダ名"},
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="create_friend_info",
            description="友だち情報（カスタム属性項目）を新規作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "友だち情報名"},
                    "folder_id": {"type": "string", "description": "格納先フォルダID"},
                    "type": {
                        "type": "string",
                        "description": "データ型（text / number / date 等）",
                    },
                },
                "required": ["name"],
            },
        ),
        # ── タグ ──
        types.Tool(
            name="list_tag_folders",
            description="タグフォルダ一覧を取得する",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="create_tag_folder",
            description="タグフォルダを新規作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "フォルダ名"},
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="list_tags",
            description="タグ一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（最大50）", "default": 50},
                },
            },
        ),
        types.Tool(
            name="create_tag",
            description="新しいタグを作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "タグ名"},
                    "folder_id": {"type": "string", "description": "格納先フォルダID"},
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="update_tag",
            description="既存タグの名前・フォルダを更新する",
            inputSchema={
                "type": "object",
                "properties": {
                    "tag_id": {"type": "string", "description": "更新するタグID"},
                    "name": {"type": "string", "description": "新しいタグ名"},
                    "folder_id": {"type": "string", "description": "移動先フォルダID"},
                },
                "required": ["tag_id"],
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
        # ── 対応マーク ──
        types.Tool(
            name="list_taiou_marks",
            description="対応マーク一覧を取得する",
            inputSchema={"type": "object", "properties": {}},
        ),
        # ── メッセージ ──
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
        # ── 共通情報 ──
        types.Tool(
            name="list_common_info_folders",
            description="共通情報フォルダ一覧を取得する",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="list_common_infos",
            description="共通情報一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（最大50）", "default": 50},
                },
            },
        ),
        types.Tool(
            name="update_common_info",
            description="共通情報の値を更新する",
            inputSchema={
                "type": "object",
                "properties": {
                    "common_info_id": {"type": "string", "description": "共通情報ID"},
                    "value": {"type": "string", "description": "新しい値"},
                },
                "required": ["common_info_id", "value"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        return _dispatch(name, arguments)
    except Exception as exc:  # noqa: BLE001 — MCP では例外を意味のある文字列で返す
        return error_response(exc)


def _dispatch(name: str, arguments: dict) -> list[types.TextContent]:
    with get_client() as client:
        # ── 友だち ──
        if name == "list_friends":
            params = {"limit": arguments.get("limit", 50)}
            if cursor := arguments.get("cursor"):
                params["cursor"] = cursor
            r = client.get("/friends", params=params)

        elif name == "add_tag_to_friend":
            friend_id = arguments["friend_id"]
            r = client.post(f"/friends/{friend_id}/tags", json={"tag_ids": arguments["tag_ids"]})

        elif name == "remove_tag_from_friend":
            friend_id = arguments["friend_id"]
            r = client.request("DELETE", f"/friends/{friend_id}/tags", json={"tag_ids": arguments["tag_ids"]})

        elif name == "set_response_mark":
            friend_id = arguments["friend_id"]
            r = client.post(f"/friends/{friend_id}/taiou-mark", json={"taiou_mark_id": arguments["taiou_mark_id"]})

        # ── 友だち情報 ──
        elif name == "create_friend_info_folder":
            body = {"name": arguments["name"]}
            r = client.post("/friend-info-folders", json=body)

        elif name == "create_friend_info":
            body = {"name": arguments["name"]}
            if folder_id := arguments.get("folder_id"):
                body["folder_id"] = folder_id
            if info_type := arguments.get("type"):
                body["type"] = info_type
            r = client.post("/friend-infos", json=body)

        # ── タグ ──
        elif name == "list_tag_folders":
            r = client.get("/tag-folders")

        elif name == "create_tag_folder":
            r = client.post("/tag-folders", json={"name": arguments["name"]})

        elif name == "list_tags":
            r = client.get("/tags", params={"limit": arguments.get("limit", 50)})

        elif name == "create_tag":
            body = {"name": arguments["name"]}
            if folder_id := arguments.get("folder_id"):
                body["folder_id"] = folder_id
            r = client.post("/tags", json=body)

        elif name == "update_tag":
            tag_id = arguments["tag_id"]
            body = {}
            if name_ := arguments.get("name"):
                body["name"] = name_
            if folder_id := arguments.get("folder_id"):
                body["folder_id"] = folder_id
            r = client.post(f"/tags/{tag_id}", json=body)

        elif name == "list_friends_by_tag":
            tag_id = arguments["tag_id"]
            params = {"limit": arguments.get("limit", 50)}
            if cursor := arguments.get("cursor"):
                params["cursor"] = cursor
            r = client.get(f"/tags/{tag_id}/friends", params=params)

        elif name == "bulk_add_tag":
            tag_id = arguments["tag_id"]
            r = client.post(f"/tags/{tag_id}/friends", json={"friend_ids": arguments["friend_ids"]})

        elif name == "bulk_remove_tag":
            tag_id = arguments["tag_id"]
            r = client.request("DELETE", f"/tags/{tag_id}/friends", json={"friend_ids": arguments["friend_ids"]})

        # ── 対応マーク ──
        elif name == "list_taiou_marks":
            r = client.get("/taiou-marks")

        # ── メッセージ ──
        elif name == "get_message_history":
            params = {"limit": arguments.get("limit", 50)}
            if cursor := arguments.get("cursor"):
                params["cursor"] = cursor
            if direction := arguments.get("direction"):
                params["direction"] = direction
            r = client.get("/messages", params=params)

        # ── 共通情報 ──
        elif name == "list_common_info_folders":
            r = client.get("/common-info-folders")

        elif name == "list_common_infos":
            r = client.get("/common-infos", params={"limit": arguments.get("limit", 50)})

        elif name == "update_common_info":
            common_info_id = arguments["common_info_id"]
            r = client.post(f"/common-infos/{common_info_id}", json={"value": arguments["value"]})

        else:
            raise ValueError(f"未知のツール: {name}")

        r.raise_for_status()
        return format_response(r.json())


def main():
    import asyncio

    async def _run():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

    asyncio.run(_run())


if __name__ == "__main__":
    main()
