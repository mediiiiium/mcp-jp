import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("jooto-mcp")
# 公式 API リファレンス（https://www.jooto.com/api/reference/request/）の Servers 定義に
# 従う。誤って Web アプリのオリジン（app.jooto.com）宛てにリクエストしないよう注意。
BASE_URL = "https://api.jooto.com"


def _client() -> httpx.Client:
    api_key = os.environ.get("JOOTO_API_KEY")
    if not api_key:
        raise ValueError("JOOTO_API_KEY が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "X-Jooto-Api-Key": api_key,
            "Content-Type": "application/json",
        },
        timeout=30,
    )


TASK_STATUS_ENUM = ["to_do", "done", "cancel", "pending", "in_progress"]


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_organization",
            description=(
                "この API キーが紐づく組織1件の情報（組織ID・組織名・業種・住所などの登録情報）を取得する。"
                "Jooto の API キーは組織ごとに発行され、1つのキーで複数組織にまたがってアクセスすることは"
                "できないため、これは『所属組織の一覧』ではなく常に1件のみを返す（Jooto API に組織一覧を"
                "返すエンドポイントは存在しない）。接続確認や組織設定の確認に使う。ページネーションなし・"
                "引数なし。読み取り専用。組織情報の更新エンドポイント（PATCH /v1/organization）も Jooto API"
                "には存在するが、本コネクタには実装していない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="list_boards",
            description=(
                "組織内のプロジェクト（ボード）一覧を取得する。特定プロジェクトの board_id を調べてから "
                "list_tasks・list_lists・create_task を呼び出す、という使い方の起点になる。archived を"
                "省略すると未アーカイブ・アーカイブ済み両方を返し、false なら未アーカイブのみ、true なら"
                "アーカイブ済みのみに絞り込める。並び順は order（asc/desc、省略時はAPI既定の desc）と "
                "order_by（id/order_id/title、省略時はAPI既定の order_id）で指定できる。ページネーションは "
                "page/per_page 方式（本ツールの既定は page=1, per_page=20。Jooto API 側の1ページあたり既定"
                "件数はドキュメントで確認できず）。読み取り専用。プロジェクトの更新・アーカイブ・復元・削除"
                "（削除はアーカイブ済みプロジェクトのみ対象）エンドポイントも Jooto API には存在するが、"
                "本コネクタには実装していない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "archived": {
                        "type": "boolean",
                        "description": "省略時は全件。false=未アーカイブのみ、true=アーカイブ済みのみ",
                    },
                    "order": {
                        "type": "string",
                        "enum": ["asc", "desc"],
                        "description": "並び順。省略時はAPI既定の desc",
                    },
                    "order_by": {
                        "type": "string",
                        "enum": ["id", "order_id", "title"],
                        "description": "並び替え基準列。省略時はAPI既定の order_id",
                    },
                    "page": {"type": "integer", "description": "ページ番号（1始まり）", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数", "default": 20},
                },
            },
        ),
        types.Tool(
            name="list_lists",
            description=(
                "指定したプロジェクト（ボード）内のリスト（カンバンの列。例: 未着手/進行中/完了）一覧を"
                "取得する。Jooto ではタスクは必ずいずれかのリストに所属し、create_task はリスト ID を"
                "必須で要求するため、タスク作成前に対象リストの list_id を確認する目的でよく使う。"
                "archived を省略すると未アーカイブ・アーカイブ済み両方を返す。並び順は order（asc/desc、"
                "省略時はAPI既定の desc）のみ指定可能。ページネーションは page/per_page 方式（本ツールの"
                "既定は page=1, per_page=20）。読み取り専用。リストの新規作成・更新・アーカイブ・復元・"
                "削除エンドポイントも Jooto API には存在するが、本コネクタには実装していない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "board_id": {"type": "integer", "description": "プロジェクト（ボード）のID（list_boards で確認）"},
                    "archived": {
                        "type": "boolean",
                        "description": "省略時は全件。false=未アーカイブのみ、true=アーカイブ済みのみ",
                    },
                    "order": {
                        "type": "string",
                        "enum": ["asc", "desc"],
                        "description": "並び順。省略時はAPI既定の desc",
                    },
                    "page": {"type": "integer", "description": "ページ番号（1始まり）", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数", "default": 20},
                },
                "required": ["board_id"],
            },
        ),
        types.Tool(
            name="list_tasks",
            description=(
                "指定したプロジェクト（ボード）内のタスク一覧を取得する。担当者（assignee_ids）・ラベル"
                "（category_ids）・ステータス（status）・締め切り期間（deadline_since/deadline_until）・"
                "フォロー中かどうか（followed）・アーカイブ状態（archived）で絞り込める（複数値指定時は"
                "OR条件）。フリーワード検索をしたい場合は、Jooto API には別途 /v1/boards/{id}/search"
                "（フリーワード検索用のタスク一覧取得）が存在するが本コネクタには未実装のため、名前の"
                "部分一致検索はできない点に注意。並び順は order（asc/desc、省略時はAPI既定の desc）のみ"
                "指定可能で、並び替えの基準列は選べない。ページネーションは page/per_page 方式（本ツール"
                "の既定は page=1, per_page=20）。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "board_id": {"type": "integer", "description": "プロジェクト（ボード）のID（list_boards で確認）"},
                    "page": {"type": "integer", "description": "ページ番号（1始まり）", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数", "default": 20},
                    "order": {
                        "type": "string",
                        "enum": ["asc", "desc"],
                        "description": "並び順。省略時はAPI既定の desc",
                    },
                    "category_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "ラベルIDの配列で絞り込む（複数指定でOR条件）",
                    },
                    "assignee_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "担当者のユーザーIDの配列で絞り込む（複数指定でOR条件）",
                    },
                    "deadline_since": {
                        "type": "string",
                        "description": "この日時（ISO 8601）以降が締め切りのタスクのみに絞り込む",
                    },
                    "deadline_until": {
                        "type": "string",
                        "description": "この日時（ISO 8601）以前が締め切りのタスクのみに絞り込む",
                    },
                    "followed": {"type": "boolean", "description": "フォロー中のタスクのみに絞り込む"},
                    "archived": {
                        "type": "boolean",
                        "description": "省略時は全件。false=未アーカイブのみ、true=アーカイブ済みのみ",
                    },
                    "status": {
                        "type": "array",
                        "items": {"type": "string", "enum": TASK_STATUS_ENUM},
                        "description": "ステータスの配列で絞り込む（複数指定でOR条件）。to_do=未着手, in_progress=進行中, pending=保留, done=完了, cancel=キャンセル",
                    },
                },
                "required": ["board_id"],
            },
        ),
        types.Tool(
            name="create_task",
            description=(
                "新しいタスクを1件作成する。name に加えて list_id が必須（Jooto ではタスクは必ずいずれかの"
                "リストに所属するため、所属リスト未指定では作成できない）。作成先候補のリスト ID は事前に"
                "list_lists で確認する。description・担当者（assigned_user_ids）・開始日時（start_date_time）"
                "・締め切り日時（deadline_date_time）・ラベル（category_ids）・予定（effort）・実績（actual）"
                "・ステータス（status、省略時は to_do）は省略可能。呼び出すたびに新規タスクが作成され、"
                "重複防止（べき等性）の仕組みは Jooto API 側にない。同じ内容で誤って複数回呼び出すと同名の"
                "タスクが重複して作成されるため、実行前に list_tasks で既存タスクの有無を確認することを"
                "推奨する。作成後のタスクの更新（PATCH）・アーカイブ・復元・削除（削除はアーカイブ済み"
                "タスクのみ対象）エンドポイントも Jooto API には存在するが、本コネクタには実装していない"
                "（必要な場合は Jooto の管理画面から操作する）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "board_id": {"type": "integer", "description": "プロジェクト（ボード）のID（list_boards で確認）"},
                    "list_id": {
                        "type": "integer",
                        "description": "作成先のリスト（カンバンの列）のID（list_lists で確認）。Jooto API 側で必須。",
                    },
                    "name": {"type": "string", "description": "タスク名（必須）"},
                    "description": {"type": "string", "description": "タスクの詳細説明（省略可）"},
                    "assigned_user_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "担当者として割り当てるユーザーIDの配列（省略可）",
                    },
                    "start_date_time": {
                        "type": "string",
                        "description": "開始日時（ISO 8601、省略可）",
                    },
                    "deadline_date_time": {
                        "type": "string",
                        "description": "締め切り日時（ISO 8601、省略可）",
                    },
                    "category_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "付与するラベルIDの配列（省略可）",
                    },
                    "effort": {"type": "string", "description": "タスクの予定（工数見積り等、省略可）"},
                    "actual": {"type": "string", "description": "タスクの実績（省略可）"},
                    "status": {
                        "type": "string",
                        "enum": TASK_STATUS_ENUM,
                        "description": "タスクのステータス（省略時は to_do）。to_do=未着手, in_progress=進行中, pending=保留, done=完了, cancel=キャンセル",
                    },
                },
                "required": ["board_id", "list_id", "name"],
            },
        ),
        types.Tool(
            name="get_task",
            description=(
                "指定した1件のタスクの詳細情報を取得する。一覧の絞り込みで対象が定まった後、その1件の"
                "詳細（担当者・ラベル・開始日時・締め切り日時・ステータス・作成者など）を確認したい場合に"
                "使う。ページネーションなし。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "board_id": {"type": "integer", "description": "プロジェクト（ボード）のID"},
                    "task_id": {"type": "integer", "description": "タスクID"},
                },
                "required": ["board_id", "task_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "get_organization":
                r = client.get("/v1/organization")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_boards":
                params: dict = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 20),
                }
                if arguments.get("archived") is not None:
                    params["archived"] = arguments["archived"]
                if arguments.get("order"):
                    params["order"] = arguments["order"]
                if arguments.get("order_by"):
                    params["order_by"] = arguments["order_by"]
                r = client.get("/v1/boards", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_lists":
                board_id = arguments["board_id"]
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 20),
                }
                if arguments.get("archived") is not None:
                    params["archived"] = arguments["archived"]
                if arguments.get("order"):
                    params["order"] = arguments["order"]
                r = client.get(f"/v1/boards/{board_id}/lists", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_tasks":
                board_id = arguments["board_id"]
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 20),
                }
                if arguments.get("order"):
                    params["order"] = arguments["order"]
                if arguments.get("category_ids"):
                    params["category_ids[]"] = arguments["category_ids"]
                if arguments.get("assignee_ids"):
                    params["assignee_ids[]"] = arguments["assignee_ids"]
                if arguments.get("deadline_since"):
                    params["deadline_since"] = arguments["deadline_since"]
                if arguments.get("deadline_until"):
                    params["deadline_until"] = arguments["deadline_until"]
                if arguments.get("followed") is not None:
                    params["followed"] = arguments["followed"]
                if arguments.get("archived") is not None:
                    params["archived"] = arguments["archived"]
                if arguments.get("status"):
                    params["status[]"] = arguments["status"]
                r = client.get(f"/v1/boards/{board_id}/tasks", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "create_task":
                board_id = arguments["board_id"]
                payload: dict = {
                    "name": arguments["name"],
                    "list_id": arguments["list_id"],
                }
                if arguments.get("description"):
                    payload["description"] = arguments["description"]
                if arguments.get("assigned_user_ids"):
                    payload["assigned_user_ids"] = arguments["assigned_user_ids"]
                if arguments.get("start_date_time"):
                    payload["start_date_time"] = arguments["start_date_time"]
                if arguments.get("deadline_date_time"):
                    payload["deadline_date_time"] = arguments["deadline_date_time"]
                if arguments.get("category_ids"):
                    payload["category_ids"] = arguments["category_ids"]
                if arguments.get("effort"):
                    payload["effort"] = arguments["effort"]
                if arguments.get("actual"):
                    payload["actual"] = arguments["actual"]
                if arguments.get("status"):
                    payload["status"] = arguments["status"]
                r = client.post(f"/v1/boards/{board_id}/tasks", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_task":
                board_id = arguments["board_id"]
                task_id = arguments["task_id"]
                r = client.get(f"/v1/boards/{board_id}/tasks/{task_id}")
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
