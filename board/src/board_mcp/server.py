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


def _csv(values) -> str:
    return ",".join(str(v) for v in values)


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
        types.Tool(
            name="get_client",
            description=(
                "指定した1件の顧客（取引先）の詳細情報を取得する。list_clients の一覧レスポンスは基本情報"
                "（small相当）のみだが、本ツールは response_group=large を指定することで住所・電話番号・"
                "支払条件・適格請求書発行事業者番号などすべての項目を取得できる。client_id は list_clients の"
                "レスポンスの id 値を指定する。読み取り専用。顧客の更新・削除エンドポイントも board API には"
                "存在するが、本コネクタには実装されていない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "client_id": {"type": "integer", "description": "取得する顧客のID（list_clients で確認）"},
                },
                "required": ["client_id"],
            },
        ),
        types.Tool(
            name="list_client_branches",
            description=(
                "顧客（取引先）の支社・支店の一覧を取得する。本社とは別の請求先・納品先住所を管理している"
                "取引先の支社情報を確認したい場合に使う。client_id で特定顧客に紐づく支社のみに絞り込める。"
                "ページネーションは page/per_page 方式（既定 page=1, per_page=20。board API 側の上限は"
                "per_page=100）。読み取り専用。顧客支社の作成・更新・削除エンドポイントも board API には"
                "存在するが、本コネクタには実装されていない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり）", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（board API 上限100件）", "default": 20},
                    "client_id": {"type": "integer", "description": "この顧客IDに紐づく支社のみに絞り込む"},
                    "include_archive": {"type": "boolean", "description": "アーカイブ済みの支社も含めて返す（既定false）"},
                },
            },
        ),
        types.Tool(
            name="list_contacts",
            description=(
                "顧客（取引先）の担当者一覧を取得する。取引先の窓口担当者の氏名・部署・メールアドレスを"
                "確認したい場合に使う。client_id で特定顧客に紐づく担当者のみに絞り込める。ページネーションは"
                "page/per_page 方式（既定 page=1, per_page=20。board API 側の上限は per_page=100）。"
                "読み取り専用。顧客担当者の作成・更新・削除エンドポイントも board API には存在するが、"
                "本コネクタには実装されていない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり）", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（board API 上限100件）", "default": 20},
                    "client_id": {"type": "integer", "description": "この顧客IDに紐づく担当者のみに絞り込む"},
                    "include_archive": {"type": "boolean", "description": "アーカイブ済みの担当者も含めて返す（既定false）"},
                },
            },
        ),
        types.Tool(
            name="list_project_costs",
            description=(
                "案件原価データの一覧を取得する。get_project を response_group=project_cost で呼ぶと1案件分の"
                "原価しか取れないが、本ツールは project_id 未指定で全案件横断の原価一覧を取得でき、請求日・"
                "支払日の範囲で絞り込める点が異なる。案件横断でのコスト状況の棚卸しに使う。ページネーションは"
                "page/per_page 方式（既定 page=1, per_page=20。board API 側の上限は per_page=100）。"
                "読み取り専用。案件原価の作成・更新・削除エンドポイントも board API には存在するが、"
                "本コネクタには実装されていない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり）", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（board API 上限100件）", "default": 20},
                    "project_id": {"type": "integer", "description": "このプロジェクトIDに紐づく原価のみに絞り込む"},
                    "invoice_date_from": {"type": "string", "description": "請求日の範囲開始（YYYY-MM-DD）"},
                    "invoice_date_to": {"type": "string", "description": "請求日の範囲終了（YYYY-MM-DD）"},
                    "payment_date_from": {"type": "string", "description": "支払日の範囲開始（YYYY-MM-DD）"},
                    "payment_date_to": {"type": "string", "description": "支払日の範囲終了（YYYY-MM-DD）"},
                },
            },
        ),
        types.Tool(
            name="list_users",
            description=(
                "board 利用ユーザー（社内アカウント）の一覧を取得する。プロジェクトの担当者を確認・特定する"
                "用途に使う。email で完全一致検索できる。ページネーションは page/per_page 方式（既定 page=1,"
                " per_page=20。board API 側の上限は per_page=100）。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり）", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（board API 上限100件）", "default": 20},
                    "email": {"type": "string", "description": "メールアドレスの完全一致で絞り込む"},
                },
            },
        ),
        types.Tool(
            name="list_analyses",
            description=(
                "計上データ（経営分析用の集計データ）の一覧を取得する。案件・案件原価・発注のいずれかの"
                "計上データを、計上年月・受注ステータス・請求ステータスなどで横断的に絞り込んで取得できる。"
                "月次の売上・原価・利益の棚卸しなど経営分析用途に使う。analysis_data_kbn で計上データ区分"
                "（1=案件, 2=案件原価, 3=発注）を指定しないと全種別が混在して返る点に注意。ページネーションは"
                "page/per_page 方式（既定 page=1, per_page=20。board API 側の上限は per_page=100）。"
                "読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり）", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（board API 上限100件）", "default": 20},
                    "report_ym_from": {"type": "string", "description": "計上年月の範囲開始（YYYY-MM）"},
                    "report_ym_to": {"type": "string", "description": "計上年月の範囲終了（YYYY-MM）"},
                    "analysis_data_kbn": {
                        "type": "array",
                        "items": {"type": "integer", "enum": [1, 2, 3]},
                        "description": "計上データ区分で絞り込む（1=案件 / 2=案件原価 / 3=発注）。複数指定可。省略時は全種別",
                    },
                    "order_status": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": (
                            "受注ステータスで絞り込む（1=見積中(高) / 2=見積中(中) / 3=見積中(低) / "
                            "8=見積中(除) / 4=受注確定 / 5=受注済 / 9=失注）。複数指定可"
                        ),
                    },
                    "invoice_status": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": (
                            "請求ステータスで絞り込む（1=未請求 / 4=請求OK / 2=請求済 / 5=一部入金済 / "
                            "3=入金済 / 9=回収不能）。複数指定可"
                        ),
                    },
                },
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

            elif name == "get_client":
                r = client.get(f"/clients/{arguments['client_id']}", params={"response_group": "large"})
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_client_branches":
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 20),
                }
                if arguments.get("client_id"):
                    params["client_id_eq"] = arguments["client_id"]
                if arguments.get("include_archive") is not None:
                    params["include_archive_flg"] = 1 if arguments["include_archive"] else 0
                r = client.get("/client_branches", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_contacts":
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 20),
                }
                if arguments.get("client_id"):
                    params["client_id_eq"] = arguments["client_id"]
                if arguments.get("include_archive") is not None:
                    params["include_archive_flg"] = 1 if arguments["include_archive"] else 0
                r = client.get("/contacts", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_project_costs":
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 20),
                }
                if arguments.get("project_id"):
                    params["project_id_eq"] = arguments["project_id"]
                if arguments.get("invoice_date_from"):
                    params["invoice_date_gteq"] = arguments["invoice_date_from"]
                if arguments.get("invoice_date_to"):
                    params["invoice_date_lteq"] = arguments["invoice_date_to"]
                if arguments.get("payment_date_from"):
                    params["payment_date_gteq"] = arguments["payment_date_from"]
                if arguments.get("payment_date_to"):
                    params["payment_date_lteq"] = arguments["payment_date_to"]
                r = client.get("/project_costs", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_users":
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 20),
                }
                if arguments.get("email"):
                    params["email_eq"] = arguments["email"]
                r = client.get("/users", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_analyses":
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 20),
                }
                if arguments.get("report_ym_from"):
                    params["report_ym_gteq"] = arguments["report_ym_from"]
                if arguments.get("report_ym_to"):
                    params["report_ym_lteq"] = arguments["report_ym_to"]
                if arguments.get("analysis_data_kbn"):
                    params["analysis_data_kbn_in[]"] = _csv(arguments["analysis_data_kbn"])
                if arguments.get("order_status"):
                    params["order_status_in[]"] = _csv(arguments["order_status"])
                if arguments.get("invoice_status"):
                    params["invoice_status_in[]"] = _csv(arguments["invoice_status"])
                r = client.get("/analyses", params=params)
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
