import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("base-ec-mcp")

BASE_URL = "https://api.thebase.in/1"


def _client() -> httpx.Client:
    token = os.environ.get("BASE_ACCESS_TOKEN")
    if not token:
        raise ValueError("BASE_ACCESS_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_shop",
            description=(
                "接続中のBASEショップの基本情報（ショップ名、URL、紹介文、ロゴ画像URL、"
                "Twitter/Facebook/Instagram/YouTube/TikTokの各アカウントID等）を取得する。"
                "パラメータは不要で、常に自分自身のショップ1件分の情報のみを返す（他ショップの情報は取得できない）。"
                "どのショップに接続しているか確認したい場合や、メッセージ文面にショップ名・URLを差し込みたい場合に使う。"
                "メールアドレスは read_users_mail スコープが付与されたトークンでないと含まれない。"
                "読み取り専用ツールであり、ショップ情報を更新するAPI自体がBASEに公開されていないため、"
                "変更は管理画面から行う必要がある。"
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="list_items",
            description=(
                "BASEショップに登録されている商品の一覧を、価格・在庫数・画像URL・バリエーション（サイズ/色等）"
                "まで含めて取得する。商品の棚卸しや、在庫確認、特定カテゴリの商品抽出などに使う。"
                "1回のリクエストで最大100件（未指定時は20件）。ページネーションはoffset方式で、"
                "続きを取得するには前回の offset + limit を次回の offset に指定する（カーソル方式ではなく、"
                "レスポンスに総件数は含まれないため、空配列が返るまでoffsetを増やし続けて取得する）。"
                "既定の並び順は list_order（管理画面での表示順）昇順。書き込みは行わない。"
                "BASE APIには商品の新規作成・編集・削除エンドポイント（items/add, items/edit, items/delete等）も"
                "存在するが、本コネクタでは未実装のため一覧取得のみ可能。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "取得件数（最大100、既定20）",
                        "default": 20,
                    },
                    "offset": {
                        "type": "integer",
                        "description": "取得開始位置（既定0）。次ページを取るには前回の offset + limit を指定する",
                        "default": 0,
                    },
                    "order": {
                        "type": "string",
                        "description": "ソート項目（list_order: 管理画面の並び順 / created: 作成日 / modified: 更新日、既定 list_order）",
                        "enum": ["list_order", "created", "modified"],
                    },
                    "sort": {
                        "type": "string",
                        "description": "ソート方向（asc: 昇順, desc: 降順、既定 asc）",
                        "enum": ["asc", "desc"],
                    },
                    "visible": {
                        "type": "integer",
                        "description": "公開状態で絞り込み（1: 公開中の商品のみ, 0: 非公開の商品のみ。省略時は両方）",
                        "enum": [0, 1],
                    },
                    "category_id": {
                        "type": "integer",
                        "description": "このカテゴリIDに属する商品のみに絞り込む",
                    },
                },
            },
        ),
        types.Tool(
            name="list_orders",
            description=(
                "BASEショップの注文一覧を、注文日・合計金額・発送状況（dispatch_status）等のサマリ情報で取得する。"
                "「今月の注文を確認したい」「未発送の注文がどれだけあるか把握したい」といった全体把握に使う。"
                "個々の注文の明細（購入商品・購入者情報・決済詳細等）が必要な場合は get_order を使う。"
                "1回のリクエストで最大100件（未指定時は20件）。ページネーションはoffset方式で、"
                "続きを取得するには前回の offset + limit を次回の offset に指定する（レスポンスに総件数は"
                "含まれない）。並び順はAPI側で明示的に文書化されていない。start_ordered/end_ordered による"
                "絞り込みは注文日時ベースであり、更新日時での絞り込みには対応していない。発送状況（dispatch_status）"
                "による絞り込みもAPI側でサポートされていないため、状態で絞りたい場合は取得結果をこのツールの"
                "呼び出し側で確認する必要がある。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "取得件数（最大100、既定20）",
                        "default": 20,
                    },
                    "offset": {
                        "type": "integer",
                        "description": "取得開始位置（既定0）。次ページを取るには前回の offset + limit を指定する",
                        "default": 0,
                    },
                    "start_ordered": {
                        "type": "string",
                        "description": "注文日時の範囲開始（yyyy-mm-dd または yyyy-mm-dd hh:mm:ss 形式）。更新日時ではなく注文日時での絞り込み。",
                    },
                    "end_ordered": {
                        "type": "string",
                        "description": "注文日時の範囲終了（yyyy-mm-dd または yyyy-mm-dd hh:mm:ss 形式）",
                    },
                },
            },
        ),
        types.Tool(
            name="get_order",
            description=(
                "1件の注文の詳細情報を、購入者情報・配送先・決済方法・購入商品明細（order_items、各商品行の"
                "order_item_id と個別ステータスを含む）まで展開して取得する。list_orders はサマリのみのため、"
                "注文内容の確認や、update_order_status に渡す order_item_id を調べる目的で使う。"
                "unique_key は list_orders のレスポンスに含まれる注文単位の識別子（order_item_id とは別物）。"
                "1件取得のみでページネーションはない。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "unique_key": {
                        "type": "string",
                        "description": "注文の一意キー（list_orders のレスポンスの unique_key）",
                    },
                },
                "required": ["unique_key"],
            },
        ),
        types.Tool(
            name="update_order_status",
            description=(
                "注文内の商品行（order_item_id で指定する個別の購入明細。注文全体を指す unique_key ではない）"
                "のステータスを更新する。order_item_id は get_order のレスポンスの order_items[].order_item_id "
                "から取得する。ステータス遷移は ordered → dispatched（発送済み）または ordered → cancelled"
                "（キャンセル）のみ許可されており、BASE側の業務ルール上それ以外の遷移（例: 一度発送済みにした"
                "行を再度変更する等）は失敗する。すなわち、この操作はべき等ではない — 同じ order_item_id に"
                "対して同じステータス変更を再実行するとエラーになる可能性がある。add_comment を指定すると、"
                "発送通知メールに追記されるメッセージを設定できる（最大250文字）。後払い決済の入金確認"
                "（atobarai_status）や配送会社・追跡番号の登録は本コネクタでは未実装。注文自体の削除・"
                "新規作成に対応するAPIはBASEに存在しない（注文は購入者のチェックアウトによってのみ作成される）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "order_item_id": {
                        "type": "integer",
                        "description": "更新対象の購入明細ID（get_order の order_items[].order_item_id）。注文全体の unique_key ではない点に注意。",
                    },
                    "status": {
                        "type": "string",
                        "description": "更新後のステータス（dispatched: 発送済みに変更 / cancelled: キャンセル。ordered からの遷移のみ許可）",
                        "enum": ["dispatched", "cancelled"],
                    },
                    "add_comment": {
                        "type": "string",
                        "description": "発送通知メールに追記するメッセージ（任意、改行含め最大250文字）",
                    },
                },
                "required": ["order_item_id", "status"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "get_shop":
                r = client.get("/users/me")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_items":
                params: dict = {
                    "limit": arguments.get("limit", 20),
                    "offset": arguments.get("offset", 0),
                }
                if arguments.get("order"):
                    params["order"] = arguments["order"]
                if arguments.get("sort"):
                    params["sort"] = arguments["sort"]
                if "visible" in arguments:
                    params["visible"] = arguments["visible"]
                if arguments.get("category_id") is not None:
                    params["category_id"] = arguments["category_id"]
                r = client.get("/items", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_orders":
                params = {
                    "limit": arguments.get("limit", 20),
                    "offset": arguments.get("offset", 0),
                }
                if arguments.get("start_ordered"):
                    params["start_ordered"] = arguments["start_ordered"]
                if arguments.get("end_ordered"):
                    params["end_ordered"] = arguments["end_ordered"]
                r = client.get("/orders", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_order":
                key = arguments["unique_key"]
                r = client.get(f"/orders/detail/{key}")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "update_order_status":
                data = {
                    "order_item_id": arguments["order_item_id"],
                    "status": arguments["status"],
                }
                if arguments.get("add_comment"):
                    data["add_comment"] = arguments["add_comment"]
                r = client.post("/orders/edit_status", data=data)
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
