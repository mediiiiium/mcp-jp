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
            description=(
                "友だち（LINE公式アカウントを追加したユーザー）の一覧を、付与済みタグ・友だち情報（カスタム属性）・"
                "対応マークを展開した状態で取得する。配信対象の確認や顧客属性の棚卸しなど、全体像の把握に使う。"
                "1回のリクエストで最大1000件まで取得可能（limit 未指定時は50件）。続きを取るには前回レスポンスの "
                "next_cursor を cursor に渡す（cursor 未指定時は先頭から）。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（最大1000、既定50）", "default": 50},
                    "cursor": {"type": "string", "description": "前回レスポンスの next_cursor を渡すとその続きから取得する"},
                },
            },
        ),
        types.Tool(
            name="add_tag_to_friend",
            description=(
                "友だち1人にタグを1件以上まとめて付与する。既に付与済みのタグIDを含めても重複エラーにはならず"
                "無視される（べき等）。対象が複数人いる場合は bulk_add_tag を使う方が効率的。"
            ),
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
            description=(
                "友だち1人からタグを1件以上まとめて解除する。付与されていないタグIDを含めてもエラーにはならず"
                "無視される（べき等）。対象が複数人いる場合は bulk_remove_tag を使う方が効率的。"
                "タグそのものの削除はできない（create_tag / update_tag はあるが削除APIは提供されていない）。"
            ),
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
            description=(
                "友だち1人の対応マーク（「対応済み」「未対応」等、問い合わせ対応状況を示す管理画面上のラベル）を"
                "1件設定する。既存のマークは上書きされる（対応マークIDは list_taiou_marks で確認する）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "friend_id": {"type": "string", "description": "友だちID"},
                    "taiou_mark_id": {"type": "string", "description": "対応マークID（list_taiou_marks で取得）"},
                },
                "required": ["friend_id", "taiou_mark_id"],
            },
        ),
        # ── 友だち情報 ──
        types.Tool(
            name="create_friend_info_folder",
            description=(
                "友だち情報（友だちごとのカスタム属性項目）を整理するためのフォルダを新規作成する。"
                "作成できるのみで、削除・更新のAPIは提供されていない。"
            ),
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
            description=(
                "友だち情報（例: 誕生日、購入回数など友だちごとに値が異なるカスタム属性項目）の定義を新規作成する。"
                "ここで作るのは項目の定義であり、個々の友だちへの値の設定は別途行う必要がある（本コネクタには"
                "友だちごとの値設定・削除ツールは未実装）。folder_id を省略すると未分類フォルダに入る。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "友だち情報名"},
                    "folder_id": {"type": "string", "description": "格納先フォルダID（省略時は未分類）"},
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
            description="タグフォルダの一覧を取得する。ページネーションなし（全件を一度に返す）。",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="create_tag_folder",
            description="タグフォルダを新規作成する。削除・更新のAPIは提供されていない。",
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
            description=(
                "登録済みタグの一覧を、タグID・名前・所属フォルダとともに取得する。友だちへの付与・解除の前に"
                "タグIDを確認する目的で使うことが多い。1回のリクエストで最大1000件（既定50件）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（最大1000、既定50）", "default": 50},
                },
            },
        ),
        types.Tool(
            name="create_tag",
            description="新しいタグを作成する。folder_id を省略すると未分類フォルダに入る。削除APIは提供されていない。",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "タグ名"},
                    "folder_id": {"type": "string", "description": "格納先フォルダID（省略時は未分類）"},
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="update_tag",
            description=(
                "既存タグの名前・所属フォルダを部分更新する（name・folder_id とも省略した項目は変更されない）。"
                "タグ自体の削除はできない（削除APIが提供されていないため）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "tag_id": {"type": "string", "description": "更新するタグID"},
                    "name": {"type": "string", "description": "新しいタグ名（省略時は変更しない）"},
                    "folder_id": {"type": "string", "description": "移動先フォルダID（省略時は変更しない）"},
                },
                "required": ["tag_id"],
            },
        ),
        types.Tool(
            name="list_friends_by_tag",
            description=(
                "指定タグが付与されている友だちの一覧を取得する。「このタグの対象者に一斉送信したい」"
                "「セグメント人数を確認したい」といった場面で使う。ページネーションはカーソル方式："
                "続きを取るには前回レスポンスの next_cursor を cursor に渡す。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "tag_id": {"type": "string", "description": "タグID"},
                    "limit": {"type": "integer", "description": "取得件数（最大1000、既定50）", "default": 50},
                    "cursor": {"type": "string", "description": "前回レスポンスの next_cursor を渡すとその続きから取得する"},
                },
                "required": ["tag_id"],
            },
        ),
        types.Tool(
            name="bulk_add_tag",
            description=(
                "1件のタグを複数の友だちへ一括付与する。既に付与済みの友だちが含まれていてもエラーにはならず"
                "無視される（べき等）。対象が1人だけなら add_tag_to_friend の方がシンプル。"
            ),
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
            description=(
                "1件のタグを複数の友だちから一括解除する。付与されていない友だちが含まれていてもエラーにはならず"
                "無視される（べき等）。対象が1人だけなら remove_tag_from_friend の方がシンプル。"
            ),
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
            description=(
                "対応マーク（問い合わせ対応状況を示す管理画面上のラベル。例: 対応済み/未対応）の一覧をIDと"
                "名前付きで取得する。set_response_mark に渡す taiou_mark_id を調べる目的で使う。"
                "ページネーションなし（全件を一度に返す）。"
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        # ── メッセージ ──
        types.Tool(
            name="get_message_history",
            description=(
                "友だちとのLINEメッセージ履歴（受信・送信・システムメッセージ）を検索・取得する。"
                "既定では送信日時の新しい順（sort_order=desc）に返る。特定の友だちとのやり取りだけを見たい場合は"
                "friend_id を指定する。期間で絞り込むには sent_at_from / sent_at_to（ISO 8601形式）を使う。"
                "1回のリクエストで最大1000件（既定50件）。続きを取るには前回レスポンスの next_cursor を "
                "cursor に渡す（このエンドポイントは前ページへの遡り取得には対応していない）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（最大1000、既定50）", "default": 50},
                    "cursor": {"type": "string", "description": "前回レスポンスの next_cursor を渡すとその続きから取得する"},
                    "friend_id": {"type": "string", "description": "この友だちとのメッセージのみに絞り込む"},
                    "direction": {
                        "type": "string",
                        "enum": ["inbound", "outbound", "system"],
                        "description": "メッセージ方向で絞り込む（inbound=友だちからの受信 / outbound=こちらからの送信 / system=システム通知）",
                    },
                    "sent_at_from": {"type": "string", "description": "送信日時の範囲開始（ISO 8601形式、例: 2026-06-01T00:00:00+09:00）"},
                    "sent_at_to": {"type": "string", "description": "送信日時の範囲終了（ISO 8601形式）"},
                    "sort_order": {
                        "type": "string",
                        "enum": ["asc", "desc"],
                        "description": "送信日時での並び順（既定 desc=新しい順）",
                        "default": "desc",
                    },
                    "is_unconfirmed": {"type": "boolean", "description": "true の場合、未読メッセージのみに絞り込む"},
                },
            },
        ),
        # ── 共通情報 ──
        types.Tool(
            name="list_common_info_folders",
            description=(
                "共通情報フォルダの一覧を取得する（共通情報とは何かは list_common_infos の説明を参照）。"
                "ページネーションなし（全件を一度に返す）。id が null の要素は未分類フォルダを表す。"
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="list_common_infos",
            description=(
                "共通情報（特定の友だちに紐づかず、アカウント全体で共有される固定値。例: 営業時間・定休日・"
                "問い合わせ先URLなど）の一覧を取得する。友だち情報（friend_info、友だちごとに値が異なる属性）とは"
                "別物。各要素は配信テンプレートやメッセージ本文からショートコード（shortcode_id）経由で差し込める。"
                "folder_id を指定するとそのフォルダ内のみに絞り込み、null を指定すると未分類フォルダのみになる。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（最大1000、既定50）", "default": 50},
                    "cursor": {"type": "string", "description": "前回レスポンスの next_cursor を渡すとその続きから取得する"},
                    "folder_id": {"type": "string", "description": "絞り込み対象のフォルダID（省略時は全フォルダ、null 指定で未分類のみ）"},
                },
            },
        ),
        types.Tool(
            name="update_common_info",
            description=(
                "共通情報（アカウント全体で共有される固定値。list_common_infos 参照）1件の値を更新する。"
                "反映後は、そのショートコードを使っている配信テンプレート・メッセージにも新しい値が反映される。"
                "共通情報の新規作成・削除のAPIは提供されていない。"
            ),
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
            if friend_id := arguments.get("friend_id"):
                params["friend_id"] = friend_id
            if direction := arguments.get("direction"):
                params["direction"] = direction
            if sent_at_from := arguments.get("sent_at_from"):
                params["sent_at_from"] = sent_at_from
            if sent_at_to := arguments.get("sent_at_to"):
                params["sent_at_to"] = sent_at_to
            if sort_order := arguments.get("sort_order"):
                params["sort_order"] = sort_order
            if "is_unconfirmed" in arguments:
                params["is_unconfirmed"] = arguments["is_unconfirmed"]
            r = client.get("/messages", params=params)

        # ── 共通情報 ──
        elif name == "list_common_info_folders":
            r = client.get("/common-info-folders")

        elif name == "list_common_infos":
            params = {"limit": arguments.get("limit", 50)}
            if cursor := arguments.get("cursor"):
                params["cursor"] = cursor
            if "folder_id" in arguments:
                params["folder_id"] = arguments["folder_id"]
            r = client.get("/common-infos", params=params)

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
