import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("notepm-mcp")


def _client() -> httpx.Client:
    team_domain = os.environ.get("NOTEPM_TEAM_DOMAIN")
    access_token = os.environ.get("NOTEPM_ACCESS_TOKEN")
    if not team_domain:
        raise ValueError("NOTEPM_TEAM_DOMAIN が設定されていません")
    if not access_token:
        raise ValueError("NOTEPM_ACCESS_TOKEN が設定されていません")
    return httpx.Client(
        base_url=f"https://{team_domain}.notepm.jp/api/v1",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_notes",
            description=(
                "ノート（NotePM上でページをグルーピングする「フォルダ」に近い単位。他コネクタの"
                "「スペース」「プロジェクト」に相当）の一覧を取得する。各ノートの note_code・名前・"
                "公開範囲（scope）・所属グループ／ユーザーを確認する用途で使う。ページングは page/per_page"
                "方式（カーソル方式ではない）で、既定20件・最大100件。レスポンスの total・next_page・"
                "previous_page で総件数・次/前ページの有無を判定する。include_archived を true にすると"
                "アーカイブ済みノートも含める（既定は含まない）。書き込みは行わない。なお NotePM API には"
                "ノートの作成・更新・削除・アーカイブ化/復元エンドポイントも存在するが、本コネクタでは"
                "参照系のみに対応しており、それらは未実装。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり、既定1）", "default": 1},
                    "per_page": {
                        "type": "integer",
                        "description": "1ページあたりの件数（最大100、既定20）。総件数・次ページ有無はレスポンスの total / next_page で確認する。",
                        "default": 20,
                    },
                    "include_archived": {
                        "type": "boolean",
                        "description": "true にするとアーカイブ済みノートも一覧に含める（既定は含まない）",
                        "default": False,
                    },
                },
            },
        ),
        types.Tool(
            name="search_pages",
            description=(
                "ページを検索・一覧取得する（NotePM APIでは検索専用エンドポイントは存在せず、GET /pages が"
                "検索とページ一覧取得を兼ねている。条件を何も指定しなければ全ノート横断で最新のページ一覧が"
                "返る）。q でキーワード検索、note_code で特定ノート内に絞り込み、tag_name でタグ絞り込みが"
                "でき、複数条件は AND として扱われる。only_title を true にするとタイトルのみを検索対象にする"
                "（既定は本文も含めて検索）。created は名前に反して日付ではなく「作成者（ユーザーコード）で"
                "絞り込む」パラメータなので注意。include_archived を true にするとアーカイブ済みページも含める"
                "（既定は含まない）。並び順（ソート）はAPIドキュメントに明記がなく、本コネクタからは指定できない。"
                "ページングは page/per_page 方式（既定20件・最大100件）で、レスポンスの total・next_page・"
                "previous_page から次ページの有無や総件数を確認する。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "q": {"type": "string", "description": "検索キーワード（タイトル・本文が対象。省略可）"},
                    "note_code": {"type": "string", "description": "特定ノート内のみ検索する場合のノートコード（list_notes で取得）"},
                    "tag_name": {"type": "string", "description": "タグ名で絞り込む"},
                    "only_title": {
                        "type": "boolean",
                        "description": "true にするとタイトルのみを検索対象にする（既定は本文も含めて検索）",
                    },
                    "created": {
                        "type": "string",
                        "description": "作成者（ユーザーコード）で絞り込む。パラメータ名は created だが日付指定ではない点に注意。",
                    },
                    "include_archived": {
                        "type": "boolean",
                        "description": "true にするとアーカイブ済みページも検索対象に含める（既定は含まない）",
                        "default": False,
                    },
                    "page": {"type": "integer", "description": "ページ番号（1始まり、既定1）", "default": 1},
                    "per_page": {
                        "type": "integer",
                        "description": "1ページあたりの件数（最大100、既定20）。総件数・次ページ有無はレスポンスの total / next_page で確認する。",
                        "default": 20,
                    },
                },
            },
        ),
        types.Tool(
            name="get_page",
            description=(
                "ページコードを指定して1件のページ詳細（本文・タグ・所属ノート・コメント一覧を含む）を取得する。"
                "条件で候補を探す場合は search_pages を先に使う。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page_code": {"type": "string", "description": "ページコード（search_pages のレスポンス等で確認できる）"},
                },
                "required": ["page_code"],
            },
        ),
        types.Tool(
            name="create_page",
            description=(
                "指定したノート配下に新しいページを作成する。呼び出すたびに新しいページコードを持つ別ページが"
                "作成され、NotePM API側に重複防止の仕組みはない（べき等ではない。同じ内容で複数回呼ぶと同じ"
                "ページが複数作成される）。title は最大100文字、memo（通知や変更履歴に表示される一言メモ）は"
                "最大255文字までの制限がある。folder_id を指定するとノート内の特定フォルダに格納でき、"
                "省略するとノート直下に作成される。作成後に内容を直したい場合は update_page を使う。"
                "NotePM API自体にはページ削除エンドポイント（DELETE .../pages/:page_code）が存在するが、"
                "誤削除防止のため本コネクタには削除ツールを実装していない（削除は NotePM の Web UI から行う）。"
                "また API にはページ作成者・作成日時を上書きするパラメータ（user / created_at、主にデータ移行"
                "用途）も存在するが、なりすまし防止のため本コネクタからは指定できない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "note_code": {"type": "string", "description": "投稿先ノートのコード（list_notes で取得）"},
                    "title": {"type": "string", "description": "ページタイトル（最大100文字）"},
                    "body": {"type": "string", "description": "本文（Markdown形式）"},
                    "folder_id": {"type": "integer", "description": "ノート内の格納先フォルダID（省略時はノート直下に作成）"},
                    "memo": {"type": "string", "description": "変更履歴・通知に表示される一言メモ（最大255文字）"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "付与するタグ名のリスト"},
                },
                "required": ["note_code", "title"],
            },
        ),
        types.Tool(
            name="update_page",
            description=(
                "既存ページを部分更新する。title/body/folder_id/memo/tags/note_code のうち指定した項目のみが"
                "変更され、省略した項目は変更されない。note_code を指定すると、そのページを別のノートへ"
                "移動できる。tags は空配列を渡すと既存タグが全て解除される（tags 自体を省略した場合は変更"
                "しない）。title は最大100文字、memo は最大255文字までの制限がある。NotePM API自体には"
                "ページ削除エンドポイントが存在するが、誤削除防止のため本コネクタには削除ツールを実装していない"
                "（削除は NotePM の Web UI から行う）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page_code": {"type": "string", "description": "更新するページのコード"},
                    "note_code": {"type": "string", "description": "移動先ノートのコード（省略時は移動しない）"},
                    "title": {"type": "string", "description": "新しいタイトル（最大100文字、省略時は変更しない）"},
                    "body": {"type": "string", "description": "新しい本文（Markdown形式、省略時は変更しない）"},
                    "folder_id": {"type": "integer", "description": "移動先フォルダID（省略時は変更しない）"},
                    "memo": {"type": "string", "description": "新しいメモ（最大255文字、省略時は変更しない）"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "新しいタグ名のリスト（省略時は変更しない。既存タグを全解除したい場合は空配列を渡す）",
                    },
                },
                "required": ["page_code"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_notes":
                params: dict = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 20),
                    "include_archived": 1 if arguments.get("include_archived") else 0,
                }
                r = client.get("/notes", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "search_pages":
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 20),
                }
                if arguments.get("q"):
                    params["q"] = arguments["q"]
                if arguments.get("note_code"):
                    params["note_code"] = arguments["note_code"]
                if arguments.get("tag_name"):
                    params["tag_name"] = arguments["tag_name"]
                if arguments.get("only_title"):
                    params["only_title"] = 1
                if arguments.get("created"):
                    params["created"] = arguments["created"]
                if arguments.get("include_archived"):
                    params["include_archived"] = 1
                r = client.get("/pages", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_page":
                r = client.get(f"/pages/{arguments['page_code']}")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "create_page":
                payload: dict = {
                    "note_code": arguments["note_code"],
                    "title": arguments["title"],
                }
                if arguments.get("body"):
                    payload["body"] = arguments["body"]
                if arguments.get("folder_id") is not None:
                    payload["folder_id"] = arguments["folder_id"]
                if arguments.get("memo"):
                    payload["memo"] = arguments["memo"]
                if arguments.get("tags"):
                    payload["tags"] = arguments["tags"]
                r = client.post("/pages", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "update_page":
                payload = {}
                if arguments.get("note_code"):
                    payload["note_code"] = arguments["note_code"]
                if arguments.get("title"):
                    payload["title"] = arguments["title"]
                if arguments.get("body"):
                    payload["body"] = arguments["body"]
                if arguments.get("folder_id") is not None:
                    payload["folder_id"] = arguments["folder_id"]
                if arguments.get("memo"):
                    payload["memo"] = arguments["memo"]
                if arguments.get("tags") is not None:
                    payload["tags"] = arguments["tags"]
                r = client.patch(f"/pages/{arguments['page_code']}", json=payload)
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
