import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("smarthr-mcp")


def get_client() -> httpx.Client:
    token = os.environ.get("SMARTHR_ACCESS_TOKEN")
    tenant = os.environ.get("SMARTHR_TENANT_ID")
    if not token:
        raise ValueError("SMARTHR_ACCESS_TOKEN が設定されていません")
    if not tenant:
        raise ValueError("SMARTHR_TENANT_ID が設定されていません")
    return httpx.Client(
        base_url=f"https://{tenant}.smarthr.jp/api/v1",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_crews",
            description=(
                "指定した条件に合致する従業員（crew）の一覧を取得する（SmartHR公式APIの GET /v1/crews に対応）。"
                "在籍状況・部署・雇用形態・役職・入社日/退職日の範囲・氏名や部署名でのフリーワード検索など"
                "複数条件を組み合わせて絞り込める。特定の従業員IDが既に分かっている場合は id パラメータに"
                "カンマ区切りで複数指定すれば、get_crew を何度も呼ぶより1回のリクエストでまとめて取得できる。"
                "ページネーションは page/per_page 方式（1始まり）。API側の既定は page=1・per_page=10 だが、"
                "本ツールは既定で20件に設定している（最大件数は公式リファレンスに明記されていないため未検証。"
                "コミュニティ情報では100件程度が目安とされる）。既定の並び順は公式ドキュメントに明記されていない。"
                "レスポンスは1人あたりの項目数が非常に多い（社会保険・給与・カスタム項目等を含む）ため、"
                "件数が多い場合や特定項目だけ必要な場合は fields パラメータで取得項目をカンマ区切りに絞ると"
                "出力の切り詰めを避けやすい。書き込みは行わない（読み取り専用）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり、既定1）", "default": 1},
                    "per_page": {
                        "type": "integer",
                        "description": "1ページあたりの件数（API既定は10。最大値は公式ドキュメント未記載）",
                        "default": 20,
                    },
                    "employment_type_id": {
                        "type": "string",
                        "description": "雇用形態IDで絞り込む（複数指定する場合はカンマ区切り）",
                    },
                    "department_id": {
                        "type": "string",
                        "description": "所属部署IDで絞り込む（複数指定する場合はカンマ区切り）",
                    },
                    "position_id": {
                        "type": "string",
                        "description": "役職IDで絞り込む（複数指定する場合はカンマ区切り）",
                    },
                    "emp_status": {
                        "type": "string",
                        "enum": ["employed", "absent", "retired"],
                        "description": "在籍状況で絞り込む（employed=在籍中 / absent=休職中 / retired=退職済み）",
                    },
                    "entered_at_from": {"type": "string", "description": "この日付（yyyy-MM-dd）以降に入社した従業員に絞り込む"},
                    "entered_at_to": {"type": "string", "description": "この日付（yyyy-MM-dd）以前に入社した従業員に絞り込む"},
                    "resigned_at_from": {"type": "string", "description": "この日付（yyyy-MM-dd）以降に退職した従業員に絞り込む"},
                    "resigned_at_to": {"type": "string", "description": "この日付（yyyy-MM-dd）以前に退職した従業員に絞り込む"},
                    "q": {"type": "string", "description": "氏名・ビジネスネーム・部署名・役職名によるフリーワード検索"},
                    "id": {
                        "type": "string",
                        "description": "取得したい従業員IDをカンマ区切りで複数指定する（分かっているIDをまとめて取得したい場合に使う）",
                    },
                    "sort": {
                        "type": "string",
                        "description": (
                            "並び順を指定する。指定可能な値の具体的な形式（フィールド名や昇順/降順の記法）は"
                            "公式ドキュメントに明記されていないため、必要な場合は実際の挙動を確認しながら使用すること"
                        ),
                    },
                    "fields": {
                        "type": "string",
                        "description": "レスポンスに含める項目名をカンマ区切りで指定する（省略時は全項目を返す）",
                    },
                },
            },
        ),
        types.Tool(
            name="get_crew",
            description=(
                "従業員（crew）1名の詳細情報を取得する（GET /v1/crews/{id}）。id には社員番号（emp_code）ではなく、"
                "SmartHR内部の従業員ID（list_crews のレスポンスの id フィールド）を指定する必要がある。"
                "社員番号から従業員を探したい場合は list_crews の emp_code パラメータで絞り込むこと。"
                "レスポンスは社会保険・給与・カスタム項目等を含む詳細な1人分のデータで、fields で取得項目を"
                "絞り込むこともできる。複数名をまとめて取得したい場合は、本ツールを繰り返し呼ぶより "
                "list_crews の id パラメータにカンマ区切りで複数IDを渡す方がリクエスト数を節約できる。"
                "書き込みは行わない（読み取り専用）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "従業員ID（list_crews のレスポンスの id フィールド。社員番号ではない）"},
                    "fields": {
                        "type": "string",
                        "description": "レスポンスに含める項目名をカンマ区切りで指定する（省略時は全項目を返す）",
                    },
                },
                "required": ["id"],
            },
        ),
        types.Tool(
            name="list_departments",
            description=(
                "部署一覧を取得する（GET /v1/departments）。返るのはフラットなリストで、各要素が親部署の情報を "
                "parent（id・name・full_name等を含むオブジェクト）として、子部署を children として持つため、"
                "階層構造が必要な場合は parent/children を辿って組み立てる。ページネーションは page/per_page方式"
                "（API既定は page=1・per_page=10。本ツールの既定は50件）。code で部署コードによる絞り込みができる。"
                "部署の作成・更新・削除・廃止（POST /v1/departments/{id}/discontinue）のAPIはSmartHR側に存在するが、"
                "本コネクタは読み取り専用のため未実装。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり、既定1）", "default": 1},
                    "per_page": {
                        "type": "integer",
                        "description": "1ページあたりの件数（API既定は10）",
                        "default": 50,
                    },
                    "code": {"type": "string", "description": "部署コードで絞り込む"},
                    "sort": {
                        "type": "string",
                        "description": (
                            "並び順を指定する。指定可能な値の具体的な形式は公式ドキュメントに明記されていない"
                        ),
                    },
                },
            },
        ),
        types.Tool(
            name="list_employment_types",
            description=(
                "雇用形態一覧を取得する（GET /v1/employment_types、正社員・パート・契約社員等）。"
                "ページネーションは page/per_page方式（API既定は page=1・per_page=10。本ツールの既定は50件）。"
                "絞り込み用のクエリパラメータ（名称検索等）はAPI側に存在しない。雇用形態の作成・更新・削除の"
                "APIはSmartHR側に存在するが、本コネクタは読み取り専用のため未実装。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり、既定1）", "default": 1},
                    "per_page": {
                        "type": "integer",
                        "description": "1ページあたりの件数（API既定は10）",
                        "default": 50,
                    },
                },
            },
        ),
        types.Tool(
            name="update_crew",
            description=(
                "従業員情報を部分更新する（PATCH /v1/crews/{id}）。指定した項目のみが更新され、省略した項目は"
                "変更されない。部署異動には department_ids（部署IDの配列。所属させたい部署IDをすべて列挙する。"
                "1件だけに異動させる場合も配列で1要素を渡す）を使う。雇用形態変更には employment_type_id"
                "（単一の雇用形態ID文字列）を使う。同じ内容で複数回呼び出しても結果は同じになる（べき等）。"
                "本ツールが対応するのはよく使う一部の項目（部署・雇用形態・氏名・メールアドレス）のみで、"
                "SmartHR API自体が持つ社会保険・給与・カスタム項目等の広範な更新項目は未実装。従業員の削除"
                "（DELETE /v1/crews/{id}）や招待メール送信（PUT /v1/crews/{id}/invite）のAPIも存在するが、"
                "誤操作時の影響が大きいため本コネクタでは未実装。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "従業員ID"},
                    "department_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "異動先の部署IDの配列（所属させたい部署IDをすべて列挙する）",
                    },
                    "employment_type_id": {"type": "string", "description": "変更後の雇用形態ID（単一ID）"},
                    "last_name": {"type": "string", "description": "姓"},
                    "first_name": {"type": "string", "description": "名"},
                    "email": {"type": "string", "description": "メールアドレス"},
                },
                "required": ["id"],
            },
        ),
        types.Tool(
            name="list_dependents",
            description=(
                "指定した従業員に紐づく家族情報（扶養家族等）の一覧を取得する"
                "（GET /v1/crews/{crew_id}/dependents）。crew_id には SmartHR内部の従業員ID"
                "（list_crews のレスポンスの id フィールド）を指定する。ページネーションは"
                "page/per_page方式（API既定は page=1・per_page=10。本ツールの既定も同じ）。"
                "書き込みは行わない（読み取り専用）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "crew_id": {"type": "string", "description": "従業員ID（list_crews のレスポンスの id フィールド）"},
                    "page": {"type": "integer", "description": "ページ番号（1始まり、既定1）", "default": 1},
                    "per_page": {
                        "type": "integer",
                        "description": "1ページあたりの件数（API既定は10）",
                        "default": 10,
                    },
                },
                "required": ["crew_id"],
            },
        ),
        types.Tool(
            name="list_job_titles",
            description=(
                "役職一覧を取得する（GET /v1/job_titles）。各要素は id・name（役職名）・"
                "rank（役職のランク、1〜99999）・code（役職コード）等を含む。ページネーションは"
                "page/per_page方式（API既定は page=1・per_page=10。本ツールの既定も同じ）。"
                "sort パラメータで並び順を指定できるが、指定可能な値の具体的な形式は"
                "公式ドキュメントに明記されていない。役職の作成・更新・削除のAPIはSmartHR側に"
                "存在するが、本コネクタは読み取り専用のため未実装。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり、既定1）", "default": 1},
                    "per_page": {
                        "type": "integer",
                        "description": "1ページあたりの件数（API既定は10）",
                        "default": 10,
                    },
                    "sort": {
                        "type": "string",
                        "description": "並び順を指定する。指定可能な値の具体的な形式は公式ドキュメントに明記されていない",
                    },
                },
            },
        ),
        types.Tool(
            name="list_grades",
            description=(
                "等級一覧を取得する（GET /v1/grades）。各要素は id・name（等級名）・"
                "rank（等級のランク）・code（等級コード）等を含む。ページネーションは"
                "page/per_page方式（API既定は page=1・per_page=10。本ツールの既定も同じ）。"
                "等級の作成・更新・削除のAPIはSmartHR側に存在するが、本コネクタは読み取り専用の"
                "ため未実装。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり、既定1）", "default": 1},
                    "per_page": {
                        "type": "integer",
                        "description": "1ページあたりの件数（API既定は10）",
                        "default": 10,
                    },
                },
            },
        ),
        types.Tool(
            name="list_job_categories",
            description=(
                "職種一覧を取得する（GET /v1/job_categories）。各要素は id・name（職種名）・"
                "created_at・updated_at を含む。ページネーションは page/per_page方式"
                "（API既定は page=1・per_page=10。本ツールの既定も同じ）。職種の作成・更新・"
                "削除のAPIはSmartHR側に存在するが、本コネクタは読み取り専用のため未実装。"
                "書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり、既定1）", "default": 1},
                    "per_page": {
                        "type": "integer",
                        "description": "1ページあたりの件数（API既定は10）",
                        "default": 10,
                    },
                },
            },
        ),
        types.Tool(
            name="list_recruitment_types",
            description=(
                "採用区分一覧を取得する（GET /v1/recruitment_types）。各要素は id・"
                "name（採用区分名）・preset_type（プリセット種別）等を含む。ページネーションは"
                "page/per_page方式（API既定は page=1・per_page=10。本ツールの既定も同じ）。"
                "採用区分の作成・更新・削除のAPIはSmartHR側に存在するが、本コネクタは読み取り"
                "専用のため未実装。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり、既定1）", "default": 1},
                    "per_page": {
                        "type": "integer",
                        "description": "1ページあたりの件数（API既定は10）",
                        "default": 10,
                    },
                },
            },
        ),
        types.Tool(
            name="list_dependent_relations",
            description=(
                "続柄（家族情報の続柄区分）の一覧を取得する（GET /v1/dependent_relations）。"
                "各要素は id・name（続柄名）・preset_type（プリセット続柄）等を含む。"
                "filter パラメータで絞り込みができる（公式ドキュメント上の指定可能値は"
                "spouse のみ確認できた）。ページネーションは page/per_page方式（API既定は"
                "page=1・per_page=10。本ツールの既定も同じ）。書き込みは行わない（読み取り専用）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {
                        "type": "string",
                        "description": "続柄の絞り込み条件（公式ドキュメント上で確認できた指定可能値は spouse のみ）",
                    },
                    "page": {"type": "integer", "description": "ページ番号（1始まり、既定1）", "default": 1},
                    "per_page": {
                        "type": "integer",
                        "description": "1ページあたりの件数（API既定は10）",
                        "default": 10,
                    },
                },
            },
        ),
        types.Tool(
            name="list_biz_establishments",
            description=(
                "事業所一覧を取得する（GET /v1/biz_establishments）。社会保険・労働保険の"
                "適用事業所単位の情報（健康保険組合の種類等）を含む。ページネーションは"
                "page/per_page方式（API既定は page=1・per_page=10。本ツールの既定も同じ）。"
                "embed パラメータで関連情報（soc_ins_owner / lab_ins_owner / company）を"
                "埋め込める。書き込みは行わない（読み取り専用）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり、既定1）", "default": 1},
                    "per_page": {
                        "type": "integer",
                        "description": "1ページあたりの件数（API既定は10）",
                        "default": 10,
                    },
                    "embed": {
                        "type": "string",
                        "enum": ["soc_ins_owner", "lab_ins_owner", "company"],
                        "description": "レスポンスに埋め込む関連オブジェクト",
                    },
                },
            },
        ),
        types.Tool(
            name="list_users",
            description=(
                "SmartHRのログインユーザー（管理者・利用者アカウント）一覧を取得する"
                "（GET /v1/users）。各要素は id・email（ログイン用メールアドレス）・"
                "notification_email（通知用メールアドレス）・admin（管理者フラグ）・role"
                "（権限）等を含む。招待ステータスは invitation_answered_at / invitation_created_at "
                "/ invitation_opened_at の値の有無で判定できる（詳細はSmartHR公式ドキュメント参照）。"
                "ページネーションは page/per_page方式（API既定は page=1・per_page=10。本ツールの"
                "既定も同じ）。embed パラメータで関連情報（crew / biz_establishment / "
                "biz_establishment_company / department_company）を埋め込める。書き込みは"
                "行わない（読み取り専用）。従業員（crew）ではなくSmartHRへのログインアカウント"
                "を扱う点に注意（従業員一覧は list_crews を使う）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり、既定1）", "default": 1},
                    "per_page": {
                        "type": "integer",
                        "description": "1ページあたりの件数（API既定は10）",
                        "default": 10,
                    },
                    "sort": {
                        "type": "string",
                        "description": "並び順を指定する。指定可能な値の具体的な形式は公式ドキュメントに明記されていない",
                    },
                    "embed": {
                        "type": "string",
                        "enum": ["crew", "biz_establishment", "biz_establishment_company", "department_company"],
                        "description": "レスポンスに埋め込む関連オブジェクト",
                    },
                },
            },
        ),
        types.Tool(
            name="list_companies",
            description=(
                "会社情報の一覧を取得する（GET /v1/companies）。通常はテナントに紐づく"
                "1社分の会社情報が返る。ページネーションは page/per_page方式（API既定は"
                "page=1・per_page=10。本ツールの既定も同じ）。書き込みは行わない（読み取り専用）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり、既定1）", "default": 1},
                    "per_page": {
                        "type": "integer",
                        "description": "1ページあたりの件数（API既定は10）",
                        "default": 10,
                    },
                },
            },
        ),
        types.Tool(
            name="list_payment_periods",
            description=(
                "給与支給形態の一覧を取得する（GET /v1/payment_periods）。給与の締め日・"
                "支払日等の設定情報を含む。ページネーションは page/per_page方式（API既定は"
                "page=1・per_page=10。本ツールの既定も同じ）。書き込みは行わない（読み取り専用）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり、既定1）", "default": 1},
                    "per_page": {
                        "type": "integer",
                        "description": "1ページあたりの件数（API既定は10）",
                        "default": 10,
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with get_client() as client:
            if name == "list_crews":
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 20),
                }
                if arguments.get("employment_type_id"):
                    params["employment_type_id"] = arguments["employment_type_id"]
                if arguments.get("department_id"):
                    params["department_id"] = arguments["department_id"]
                if arguments.get("position_id"):
                    params["position_id"] = arguments["position_id"]
                if arguments.get("emp_status"):
                    params["emp_status"] = arguments["emp_status"]
                if arguments.get("entered_at_from"):
                    params["entered_at_from"] = arguments["entered_at_from"]
                if arguments.get("entered_at_to"):
                    params["entered_at_to"] = arguments["entered_at_to"]
                if arguments.get("resigned_at_from"):
                    params["resigned_at_from"] = arguments["resigned_at_from"]
                if arguments.get("resigned_at_to"):
                    params["resigned_at_to"] = arguments["resigned_at_to"]
                if arguments.get("q"):
                    params["q"] = arguments["q"]
                if arguments.get("id"):
                    params["id"] = arguments["id"]
                if arguments.get("sort"):
                    params["sort"] = arguments["sort"]
                if arguments.get("fields"):
                    params["fields"] = arguments["fields"]
                r = client.get("/crews", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_crew":
                params = {}
                if arguments.get("fields"):
                    params["fields"] = arguments["fields"]
                r = client.get(f"/crews/{arguments['id']}", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_departments":
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 50),
                }
                if arguments.get("code"):
                    params["code"] = arguments["code"]
                if arguments.get("sort"):
                    params["sort"] = arguments["sort"]
                r = client.get("/departments", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_employment_types":
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 50),
                }
                r = client.get("/employment_types", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "update_crew":
                crew_id = arguments.pop("id")
                payload = {k: v for k, v in arguments.items() if v is not None}
                r = client.patch(f"/crews/{crew_id}", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_dependents":
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 10),
                }
                r = client.get(f"/crews/{arguments['crew_id']}/dependents", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_job_titles":
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 10),
                }
                if arguments.get("sort"):
                    params["sort"] = arguments["sort"]
                r = client.get("/job_titles", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_grades":
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 10),
                }
                r = client.get("/grades", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_job_categories":
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 10),
                }
                r = client.get("/job_categories", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_recruitment_types":
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 10),
                }
                r = client.get("/recruitment_types", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_dependent_relations":
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 10),
                }
                if arguments.get("filter"):
                    params["filter"] = arguments["filter"]
                r = client.get("/dependent_relations", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_biz_establishments":
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 10),
                }
                if arguments.get("embed"):
                    params["embed"] = arguments["embed"]
                r = client.get("/biz_establishments", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_users":
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 10),
                }
                if arguments.get("sort"):
                    params["sort"] = arguments["sort"]
                if arguments.get("embed"):
                    params["embed"] = arguments["embed"]
                r = client.get("/users", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_companies":
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 10),
                }
                r = client.get("/companies", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_payment_periods":
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 10),
                }
                r = client.get("/payment_periods", params=params)
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
