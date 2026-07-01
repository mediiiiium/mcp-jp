import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("trello-mcp")
BASE_URL = "https://api.trello.com/1"


def _params() -> dict:
    api_key = os.environ.get("TRELLO_API_KEY")
    token = os.environ.get("TRELLO_TOKEN")
    if not api_key:
        raise ValueError("TRELLO_API_KEY が設定されていません")
    if not token:
        raise ValueError("TRELLO_TOKEN が設定されていません")
    return {"key": api_key, "token": token}


def _client() -> httpx.Client:
    return httpx.Client(base_url=BASE_URL, timeout=30)


BOARD_FILTER_ENUM = ["none", "members", "organization", "public", "open", "closed", "all"]
OPEN_CLOSED_ALL_ENUM = ["open", "closed", "all"]


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_boards",
            description=(
                "自分（このトークンのユーザー）が所属するボード一覧を取得する。他のツールに渡す board_id "
                "を調べる起点として使う。filter を省略した場合、Trello API の既定値は all（オープン・"
                "アーカイブ済み双方を含む全ボード）。ページネーションカーソル（before/since）は無く、"
                "該当するボードを1回のレスポンスで配列として全件返す（Trello 側に件数上限の明記は無い）。"
                "読み取り専用。ボードの作成・更新（名前変更・アーカイブ）・削除エンドポイントも Trello API "
                "には存在するが、本コネクタには実装していない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {
                        "type": "string",
                        "enum": BOARD_FILTER_ENUM,
                        "description": (
                            "絞り込み条件。open=未アーカイブのみ、closed=アーカイブ済みのみ、all=両方、"
                            "members/organization/public は所属種別による絞り込み。省略時はAPI既定の all"
                            "（アーカイブ済みも含む全件）。"
                        ),
                    },
                },
            },
        ),
        types.Tool(
            name="list_lists",
            description=(
                "指定したボード内のリスト（カンバンの列。例: 未着手/進行中/完了）一覧を取得する。カードを"
                "作成・移動する前に対象リストの list_id を確認する目的でよく使う。filter を省略すると "
                "Trello API 既定の open（未アーカイブのリストのみ）が適用され、アーカイブ済みリストは含ま"
                "れない点に注意（closed や all を指定すると取得できる）。ページネーションカーソルは無く、"
                "該当するリストを1回のレスポンスで配列として全件返す。読み取り専用。リストの新規作成・"
                "名前変更・アーカイブ・別ボードへの移動エンドポイントも Trello API には存在するが、本"
                "コネクタには実装していない。また Trello にはリストの削除エンドポイント自体が無く（アーカ"
                "イブのみ可能）、UI上の「削除」もアーカイブ後のみ操作できる。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "board_id": {"type": "string", "description": "ボードID（list_boards で確認）"},
                    "filter": {
                        "type": "string",
                        "enum": OPEN_CLOSED_ALL_ENUM,
                        "description": (
                            "絞り込み条件。open=未アーカイブのみ（省略時のAPI既定値）、closed=アーカイブ"
                            "済みのみ、all=両方。"
                        ),
                    },
                },
                "required": ["board_id"],
            },
        ),
        types.Tool(
            name="list_cards",
            description=(
                "指定したリスト内のカード一覧を取得する。filter を省略すると Trello API 既定の open"
                "（未アーカイブのカードのみ）が適用され、アーカイブ済みカードは含まれない点に注意（closed "
                "や all を指定すると取得できる）。ページネーションカーソル（before/since）は無く、該当する"
                "カードを1回のレスポンスで配列として全件返す。カード数が非常に多いリストでは応答が大きく"
                "なり、本コネクタの共通処理により20,000文字を超える分は切り詰められる（その場合はボードを"
                "分けるか filter で絞り込むこと）。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "list_id": {"type": "string", "description": "リストID（list_lists で確認）"},
                    "filter": {
                        "type": "string",
                        "enum": OPEN_CLOSED_ALL_ENUM,
                        "description": (
                            "絞り込み条件。open=未アーカイブのみ（省略時のAPI既定値）、closed=アーカイブ"
                            "済みのみ、all=両方。"
                        ),
                    },
                },
                "required": ["list_id"],
            },
        ),
        types.Tool(
            name="create_card",
            description=(
                "指定したリストに新しいカードを1枚作成する。list_id と name が必須（作成先のリストIDは"
                "list_lists で確認する）。desc（説明）・due（期限日時、ISO 8601）・start（開始日時、ISO "
                "8601）・idMembers（担当者として割り当てるメンバーIDの配列）・idLabels（付与するラベルID"
                "の配列）・pos（位置。top/bottom または数値、省略時はリスト末尾）は省略可能。呼び出すたび"
                "に新規カードが作成され、重複防止（べき等性）の仕組みは Trello API 側にない。同じ内容で"
                "誤って複数回呼び出すと同名カードが重複して作成されるため、実行前に list_cards で既存"
                "カードの有無を確認することを推奨する。作成後のカードの名前・説明・期限・担当者・ラベル"
                "変更やアーカイブは move_card 同様に PUT /1/cards/{id} で可能だが、list_id（所属リスト）"
                "以外のフィールドを更新するツールは本コネクタには実装していない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "list_id": {"type": "string", "description": "カードを追加するリストID（list_lists で確認）"},
                    "name": {"type": "string", "description": "カード名（必須）"},
                    "desc": {"type": "string", "description": "カードの説明（省略可）"},
                    "due": {"type": "string", "description": "期限日時（ISO 8601形式、省略可）"},
                    "start": {"type": "string", "description": "開始日時（ISO 8601形式、省略可）"},
                    "idMembers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "担当者として割り当てるメンバーIDの配列（省略可）",
                    },
                    "idLabels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "付与するラベルIDの配列（省略可）",
                    },
                    "pos": {
                        "type": "string",
                        "description": "リスト内でのカード位置。top・bottom または数値文字列（省略時はリスト末尾）",
                    },
                },
                "required": ["list_id", "name"],
            },
        ),
        types.Tool(
            name="move_card",
            description=(
                "既存のカードを別のリストへ移動する（PUT /1/cards/{id} の idList のみを更新する）。同じ "
                "list_id を指定して繰り返し呼び出しても結果は変わらないため冪等な操作。移動先が別ボードの"
                "リストであっても Trello 側で自動的にボード間移動として扱われる。名前・説明・期限・担当者"
                "・ラベルなど他フィールドの更新、カードのアーカイブ（closed=true）、完全削除（DELETE "
                "/1/cards/{id}。アーカイブと異なり元に戻せず、コメントや添付ファイルも含めて完全に消去され"
                "る）を行うエンドポイントも Trello API には存在するが、本コネクタには実装していない"
                "（必要な場合は Trello の管理画面から操作する）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "card_id": {"type": "string", "description": "移動するカードのID"},
                    "list_id": {"type": "string", "description": "移動先リストID（list_lists で確認）"},
                },
                "required": ["card_id", "list_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            auth = _params()

            if name == "list_boards":
                params = {**auth}
                if arguments.get("filter"):
                    params["filter"] = arguments["filter"]
                r = client.get("/members/me/boards", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_lists":
                board_id = arguments["board_id"]
                params = {**auth}
                if arguments.get("filter"):
                    params["filter"] = arguments["filter"]
                r = client.get(f"/boards/{board_id}/lists", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_cards":
                list_id = arguments["list_id"]
                params = {**auth}
                if arguments.get("filter"):
                    params["filter"] = arguments["filter"]
                r = client.get(f"/lists/{list_id}/cards", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "create_card":
                params = {**auth, "idList": arguments["list_id"], "name": arguments["name"]}
                if arguments.get("desc"):
                    params["desc"] = arguments["desc"]
                if arguments.get("due"):
                    params["due"] = arguments["due"]
                if arguments.get("start"):
                    params["start"] = arguments["start"]
                if arguments.get("idMembers"):
                    params["idMembers"] = ",".join(arguments["idMembers"])
                if arguments.get("idLabels"):
                    params["idLabels"] = ",".join(arguments["idLabels"])
                if arguments.get("pos"):
                    params["pos"] = arguments["pos"]
                r = client.post("/cards", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "move_card":
                card_id = arguments["card_id"]
                params = {**auth, "idList": arguments["list_id"]}
                r = client.put(f"/cards/{card_id}", params=params)
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
