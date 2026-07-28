import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("jobcan-workflow-mcp")

BASE_URL = "https://ssl.wf.jobcan.jp/wf_api"


def _client() -> httpx.Client:
    token = os.environ.get("JOBCAN_API_TOKEN")
    if not token:
        raise ValueError("JOBCAN_API_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Token {token}", "Content-Type": "application/json"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_requests",
            description=(
                "ジョブカン経費精算/ワークフローの申請書一覧を、ステータス・申請者・グループ・"
                "プロジェクト・日付範囲などで絞り込んで取得する（GET /v2/requests/）。「今月の申請を"
                "見せて」「進行中の申請一覧」のような棚卸し・一覧確認に使う。1件の詳細（明細行や"
                "コメント履歴を含む全項目）が必要な場合は get_request を使うこと。並び順は既定で"
                "sort_by=applied_date_desc（申請日の新しい順）。ページネーションはページ番号方式で"
                "1ページ100件固定：レスポンスの next が null でなければ page を1つ増やして再取得する"
                "（next には次ページの完全なURLが入るが、本ツールは page 番号のみ受け付ける）。"
                "applied_after/applied_before/completed_after/completed_before の日付は "
                "yyyy/mm/dd または yyyy/mm/dd hh:mm:ss 形式で指定する（ハイフン区切りは受け付けられない"
                "可能性が高い）。include_canceled を true にしない限り、取り消し済みの申請は"
                "結果から除外される。読み取り専用で副作用はない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "申請書IDで絞り込み（完全一致）。複数指定する場合はカンマ区切りで指定（例: \"123,456\"）。",
                    },
                    "status": {
                        "type": "string",
                        "description": "申請状況で絞り込み（in_progress: 進行中, completed: 完了, rejected: 却下, returned: 差し戻し, canceled: 取り消し, canceled_after_completion: 完了後取消）。",
                        "enum": ["in_progress", "completed", "rejected", "returned", "canceled", "canceled_after_completion"],
                    },
                    "form_id": {
                        "type": "string",
                        "description": "フォームID（申請書の様式）で絞り込み（完全一致）。フォームIDが不明な場合は絞り込まずに一覧を取得し、結果の form 情報から確認する。",
                    },
                    "title": {
                        "type": "string",
                        "description": "申請書タイトルで絞り込み（部分一致）。",
                    },
                    "applicant_code": {
                        "type": "string",
                        "description": "申請者のスタッフコード（ユーザーコード）で絞り込み（完全一致）。list_users で取得できるユーザーコードを指定する。",
                    },
                    "group_code": {
                        "type": "string",
                        "description": "申請者が所属するグループ（部署）のコードで絞り込み（完全一致）。",
                    },
                    "project_code": {
                        "type": "string",
                        "description": "プロジェクトコードで絞り込み（完全一致）。list_projects で取得できるコードを指定する。",
                    },
                    "applied_after": {
                        "type": "string",
                        "description": "申請日時の開始（この日時以降に申請されたものを抽出）。yyyy/mm/dd または yyyy/mm/dd hh:mm:ss 形式（例: \"2024/01/01\"）。",
                    },
                    "applied_before": {
                        "type": "string",
                        "description": "申請日時の終了（この日時以前に申請されたものを抽出）。yyyy/mm/dd または yyyy/mm/dd hh:mm:ss 形式。",
                    },
                    "completed_after": {
                        "type": "string",
                        "description": "最終承認日時の開始（この日時以降に最終承認されたものを抽出）。yyyy/mm/dd または yyyy/mm/dd hh:mm:ss 形式。未承認・進行中の申請には最終承認日がないため対象外になる。",
                    },
                    "completed_before": {
                        "type": "string",
                        "description": "最終承認日時の終了（この日時以前に最終承認されたものを抽出）。yyyy/mm/dd または yyyy/mm/dd hh:mm:ss 形式。",
                    },
                    "include_canceled": {
                        "type": "boolean",
                        "description": "取り消し済みの申請も結果に含めるか（既定は false = 除外）。取り消し申請だけを見たい場合は status=canceled と併用する。",
                        "default": False,
                    },
                    "sort_by": {
                        "type": "string",
                        "description": "並び順（applied_date_asc: 申請日昇順, applied_date_desc: 申請日降順[既定], group: グループ順, form: フォーム順, user: 申請者順）。",
                        "enum": ["applied_date_asc", "applied_date_desc", "group", "form", "user"],
                    },
                    "page": {
                        "type": "integer",
                        "description": "ページ番号（デフォルト: 1）。1ページ100件固定。レスポンスの next が null でなければ次ページが存在する。",
                        "default": 1,
                    },
                },
            },
        ),
        types.Tool(
            name="get_request",
            description=(
                "申請書1件の詳細情報を取得する（GET /v2/requests/{request_id}/）。list_requests の"
                "一覧には含まれない明細行・添付ファイル情報・承認ルートの進捗などを確認したいときに使う。"
                "request_id は list_requests のレスポンスに含まれる id フィールドの値を指定する。"
                "読み取り専用で副作用はない。承認・却下・差し戻しを行うAPIエンドポイントは本APIには"
                "存在しない（承認操作はジョブカンのWeb画面上でのみ可能）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "request_id": {
                        "type": "integer",
                        "description": "申請書ID（list_requests のレスポンスの id フィールドで取得できる）。",
                    },
                },
                "required": ["request_id"],
            },
        ),
        types.Tool(
            name="list_users",
            description=(
                "ジョブカンに登録されているユーザーの一覧を取得する（GET /v3/users/）。list_requests の"
                "applicant_code に指定するスタッフコードを調べる際などに使う。v3 を使用しているのは、"
                "v1/v2 に比べて所属（グループ・役職）が構造化されたオブジェクトで返り、v3 のみメモ欄"
                "（memo）も含まれるため。ページネーションはページ番号方式：レスポンスの next が null で"
                "なければ page を1つ増やして再取得する（1ページあたりの件数・並び順はAPIドキュメントに"
                "明記されておらず未検証）。page 以外の絞り込みパラメータ（氏名・グループ等）はAPIドキュメント"
                "上に存在しない。なお本APIにはユーザー作成（POST）・更新（PUT）・無効化（DELETE）の"
                "エンドポイントが存在するが、本コネクタでは読み取り専用ツールのみを実装しており未対応。"
                "読み取り専用で副作用はない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer",
                        "description": "ページ番号（デフォルト: 1）。1ページあたりの件数はAPIドキュメントに明記なし。",
                        "default": 1,
                    },
                },
            },
        ),
        types.Tool(
            name="list_projects",
            description=(
                "ジョブカンに登録されているプロジェクト一覧を取得する（GET /v1/projects/）。"
                "list_requests の project_code に指定するコードを調べる際などに使う。ページネーションは"
                "ページ番号方式：レスポンスの next が null でなければ page を1つ増やして再取得する"
                "（1ページあたりの件数・並び順はAPIドキュメントに明記されておらず未検証）。page 以外の"
                "絞り込みパラメータ（プロジェクト名等）はAPIドキュメント上に存在しない。なお本APIには"
                "プロジェクト作成（POST）・更新（PUT）・削除（DELETE）のエンドポイントが存在するが、"
                "本コネクタでは読み取り専用ツールのみを実装しており未対応。読み取り専用で副作用はない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer",
                        "description": "ページ番号（デフォルト: 1）。1ページあたりの件数はAPIドキュメントに明記なし。",
                        "default": 1,
                    },
                },
            },
        ),
        types.Tool(
            name="list_companies",
            description=(
                "ジョブカンに登録されている取引先（会社）一覧を取得する（GET /v1/company/）。経費精算の"
                "取引先マスタを確認したいときに使う。ページネーションはページ番号方式：レスポンスの next が"
                "null でなければ page を1つ増やして再取得する（1ページあたりの件数・並び順はAPIドキュメント"
                "に明記されておらず未検証）。page 以外の絞り込みパラメータ（取引先名等）はAPIドキュメント上"
                "に存在しない。なお本APIには取引先作成（POST）・更新（PUT）・削除（DELETE）のエンドポイント"
                "が存在するが、本コネクタでは読み取り専用ツールのみを実装しており未対応。読み取り専用で"
                "副作用はない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer",
                        "description": "ページ番号（デフォルト: 1）。1ページ100件固定。next が null でなければ次ページが存在する。",
                        "default": 1,
                    },
                },
            },
        ),
        types.Tool(
            name="list_forms",
            description=(
                "ジョブカンに登録されている申請フォーム（申請書の様式）の一覧を取得する（GET /v1/forms/）。"
                "list_requests の form_id に指定するフォームIDや、どんな申請様式が使えるかを調べる際に使う。"
                "form_type（general: 一般ワークフロー, expense: 経費精算, payment: 支払依頼, ec_purchase: EC購買）や "
                "settlement_type（pre_application: 事前申請, settlement: 精算。expense フォームでのみ有効）、"
                "フォーム名の部分一致（name）などで絞り込める。レスポンスの results 各要素には id・category・"
                "form_type・settlement_type・name・view_type・description が含まれ、この id が list_requests の "
                "form_id に相当する。ページネーションはページ番号方式で1ページ100件固定：レスポンスの next が "
                "null でなければ page を1つ増やして再取得する。読み取り専用で副作用はない。フォームの作成・更新・"
                "削除エンドポイントは本APIに存在しない（フォーム設計はWeb管理画面でのみ行う）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "form_type": {
                        "type": "string",
                        "description": "フォーム種別で絞り込み（general: 一般ワークフロー / expense: 経費精算 / payment: 支払依頼 / ec_purchase: EC購買）。",
                        "enum": ["general", "expense", "payment", "ec_purchase"],
                    },
                    "settlement_type": {
                        "type": "string",
                        "description": "精算種別で絞り込み（pre_application: 事前申請 / settlement: 精算）。form_type=expense のフォームでのみ意味を持つ。",
                        "enum": ["pre_application", "settlement"],
                    },
                    "category_code": {
                        "type": "string",
                        "description": "フォームのカテゴリ（分類）コードで絞り込み（完全一致）。",
                    },
                    "name": {
                        "type": "string",
                        "description": "フォーム名で絞り込み（部分一致）。",
                    },
                    "view_type": {
                        "type": "string",
                        "description": "公開範囲で絞り込み（public: 全体公開 / private: 非公開 / restricted: 限定公開）。",
                        "enum": ["public", "private", "restricted"],
                    },
                    "description": {
                        "type": "string",
                        "description": "フォームの説明文で絞り込み（部分一致）。",
                    },
                    "page": {
                        "type": "integer",
                        "description": "ページ番号（デフォルト: 1）。1ページ100件固定。next が null でなければ次ページが存在する。",
                        "default": 1,
                    },
                },
            },
        ),
        types.Tool(
            name="list_groups",
            description=(
                "ジョブカンに登録されているグループ（部署）の一覧を取得する（GET /v1/groups/）。list_requests の "
                "group_code に指定する部署コードを調べる際などに使う。レスポンスの results 各要素には "
                "group_code・group_name・parent_group_code（親グループのコード。階層構造を表す）・description が"
                "含まれる。ページネーションはページ番号方式で1ページ100件固定：レスポンスの next が null で"
                "なければ page を1つ増やして再取得する。API仕様上、page 以外の絞り込みパラメータ（グループ名等）は"
                "存在しない。個別のグループ詳細取得（GET /v1/groups/{group_code}/）も実在するが、一覧と同じ項目"
                "しか返らないため本コネクタでは実装していない。読み取り専用で副作用はない。グループの作成・更新・"
                "削除エンドポイントは本APIに存在するが、副作用を避けるため未実装。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer",
                        "description": "ページ番号（デフォルト: 1）。1ページ100件固定。next が null でなければ次ページが存在する。",
                        "default": 1,
                    },
                },
            },
        ),
        types.Tool(
            name="list_positions",
            description=(
                "ジョブカンに登録されている役職の一覧を取得する（GET /v1/positions/）。ユーザーに紐づく役職"
                "コードの意味を調べる際などに使う。レスポンスの results 各要素には position_code・position_name・"
                "description が含まれる。ページネーションはページ番号方式で1ページ100件固定：レスポンスの next が "
                "null でなければ page を1つ増やして再取得する。API仕様上、page 以外の絞り込みパラメータは存在"
                "しない。個別の役職詳細取得（GET /v1/positions/{position_code}/）も実在するが、一覧と同じ項目しか"
                "返らないため本コネクタでは実装していない。読み取り専用で副作用はない。役職の作成・更新・削除"
                "エンドポイントは本APIに存在するが、副作用を避けるため未実装。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer",
                        "description": "ページ番号（デフォルト: 1）。1ページ100件固定。next が null でなければ次ページが存在する。",
                        "default": 1,
                    },
                },
            },
        ),
        types.Tool(
            name="get_user",
            description=(
                "指定した1人のユーザーの詳細情報を取得する（GET /v1/users/{user_code}/）。list_users の一覧では"
                "把握しづらい個別ユーザーの詳細（メールアドレス・承認権限 is_approver・修正権限 is_modifier・"
                "ユーザーロール user_role・所属グループ user_groups・役職 user_positions・振込口座 "
                "user_bank_account など）をピンポイントで確認したいときに使う。user_code は list_users のレスポンスや "
                "list_requests の applicant_code で得られるスタッフコードを指定する。個別詳細は v1 エンドポイントを"
                "使用しており、メモ欄（memo）は含まれない（memo が必要な場合は list_users の v3 一覧を参照）。"
                "読み取り専用で副作用はない。ユーザーの作成（POST）・更新（PUT）・無効化（DELETE）エンドポイントは"
                "本APIに存在するが、副作用を避けるため未実装。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_code": {
                        "type": "string",
                        "description": "ユーザーのスタッフコード（list_users のレスポンスや list_requests の applicant_code で取得できる）。",
                    },
                },
                "required": ["user_code"],
            },
        ),
        types.Tool(
            name="get_company",
            description=(
                "指定した1件の取引先（会社）の詳細情報を取得する（GET /v1/company/{company_code}/）。"
                "list_companies の一覧よりも詳しい項目、特に振込先口座情報（bank_code・bank_name・branch_code・"
                "branch_name・bank_account_type_code・bank_account_code・bank_account_name_kana）や適格請求書発行"
                "事業者登録番号（invoice_registrated_number）、郵便番号・住所（zip_code・address）まで確認したい"
                "ときに使う。company_code は list_companies のレスポンスで得られるコードを指定する。読み取り専用で"
                "副作用はない。取引先の作成（POST）・更新（PUT）・削除（DELETE）エンドポイントは本APIに存在するが、"
                "副作用を避けるため未実装。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "company_code": {
                        "type": "string",
                        "description": "取引先コード（list_companies のレスポンスで取得できる）。",
                    },
                },
                "required": ["company_code"],
            },
        ),
        types.Tool(
            name="get_generic_master",
            description=(
                "汎用マスタ（ユーザーが「汎用マスタ」画面で自由に定義したマスタデータ）の1つを、その登録レコード"
                "一覧とともに取得する（GET /v1/generic_master/{generic_master_code}/）。費目・勘定科目・拠点など、"
                "標準マスタ（グループ/役職/プロジェクト/取引先）に当てはまらない独自の選択肢マスタを申請フォームで"
                "使っている場合に、その中身を確認する用途で使う。generic_master_code はジョブカンの「汎用マスタ」"
                "画面で登録したコードを指定する必要があり、コード自体はAPIでは作成できない（Web画面でのみ登録）。"
                "どんな汎用マスタコードが存在するかを一覧するAPIは提供されていないため、コードは事前に管理者に"
                "確認する必要がある。ページネーションはページ番号方式で1ページ100件固定：レスポンスの next が "
                "null でなければ page を1つ増やして再取得する。読み取り専用で副作用はない。汎用マスタレコードの"
                "作成・更新・削除エンドポイントは本APIに存在するが、副作用を避けるため未実装。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "generic_master_code": {
                        "type": "string",
                        "description": "汎用マスタのコード（ジョブカンの「汎用マスタ」画面で登録したコード）。",
                    },
                    "page": {
                        "type": "integer",
                        "description": "ページ番号（デフォルト: 1）。1ページ100件固定。next が null でなければ次ページが存在する。",
                        "default": 1,
                    },
                },
                "required": ["generic_master_code"],
            },
        ),
        types.Tool(
            name="validate_token",
            description=(
                "APIトークンが有効かどうかを検証する（GET /test/）。JOBCAN_API_TOKEN が正しく設定・発行されて"
                "いるか、認証が通るかを確認する接続テスト用。成功すると 200 で {\"test\": \"ok\"} 相当、トークンが"
                "無効なら 401 を返す。他のツールで 401 エラーが出るときの切り分けに使う。パラメータは不要。"
                "読み取り専用で副作用はない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_requests":
                params: dict = {"page": arguments.get("page", 1)}
                if arguments.get("id"):
                    params["id"] = arguments["id"]
                if arguments.get("status"):
                    params["status"] = arguments["status"]
                if arguments.get("form_id"):
                    params["form_id"] = arguments["form_id"]
                if arguments.get("title"):
                    params["title"] = arguments["title"]
                if arguments.get("applicant_code"):
                    params["applicant_code"] = arguments["applicant_code"]
                if arguments.get("group_code"):
                    params["group_code"] = arguments["group_code"]
                if arguments.get("project_code"):
                    params["project_code"] = arguments["project_code"]
                if arguments.get("applied_after"):
                    params["applied_after"] = arguments["applied_after"]
                if arguments.get("applied_before"):
                    params["applied_before"] = arguments["applied_before"]
                if arguments.get("completed_after"):
                    params["completed_after"] = arguments["completed_after"]
                if arguments.get("completed_before"):
                    params["completed_before"] = arguments["completed_before"]
                if "include_canceled" in arguments:
                    params["include_canceled"] = arguments["include_canceled"]
                if arguments.get("sort_by"):
                    params["sort_by"] = arguments["sort_by"]
                r = client.get("/v2/requests/", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_request":
                rid = arguments["request_id"]
                r = client.get(f"/v2/requests/{rid}/")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_users":
                params = {"page": arguments.get("page", 1)}
                r = client.get("/v3/users/", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_projects":
                params = {"page": arguments.get("page", 1)}
                r = client.get("/v1/projects/", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_companies":
                params = {"page": arguments.get("page", 1)}
                r = client.get("/v1/company/", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_forms":
                params = {"page": arguments.get("page", 1)}
                if arguments.get("form_type"):
                    params["form_type"] = arguments["form_type"]
                if arguments.get("settlement_type"):
                    params["settlement_type"] = arguments["settlement_type"]
                if arguments.get("category_code"):
                    params["category_code"] = arguments["category_code"]
                if arguments.get("name"):
                    params["name"] = arguments["name"]
                if arguments.get("view_type"):
                    params["view_type"] = arguments["view_type"]
                if arguments.get("description"):
                    params["description"] = arguments["description"]
                r = client.get("/v1/forms/", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_groups":
                params = {"page": arguments.get("page", 1)}
                r = client.get("/v1/groups/", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_positions":
                params = {"page": arguments.get("page", 1)}
                r = client.get("/v1/positions/", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_user":
                code = arguments["user_code"]
                r = client.get(f"/v1/users/{code}/")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_company":
                code = arguments["company_code"]
                r = client.get(f"/v1/company/{code}/")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_generic_master":
                code = arguments["generic_master_code"]
                params = {"page": arguments.get("page", 1)}
                r = client.get(f"/v1/generic_master/{code}/", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "validate_token":
                r = client.get("/test/")
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
