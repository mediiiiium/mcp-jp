import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("board-mcp")
BASE_URL = "https://api.the-board.jp/v1"


def _client() -> httpx.Client:
    api_key = os.environ.get("BOARD_API_KEY")
    api_token = os.environ.get("BOARD_API_TOKEN")
    if not api_key:
        raise ValueError("BOARD_API_KEY が設定されていません")
    if not api_token:
        raise ValueError("BOARD_API_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "x-api-key": api_key,
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_clients",
            description=(
                "顧客（取引先）の一覧を取得する。取引先ごとの案件・請求状況を確認する起点として使うほか、"
                "create_project に渡す client_id を調べる目的でもよく使う。name を指定すると顧客名の部分一致で"
                "絞り込める。ページネーションは page/per_page 方式（本ツールの既定は page=1, per_page=20。"
                "board API 側の上限は per_page=100）。並び順は API 側の既定に従う（本コネクタで変更するパラメータは"
                "提供していない）。読み取り専用。board API には取引先の新規作成・更新・削除エンドポイントも"
                "存在するが、本コネクタには実装されていない（必要な場合は board 管理画面から操作する）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり）", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（board API 上限100件）", "default": 20},
                    "name": {"type": "string", "description": "顧客名で絞り込む（部分一致）"},
                },
            },
        ),
        types.Tool(
            name="list_projects",
            description=(
                "プロジェクト（案件）の一覧を取得する。取引先横断でのプロジェクト状況の棚卸しや、"
                "特定顧客の案件一覧を確認する目的で使う。既定では新しい順（作成日時の降順）で返り、"
                "本コネクタには並び順を変更するパラメータはない。ページネーションは page/per_page 方式"
                "（本ツールの既定は page=1, per_page=20。board API 側の上限は per_page=100）。client_id で"
                "顧客を絞り込み、status で稼働状況（active=進行中 / complete=完了 / suspend=中断）を絞り込める。"
                "個々のプロジェクトに紐づく見積書・発注書・請求書などの書類詳細まで見たい場合は get_project を"
                "使う（response_group パラメータで書類データを含められる）。読み取り専用。プロジェクトの更新・"
                "削除エンドポイントも board API には存在するが、本コネクタには実装されていない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり）", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（board API 上限100件）", "default": 20},
                    "client_id": {"type": "integer", "description": "この顧客IDに紐づくプロジェクトのみに絞り込む"},
                    "status": {"type": "string", "description": "稼働状況で絞り込む: active（進行中）/ complete（完了）/ suspend（中断）"},
                },
            },
        ),
        types.Tool(
            name="get_project",
            description=(
                "指定した1件のプロジェクト（案件）の詳細情報を取得する。一覧の絞り込みで対象が定まった後、"
                "その1件の詳細（見積書・発注書・納品書・請求書・領収書などの紐づく書類）を確認したい場合に使う。"
                "response_group を省略すると基本情報のみが返る。invoice を指定すると請求書データ、estimate なら"
                "見積書データ、order なら発注書データ、delivery なら納品書データ、receipt なら領収書データ、"
                "project_cost なら原価情報、all なら全書類データをまとめて取得できる（未指定時は書類の詳細は"
                "含まれない点に注意）。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer", "description": "取得するプロジェクトのID（list_projects で確認）"},
                    "response_group": {
                        "type": "string",
                        "enum": ["small", "medium", "large", "estimate", "order", "delivery", "invoice", "receipt", "project_cost", "all"],
                        "description": (
                            "取得する関連書類の詳細度。省略時は small（基本情報のみ）。"
                            "invoice=請求書, estimate=見積書, order=発注書, delivery=納品書, receipt=領収書, "
                            "project_cost=原価, medium/large=段階的に多くの付随情報を含む, all=すべて含む"
                        ),
                    },
                },
                "required": ["project_id"],
            },
        ),
        types.Tool(
            name="list_invoices",
            description=(
                "請求データの一覧を取得する。特定顧客・特定プロジェクトの請求状況をまとめて確認したい場合に"
                "使う。ページネーションは page/per_page 方式（本ツールの既定は page=1, per_page=20。board API 側の"
                "上限は per_page=100）。client_id・project_id で絞り込み可能。ここで返る id は請求管理データの"
                "IDであり、請求書ドキュメントそのものの内容（明細・PDF等）まで詳しく見たい場合は get_project を"
                "project_id 指定・response_group=invoice で呼び出す方が確実（board API 側では請求データIDと"
                "請求書ドキュメントIDが別概念として扱われるため）。読み取り専用。請求書の新規作成・更新・削除を"
                "行うツールは本コネクタには実装されていない（請求書は board 上ではプロジェクト作成時に自動生成"
                "され、内容の更新・削除は管理画面またはプロジェクト配下のエンドポイントで行う）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり）", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（board API 上限100件）", "default": 20},
                    "client_id": {"type": "integer", "description": "この顧客IDに紐づく請求データのみに絞り込む"},
                    "project_id": {"type": "integer", "description": "このプロジェクトIDに紐づく請求データのみに絞り込む"},
                },
            },
        ),
        types.Tool(
            name="create_project",
            description=(
                "新しいプロジェクト（案件）を1件作成する。作成すると請求書などの関連書類は空の状態で"
                "自動的に生成される。呼び出すたびに新規レコードが作成され、重複防止（べき等性）の仕組みは"
                "board API 側にない。同じ内容で誤って複数回呼び出すと同名のプロジェクトが重複して作成される"
                "ため、実行前に list_projects で既存の同名プロジェクトがないか確認することを推奨する。"
                "name のみ必須で、client_id・start_date・end_date・budget は省略可能。作成後のプロジェクトの"
                "更新・削除エンドポイントは board API には存在するが、本コネクタには実装されていない"
                "（必要な場合は board 管理画面から操作する）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "プロジェクト名（必須）"},
                    "client_id": {"type": "integer", "description": "紐づける顧客ID（省略可）"},
                    "start_date": {"type": "string", "description": "開始日（YYYY-MM-DD、省略可）"},
                    "end_date": {"type": "string", "description": "終了日（YYYY-MM-DD、省略可）"},
                    "budget": {"type": "integer", "description": "予算（円、省略可）"},
                },
                "required": ["name"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_clients":
                params: dict = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 20),
                }
                if arguments.get("name"):
                    params["name"] = arguments["name"]
                r = client.get("/clients", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_projects":
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 20),
                }
                if arguments.get("client_id"):
                    params["client_id"] = arguments["client_id"]
                if arguments.get("status"):
                    params["status"] = arguments["status"]
                r = client.get("/projects", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_project":
                params = {}
                if arguments.get("response_group"):
                    params["response_group"] = arguments["response_group"]
                r = client.get(f"/projects/{arguments['project_id']}", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_invoices":
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 20),
                }
                if arguments.get("client_id"):
                    params["client_id"] = arguments["client_id"]
                if arguments.get("project_id"):
                    params["project_id"] = arguments["project_id"]
                r = client.get("/invoices", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "create_project":
                payload: dict = {"name": arguments["name"]}
                if arguments.get("client_id"):
                    payload["client_id"] = arguments["client_id"]
                if arguments.get("start_date"):
                    payload["start_date"] = arguments["start_date"]
                if arguments.get("end_date"):
                    payload["end_date"] = arguments["end_date"]
                if arguments.get("budget") is not None:
                    payload["budget"] = arguments["budget"]
                r = client.post("/projects", json=payload)
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
