import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("harvest-mcp")
BASE_URL = "https://api.harvestapp.com/v2"


def _client() -> httpx.Client:
    access_token = os.environ.get("HARVEST_ACCESS_TOKEN")
    account_id = os.environ.get("HARVEST_ACCOUNT_ID")
    if not access_token:
        raise ValueError("HARVEST_ACCESS_TOKEN が設定されていません")
    if not account_id:
        raise ValueError("HARVEST_ACCOUNT_ID が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Harvest-Account-Id": account_id,
            "Content-Type": "application/json",
            "User-Agent": "harvest-mcp/0.1.0",
        },
        timeout=30,
    )


_PAGE_DESC = "取得するページ番号（1始まり）。続きのページを取りたい場合に指定する（既定1）。"
_PER_PAGE_DESC = "1ページあたりの件数。1〜2000の範囲で指定可能（省略時はHarvest側の既定・上限である2000件が返る）。"
_UPDATED_SINCE_DESC = "この日時（ISO 8601形式、例: 2026-06-01T00:00:00Z）以降に更新されたレコードのみに絞り込む。前回同期時刻を渡すことで差分取得に使える。"


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_projects",
            description=(
                "プロジェクト一覧を取得する。time_entry作成時に必要なproject_id/task_idの組み合わせを事前に確認したい"
                "場合や、稼働中プロジェクトの棚卸しに使う。既定では作成日時の新しい順（最近作成されたものが先頭）で返る。"
                "ページネーションはページ番号方式（page / per_page）。is_active で有効/無効を絞り込み、client_id で"
                "特定クライアントのプロジェクトのみに絞り込み、updated_since で差分取得もできる。読み取り専用で、"
                "プロジェクトの作成・更新・削除APIはHarvest側に存在するが本コネクタでは提供していない"
                "（誤操作で稼働中プロジェクトや紐づく時間データに影響が出るのを避けるため）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "is_active": {"type": "boolean", "description": "true=アクティブなプロジェクトのみ、false=非アクティブのみ（省略時は両方）"},
                    "client_id": {"type": "integer", "description": "このクライアントIDに紐づくプロジェクトのみに絞り込む"},
                    "updated_since": _updated_since_schema(),
                    "page": {"type": "integer", "description": _PAGE_DESC},
                    "per_page": {"type": "integer", "description": _PER_PAGE_DESC},
                },
            },
        ),
        types.Tool(
            name="list_time_entries",
            description=(
                "時間計測エントリー一覧を取得する。特定期間・特定プロジェクト/タスク/担当者の稼働実績を横断的に"
                "確認したい場合や、請求前の集計に使う。既定ではspent_date（作業日）でソートされて返るが、"
                "APIドキュメント上は昇順/降順が明記されていないため並び順に依存する処理は避けること。"
                "ページネーションはページ番号方式（page / per_page、既定・上限とも2000件）。project_id・client_id・"
                "task_id・user_idで絞り込み、is_billed（請求済みか）・is_running（実行中タイマーか）・"
                "approval_status（unsubmitted/submitted/approved）でステータス絞り込み、from_date/to_date で"
                "spent_dateの範囲指定、updated_since で差分取得ができる。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer", "description": "このプロジェクトIDのエントリーのみに絞り込む"},
                    "client_id": {"type": "integer", "description": "このクライアントIDに紐づくプロジェクトのエントリーのみに絞り込む"},
                    "task_id": {"type": "integer", "description": "このタスクIDのエントリーのみに絞り込む"},
                    "user_id": {"type": "integer", "description": "このユーザーIDが記録したエントリーのみに絞り込む"},
                    "is_billed": {"type": "boolean", "description": "true=請求済みのみ、false=未請求のみ（省略時は両方）"},
                    "is_running": {"type": "boolean", "description": "true=実行中タイマーのみ、false=停止済みのみ（省略時は両方）"},
                    "approval_status": {
                        "type": "string",
                        "enum": ["unsubmitted", "submitted", "approved"],
                        "description": "承認ステータスで絞り込む（unsubmitted=未提出 / submitted=提出済み / approved=承認済み）",
                    },
                    "from_date": {"type": "string", "description": "作業日(spent_date)の範囲開始（YYYY-MM-DD形式、この日を含む）"},
                    "to_date": {"type": "string", "description": "作業日(spent_date)の範囲終了（YYYY-MM-DD形式、この日を含む）"},
                    "updated_since": _updated_since_schema(),
                    "page": {"type": "integer", "description": _PAGE_DESC},
                    "per_page": {"type": "integer", "description": _PER_PAGE_DESC},
                },
            },
        ),
        types.Tool(
            name="create_time_entry",
            description=(
                "新しい時間計測エントリーを1件作成する（duration方式：作業時間を hours で直接指定する方法のみ対応。"
                "開始/終了時刻を指定するタイムスタンプ方式はHarvest API側には存在するが本コネクタは未実装）。"
                "呼び出すたびに新規エントリーが作成されるため冪等ではない（同じ内容で2回呼ぶと重複して2件作成される）。"
                "hours を省略した場合、アカウントのタイムトラッキング方式によっては実行中タイマーとして作成される"
                "ことがある。project_id・task_id は事前に list_projects 等で有効な組み合わせを確認しておくこと。"
                "作成後の内容変更は update_time_entry、削除は delete_time_entry を使う。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer", "description": "紐づけるプロジェクトID"},
                    "task_id": {"type": "integer", "description": "紐づけるタスクID（プロジェクトに割り当て済みのタスクである必要がある）"},
                    "spent_date": {"type": "string", "description": "作業日（YYYY-MM-DD形式）"},
                    "hours": {"type": "number", "description": "作業時間（例: 1.5）。省略するとアカウント設定によっては実行中タイマーとして作成される"},
                    "notes": {"type": "string", "description": "メモ・作業内容の説明"},
                },
                "required": ["project_id", "task_id", "spent_date"],
            },
        ),
        types.Tool(
            name="update_time_entry",
            description=(
                "既存の時間計測エントリー1件を部分更新する（PATCH）。project_id・task_id・spent_date・hours・notes"
                "のうち指定した項目のみが変更され、省略した項目は変更されない。同一内容で複数回呼び出しても結果は"
                "変わらないため実質的に冪等。請求確定済み・承認済みなどロックされたエントリーは更新できずAPIエラー"
                "になる場合がある。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "time_entry_id": {"type": "integer", "description": "更新する時間計測エントリーのID"},
                    "project_id": {"type": "integer", "description": "変更後のプロジェクトID（省略時は変更しない）"},
                    "task_id": {"type": "integer", "description": "変更後のタスクID（省略時は変更しない）"},
                    "spent_date": {"type": "string", "description": "変更後の作業日（YYYY-MM-DD形式、省略時は変更しない）"},
                    "hours": {"type": "number", "description": "変更後の作業時間（省略時は変更しない）"},
                    "notes": {"type": "string", "description": "変更後のメモ（省略時は変更しない）"},
                },
                "required": ["time_entry_id"],
            },
        ),
        types.Tool(
            name="delete_time_entry",
            description=(
                "時間計測エントリー1件を削除する。close済み（請求確定済みなど）でなく、関連するプロジェクト・タスク"
                "がアーカイブされていない場合のみ削除可能（Admin権限があればclose済みエントリーも削除できる、"
                "詳細はHarvest API仕様に依存）。削除は取り消せない。一度削除したIDに対して再度削除を呼ぶと"
                "404エラーになるため、lstepのタグ解除操作などとは異なり冪等ではない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "time_entry_id": {"type": "integer", "description": "削除する時間計測エントリーのID"},
                },
                "required": ["time_entry_id"],
            },
        ),
        types.Tool(
            name="list_clients",
            description=(
                "クライアント（請求先企業）一覧を取得する。プロジェクトや請求書のclient_idを確認したい場合に使う。"
                "既定では作成日時の新しい順で返る。ページネーションはページ番号方式（page / per_page）。is_active で"
                "有効/無効を絞り込み、updated_since で差分取得もできる。読み取り専用。クライアントの作成・更新・"
                "削除APIはHarvest側に存在する（削除は紐づくプロジェクト・請求書・見積が0件の場合のみ可能）が、"
                "請求データに影響する操作のため本コネクタでは参照のみ提供している。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "is_active": {"type": "boolean", "description": "true=アクティブなクライアントのみ、false=非アクティブのみ（省略時は両方）"},
                    "updated_since": _updated_since_schema(),
                    "page": {"type": "integer", "description": _PAGE_DESC},
                    "per_page": {"type": "integer", "description": _PER_PAGE_DESC},
                },
            },
        ),
        types.Tool(
            name="list_invoices",
            description=(
                "請求書一覧を取得する。入金状況の確認や未請求・未払いの洗い出しに使う。既定では発行日(issue_date)の"
                "新しい順で返る。ページネーションはページ番号方式（page / per_page）。client_id・project_id・"
                "state（draft/open/paid/closed）・from_date/to_date（issue_date範囲）・updated_since（差分取得用）"
                "で絞り込み可能。読み取り専用。請求書の作成・更新・削除APIはHarvest側に存在するが、請求データの"
                "安全性を優先し本コネクタでは参照のみ提供している。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "client_id": {"type": "integer", "description": "このクライアントIDの請求書のみに絞り込む"},
                    "project_id": {"type": "integer", "description": "このプロジェクトIDに紐づく請求書のみに絞り込む"},
                    "state": {
                        "type": "string",
                        "enum": ["draft", "open", "paid", "closed"],
                        "description": "請求書ステータスで絞り込む（draft=下書き / open=送付済み未入金 / paid=入金済み / closed=クローズ済み）",
                    },
                    "from_date": {"type": "string", "description": "発行日(issue_date)の範囲開始（YYYY-MM-DD形式、この日を含む）"},
                    "to_date": {"type": "string", "description": "発行日(issue_date)の範囲終了（YYYY-MM-DD形式、この日を含む）"},
                    "updated_since": _updated_since_schema(),
                    "page": {"type": "integer", "description": _PAGE_DESC},
                    "per_page": {"type": "integer", "description": _PER_PAGE_DESC},
                },
            },
        ),
    ]


def _updated_since_schema() -> dict:
    return {"type": "string", "description": _UPDATED_SINCE_DESC}


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_projects":
                params = _page_params(arguments)
                if arguments.get("is_active") is not None:
                    params["is_active"] = arguments["is_active"]
                if arguments.get("client_id"):
                    params["client_id"] = arguments["client_id"]
                if arguments.get("updated_since"):
                    params["updated_since"] = arguments["updated_since"]
                r = client.get("/projects", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_time_entries":
                params = _page_params(arguments)
                if arguments.get("project_id"):
                    params["project_id"] = arguments["project_id"]
                if arguments.get("client_id"):
                    params["client_id"] = arguments["client_id"]
                if arguments.get("task_id"):
                    params["task_id"] = arguments["task_id"]
                if arguments.get("user_id"):
                    params["user_id"] = arguments["user_id"]
                if arguments.get("is_billed") is not None:
                    params["is_billed"] = arguments["is_billed"]
                if arguments.get("is_running") is not None:
                    params["is_running"] = arguments["is_running"]
                if arguments.get("approval_status"):
                    params["approval_status"] = arguments["approval_status"]
                if arguments.get("from_date"):
                    params["from"] = arguments["from_date"]
                if arguments.get("to_date"):
                    params["to"] = arguments["to_date"]
                if arguments.get("updated_since"):
                    params["updated_since"] = arguments["updated_since"]
                r = client.get("/time_entries", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "create_time_entry":
                payload = {
                    "project_id": arguments["project_id"],
                    "task_id": arguments["task_id"],
                    "spent_date": arguments["spent_date"],
                }
                if arguments.get("hours"):
                    payload["hours"] = arguments["hours"]
                if arguments.get("notes"):
                    payload["notes"] = arguments["notes"]
                r = client.post("/time_entries", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "update_time_entry":
                time_entry_id = arguments["time_entry_id"]
                payload = {}
                if arguments.get("project_id"):
                    payload["project_id"] = arguments["project_id"]
                if arguments.get("task_id"):
                    payload["task_id"] = arguments["task_id"]
                if arguments.get("spent_date"):
                    payload["spent_date"] = arguments["spent_date"]
                if arguments.get("hours") is not None:
                    payload["hours"] = arguments["hours"]
                if arguments.get("notes") is not None:
                    payload["notes"] = arguments["notes"]
                r = client.patch(f"/time_entries/{time_entry_id}", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "delete_time_entry":
                time_entry_id = arguments["time_entry_id"]
                r = client.delete(f"/time_entries/{time_entry_id}")
                r.raise_for_status()
                return format_response({"deleted": True, "time_entry_id": time_entry_id})

            elif name == "list_clients":
                params = _page_params(arguments)
                if arguments.get("is_active") is not None:
                    params["is_active"] = arguments["is_active"]
                if arguments.get("updated_since"):
                    params["updated_since"] = arguments["updated_since"]
                r = client.get("/clients", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_invoices":
                params = _page_params(arguments)
                if arguments.get("client_id"):
                    params["client_id"] = arguments["client_id"]
                if arguments.get("project_id"):
                    params["project_id"] = arguments["project_id"]
                if arguments.get("state"):
                    params["state"] = arguments["state"]
                if arguments.get("from_date"):
                    params["from"] = arguments["from_date"]
                if arguments.get("to_date"):
                    params["to"] = arguments["to_date"]
                if arguments.get("updated_since"):
                    params["updated_since"] = arguments["updated_since"]
                r = client.get("/invoices", params=params)
                r.raise_for_status()
                return format_response(r.json())

            else:
                raise ValueError(f"未知のツール: {name}")
    except Exception as exc:  # noqa: BLE001
        return error_response(exc)


def _page_params(arguments: dict) -> dict:
    params = {}
    if arguments.get("page"):
        params["page"] = arguments["page"]
    if arguments.get("per_page"):
        params["per_page"] = arguments["per_page"]
    return params


def main():
    import asyncio

    async def _run():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

    asyncio.run(_run())


if __name__ == "__main__":
    main()
