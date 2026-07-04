import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("talentio-mcp")
BASE_URL = "https://talentio.com/api/v1"


def _client() -> httpx.Client:
    token = os.environ.get("TALENTIO_ACCESS_TOKEN")
    if not token:
        raise ValueError("TALENTIO_ACCESS_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "Authorization": f"Bearer {token}",
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
            name="list_candidates",
            description=(
                "候補者（＝応募者）の一覧を取得する。特定求人への応募状況の確認、選考ステータス別の絞り込み、"
                "採用状況の棚卸しに使う。Talentio API には「応募(Application)」という独立したリソースは存在せず、"
                "候補者が応募先の求人(requisition)を保持する形でデータが管理されているため、特定求人の応募者を"
                "見たい場合は requisition_ids で絞り込む（本コネクタに list_applications 相当のツールはない）。"
                "ページネーションは page 番号方式（1始まり）で1ページ100件固定（limit/offset は指定不可）。"
                "レスポンス本文は候補者オブジェクトの配列のみで、総件数は本来 API レスポンスヘッダー X-Total に"
                "含まれるが本コネクタは本文のみを返すため件数は分からない。返ってきた件数が100件なら次ページが"
                "存在する可能性が高いので page を+1して再取得する。既定の並び順（sort 省略時）は registeredAt"
                "（登録日時）昇順。読み取り専用で書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり、1ページ100件固定）", "default": 1},
                    "status": {
                        "type": "string",
                        "enum": ["ongoing", "reject", "fail", "pass", "poolActive", "poolInactive"],
                        "description": (
                            "候補者ステータスで絞り込む（ongoing=選考中 / reject=辞退 / fail=お見送り / "
                            "pass=採用 / poolActive=コンタクト中 / poolInactive=非コンタクト中）。省略時は全件"
                        ),
                    },
                    "requisition_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "求人ID（list_jobs で取得）のリストで絞り込む。指定した求人への応募者のみ返す",
                    },
                    "job_title_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "職種IDのリストで絞り込む",
                    },
                    "stage_statuses": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["on_evaluating", "evaluated_all", "pass", "failed"],
                        },
                        "description": (
                            "選考ステージの状況で絞り込む（on_evaluating=評価待ち / evaluated_all=判定待ち / "
                            "pass=通過 / failed=お見送り）。複数指定可"
                        ),
                    },
                    "applied_at_from": {"type": "string", "description": "応募日時の範囲開始（yyyy/MM/dd）"},
                    "applied_at_to": {"type": "string", "description": "応募日時の範囲終了（yyyy/MM/dd）"},
                    "joined_at_from": {"type": "string", "description": "入社日の範囲開始（yyyy/MM/dd）"},
                    "joined_at_to": {"type": "string", "description": "入社日の範囲終了（yyyy/MM/dd）"},
                    "updated_at_from": {
                        "type": "string",
                        "description": "候補者の更新日時の範囲開始（yyyy-MM-ddThh:mm:ss）",
                    },
                    "updated_at_to": {
                        "type": "string",
                        "description": "候補者の更新日時の範囲終了（yyyy-MM-ddThh:mm:ss）",
                    },
                    "include_inactive_responsible_employees": {
                        "type": "boolean",
                        "description": "無効化された担当者が設定されている候補者も含めて返す（既定 false）",
                        "default": False,
                    },
                    "sort": {
                        "type": "string",
                        "enum": ["registeredAt", "-registeredAt", "appliedAt", "-appliedAt", "updatedAt", "-updatedAt"],
                        "description": (
                            "並び替え基準（先頭に - を付けると降順）。既定は registeredAt（登録日時の昇順）"
                        ),
                        "default": "registeredAt",
                    },
                },
            },
        ),
        types.Tool(
            name="get_candidate",
            description=(
                "候補者1名の詳細情報を取得する。list_candidates の一覧レスポンスには含まれない選考ステージごとの"
                "評価（evaluations、評価フォームの回答項目を含む）を確認したい場合に使う。candidate_id は "
                "list_candidates のレスポンスの id 値を指定する。読み取り専用で書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "candidate_id": {"type": "string", "description": "候補者ID（list_candidates で取得）"},
                    "include_inactive_responsible_employees": {
                        "type": "boolean",
                        "description": "無効化された担当者が設定されている場合も含めて返す（既定 false）",
                        "default": False,
                    },
                },
                "required": ["candidate_id"],
            },
        ),
        types.Tool(
            name="list_jobs",
            description=(
                "求人（Talentio API 上は requisition と呼ばれる）の一覧を取得する。募集中/募集終了の求人棚卸しや、"
                "list_candidates を requisition_ids で絞り込む前に対象求人IDを調べる用途に使う。ページネーションは"
                "page 番号方式（1始まり）で1ページ100件固定。レスポンス本文は求人オブジェクトの配列のみで、"
                "総件数は本来ヘッダー X-Total に含まれるが本コネクタは本文のみを返す。既定の並び順（sort 省略時）"
                "は createdAt（登録日時）昇順。status で絞り込める値は active（募集中）/inactive（募集終了）の"
                "2種類のみ。求人の新規作成 API（POST /requisitions）は存在するが、更新・削除に対応するAPIは"
                "Talentio に存在しないため、本コネクタにも作成・更新・削除ツールはない（Talentio 管理画面から"
                "操作する）。読み取り専用で書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり、1ページ100件固定）", "default": 1},
                    "status": {
                        "type": "string",
                        "enum": ["active", "inactive"],
                        "description": "募集状況で絞り込む（active=募集中 / inactive=募集終了）。省略時は全件",
                    },
                    "updated_at_from": {
                        "type": "string",
                        "description": "求人の更新日時の範囲開始（yyyy-MM-ddThh:mm:ss）",
                    },
                    "updated_at_to": {
                        "type": "string",
                        "description": "求人の更新日時の範囲終了（yyyy-MM-ddThh:mm:ss）",
                    },
                    "sort": {
                        "type": "string",
                        "enum": ["createdAt", "-createdAt", "updatedAt", "-updatedAt"],
                        "description": (
                            "並び替え基準（先頭に - を付けると降順）。既定は createdAt（登録日時の昇順）"
                        ),
                        "default": "createdAt",
                    },
                },
            },
        ),
        types.Tool(
            name="get_job",
            description=(
                "求人1件の詳細情報を取得する。list_jobs の一覧レスポンスには含まれない募集要項の詳細"
                "（recruiters, recruiterGroups, jobDescriptionDetails, companyDetails など）を確認したい場合に"
                "使う。job_id は list_jobs のレスポンスの id 値を指定する。求人の更新・削除に対応するAPIは"
                "Talentio に存在しないため、本コネクタにも該当ツールはない。読み取り専用で書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {"type": "string", "description": "求人ID（list_jobs で取得）"},
                },
                "required": ["job_id"],
            },
        ),
        types.Tool(
            name="list_job_titles",
            description=(
                "職種（job title）の一覧を取得する。求人の分類や、list_candidates の job_title_ids で"
                "絞り込む前に対象の職種IDを調べる用途に使う。各職種には紐づく求人一覧（requisitions）が"
                "含まれる。ページネーションは page 番号方式（1始まり）で1ページ100件固定。総件数は"
                "レスポンスヘッダー X-Total に含まれるが本コネクタは本文のみを返す。読み取り専用で"
                "書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり、1ページ100件固定）", "default": 1},
                    "status": {
                        "type": "string",
                        "enum": ["active", "archived"],
                        "description": "職種の状態で絞り込む（active=アクティブ / archived=アーカイブ済み）。省略時は全件",
                    },
                    "sort": {
                        "type": "string",
                        "enum": ["createdAt", "-createdAt", "updatedAt", "-updatedAt"],
                        "description": "並び替え基準（先頭に - を付けると降順）",
                    },
                },
            },
        ),
        types.Tool(
            name="list_candidate_channels",
            description=(
                "候補者の応募経路（チャネル。転職サイト・エージェント・社員紹介・自由入力など）の一覧を"
                "取得する。応募経路ごとの棚卸しや分析の前提となるマスタデータの確認に使う。ページネーションは"
                "page 番号方式（1始まり）で1ページ100件固定。読み取り専用で書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり、1ページ100件固定）", "default": 1},
                    "sort": {
                        "type": "string",
                        "enum": ["createdAt", "-createdAt", "updatedAt", "-updatedAt"],
                        "description": "並び替え基準（先頭に - を付けると降順）",
                    },
                },
            },
        ),
        types.Tool(
            name="list_form_templates",
            description=(
                "評価フォームテンプレート（選考時に使う評価項目のひな形）の一覧を取得する。id と name のみの"
                "シンプルな一覧で、get_candidate の evaluations に登場するフォームがどのテンプレートに"
                "基づくかを確認する用途に使う。ページネーションは page 番号方式（1始まり）で1ページ100件固定。"
                "読み取り専用で書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり、1ページ100件固定）", "default": 1},
                },
            },
        ),
        types.Tool(
            name="list_employees",
            description=(
                "Talentio 利用メンバー（社員アカウント）の一覧を取得する。担当求人（responsibleRequisitions）や"
                "所属グループ（groups）、権限（role: admin/manager/member）を確認する用途に使う。ページネーションは"
                "page 番号方式（1始まり）で1ページ100件固定。読み取り専用で書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり、1ページ100件固定）", "default": 1},
                    "status": {
                        "type": "string",
                        "enum": ["active", "inactive"],
                        "description": "メンバーの状態で絞り込む（active=有効 / inactive=無効）。省略時は全件",
                    },
                    "role": {
                        "type": "string",
                        "enum": ["admin", "manager", "member"],
                        "description": "メンバーの役割で絞り込む。省略時は全件",
                    },
                    "sort": {
                        "type": "string",
                        "enum": ["createdAt", "-createdAt", "updatedAt", "-updatedAt"],
                        "description": "並び替え基準（先頭に - を付けると降順）",
                    },
                },
            },
        ),
        types.Tool(
            name="list_employee_groups",
            description=(
                "メンバーの所属グループ（組織構成）の一覧を取得する。各グループに所属するメンバー一覧"
                "（employees）を含む。ページネーションは page 番号方式（1始まり）で1ページ100件固定。"
                "読み取り専用で書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり、1ページ100件固定）", "default": 1},
                    "sort": {
                        "type": "string",
                        "enum": ["createdAt", "-createdAt", "updatedAt", "-updatedAt"],
                        "description": "並び替え基準（先頭に - を付けると降順）",
                    },
                },
            },
        ),
        types.Tool(
            name="list_workspaces",
            description=(
                "ワークスペース（テナント）の一覧を取得する。複数ワークスペースを利用している組織で、"
                "アクティブ／アーカイブ済みの棚卸しに使う。ページネーションは page 番号方式（1始まり）で"
                "1ページ100件固定。読み取り専用で書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり、1ページ100件固定）", "default": 1},
                    "status": {
                        "type": "string",
                        "enum": ["active", "archived"],
                        "description": "ワークスペースの状態で絞り込む（active=アクティブ / archived=アーカイブ済み）。省略時は全件",
                    },
                    "sort": {
                        "type": "string",
                        "enum": ["createdAt", "-createdAt", "updatedAt", "-updatedAt"],
                        "description": "並び替え基準（先頭に - を付けると降順）",
                    },
                },
            },
        ),
        types.Tool(
            name="list_deleted_candidates",
            description=(
                "削除済み候補者の一覧（候補者IDと削除日時のみ）を削除日時の降順で取得する。外部システムとの"
                "同期時に、Talentio 側で削除された候補者を検知して連携先からも除去する用途に使う。"
                "ページネーションは page 番号方式（1始まり）で1ページ100件固定。読み取り専用で書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり、1ページ100件固定）", "default": 1},
                    "deleted_at_from": {
                        "type": "string",
                        "description": "削除日時の範囲開始（yyyy-MM-ddThh:mm:ss）",
                    },
                    "deleted_at_to": {
                        "type": "string",
                        "description": "削除日時の範囲終了（yyyy-MM-ddThh:mm:ss）",
                    },
                },
            },
        ),
        types.Tool(
            name="list_candidate_comments",
            description=(
                "指定した候補者への社内コメント（選考メモ等）一覧を取得する。get_candidate の詳細情報には"
                "含まれないコメントスレッドを確認したい場合に使う。コメント内容にメンションが含まれる場合、"
                "`${email@example.com}` のような形式で本文中に埋め込まれる。candidate_id は list_candidates の"
                "レスポンスの id 値を指定する。読み取り専用で書き込みは行わない（コメント投稿 API は"
                "存在するが、本コネクタは読み取り中心の方針のため未実装）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "candidate_id": {"type": "string", "description": "候補者ID（list_candidates で取得）"},
                },
                "required": ["candidate_id"],
            },
        ),
        types.Tool(
            name="list_candidate_attachments",
            description=(
                "指定した候補者に添付されているファイル（履歴書・職務経歴書等）の一覧（ID・ファイル名のみ）を"
                "取得する。candidate_id は list_candidates のレスポンスの id 値を指定する。本APIはファイル名の"
                "一覧のみを返し、ファイル本体のダウンロードURLは含まれない。読み取り専用で書き込みは行わない"
                "（添付ファイルの追加・削除 API は存在するが、本コネクタは読み取り中心の方針のため未実装）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "candidate_id": {"type": "string", "description": "候補者ID（list_candidates で取得）"},
                },
                "required": ["candidate_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_candidates":
                params: dict = {"page": arguments.get("page", 1)}
                if arguments.get("status"):
                    params["status"] = arguments["status"]
                if arguments.get("requisition_ids"):
                    params["requisitionIds"] = _csv(arguments["requisition_ids"])
                if arguments.get("job_title_ids"):
                    params["jobTitleIds"] = _csv(arguments["job_title_ids"])
                if arguments.get("stage_statuses"):
                    params["stageStatuses"] = _csv(arguments["stage_statuses"])
                if arguments.get("applied_at_from"):
                    params["appliedAtFrom"] = arguments["applied_at_from"]
                if arguments.get("applied_at_to"):
                    params["appliedAtTo"] = arguments["applied_at_to"]
                if arguments.get("joined_at_from"):
                    params["joinedAtFrom"] = arguments["joined_at_from"]
                if arguments.get("joined_at_to"):
                    params["joinedAtTo"] = arguments["joined_at_to"]
                if arguments.get("updated_at_from"):
                    params["updatedAtFrom"] = arguments["updated_at_from"]
                if arguments.get("updated_at_to"):
                    params["updatedAtTo"] = arguments["updated_at_to"]
                if arguments.get("include_inactive_responsible_employees") is not None:
                    params["includeInactiveResponsibleEmployees"] = arguments[
                        "include_inactive_responsible_employees"
                    ]
                if arguments.get("sort"):
                    params["sort"] = arguments["sort"]
                r = client.get("/candidates", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_candidate":
                params = {}
                if arguments.get("include_inactive_responsible_employees") is not None:
                    params["includeInactiveResponsibleEmployees"] = arguments[
                        "include_inactive_responsible_employees"
                    ]
                r = client.get(f"/candidates/{arguments['candidate_id']}", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_jobs":
                params = {"page": arguments.get("page", 1)}
                if arguments.get("status"):
                    params["status"] = arguments["status"]
                if arguments.get("updated_at_from"):
                    params["updatedAtFrom"] = arguments["updated_at_from"]
                if arguments.get("updated_at_to"):
                    params["updatedAtTo"] = arguments["updated_at_to"]
                if arguments.get("sort"):
                    params["sort"] = arguments["sort"]
                r = client.get("/requisitions", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_job":
                r = client.get(f"/requisitions/{arguments['job_id']}")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_job_titles":
                params = {"page": arguments.get("page", 1)}
                if arguments.get("status"):
                    params["status"] = arguments["status"]
                if arguments.get("sort"):
                    params["sort"] = arguments["sort"]
                r = client.get("/job_titles", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_candidate_channels":
                params = {"page": arguments.get("page", 1)}
                if arguments.get("sort"):
                    params["sort"] = arguments["sort"]
                r = client.get("/candidate_channels", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_form_templates":
                params = {"page": arguments.get("page", 1)}
                r = client.get("/form_templates", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_employees":
                params = {"page": arguments.get("page", 1)}
                if arguments.get("status"):
                    params["status"] = arguments["status"]
                if arguments.get("role"):
                    params["role"] = arguments["role"]
                if arguments.get("sort"):
                    params["sort"] = arguments["sort"]
                r = client.get("/employees", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_employee_groups":
                params = {"page": arguments.get("page", 1)}
                if arguments.get("sort"):
                    params["sort"] = arguments["sort"]
                r = client.get("/employee_groups", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_workspaces":
                params = {"page": arguments.get("page", 1)}
                if arguments.get("status"):
                    params["status"] = arguments["status"]
                if arguments.get("sort"):
                    params["sort"] = arguments["sort"]
                r = client.get("/workspaces", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_deleted_candidates":
                params = {"page": arguments.get("page", 1)}
                if arguments.get("deleted_at_from"):
                    params["deletedAtFrom"] = arguments["deleted_at_from"]
                if arguments.get("deleted_at_to"):
                    params["deletedAtTo"] = arguments["deleted_at_to"]
                r = client.get("/candidates/deleted", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_candidate_comments":
                r = client.get(f"/candidates/{arguments['candidate_id']}/comments")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_candidate_attachments":
                r = client.get(f"/candidates/{arguments['candidate_id']}/attachments")
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
