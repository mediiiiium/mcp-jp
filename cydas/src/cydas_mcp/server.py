import os

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("cydas-mcp")

# CTM 2.0 API。OpenAPI 3.0.0 が https://developer.cydas.com で公開されている。
# ステージング (https://api-stg.cydas.com) を叩きたい場合は CYDAS_BASE_URL で上書きする。
DEFAULT_BASE_URL = "https://people-api.cydas.com"

# pageSize の上限は API 側で 100。超えると 400 INVALID_PARAMETER が返る。
MAX_PAGE_SIZE = 100


def _client() -> httpx.Client:
    token = os.environ.get("CYDAS_ACCESS_TOKEN")
    if not token:
        raise ValueError("CYDAS_ACCESS_TOKEN が設定されていません")

    base_url = os.environ.get("CYDAS_BASE_URL") or DEFAULT_BASE_URL
    return httpx.Client(
        base_url=base_url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
        timeout=30,
    )


def _page_params(arguments: dict, *keys: str) -> dict:
    """page / pageSize と、指定されたキーのうち値があるものだけを query params にする。

    pageSize は API 上限（100）で頭打ちにする。上限超過は 400 になるだけで
    「たくさん取れる」わけではないため、ここで黙って抑える方が使い勝手が良い。
    """
    params: dict = {}
    if (page := arguments.get("page")) is not None:
        params["page"] = page
    if (size := arguments.get("pageSize")) is not None:
        params["pageSize"] = min(int(size), MAX_PAGE_SIZE)
    for k in keys:
        v = arguments.get(k)
        if v is not None and v != "":
            params[k] = v
    return params


# ページネーションを持つツールに共通で足す入力スキーマ
_PAGE_PROPS = {
    "page": {"type": "integer", "description": "ページ番号（省略時は1）"},
    "pageSize": {
        "type": "integer",
        "description": f"1ページの件数（省略時は100。API上限{MAX_PAGE_SIZE}を超える指定は{MAX_PAGE_SIZE}に丸める）",
    },
}


def _props(extra: dict | None = None, *, paging: bool = True) -> dict:
    props = dict(_PAGE_PROPS) if paging else {}
    props.update(extra or {})
    return props


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_tenant_context",
            description=(
                "接続先テナントの情報を取得する (GET /people/v1/tenant/context)。パラメータは無く、"
                "アクセストークンがどのテナントに紐づいているかを返す。CYDAS はテナントごとに"
                "発行トークンが異なるため、他のツールを呼ぶ前に「意図した環境（本番/ステージング、"
                "どの会社のテナント）に繋がっているか」を確かめる用途に使うのが基本。認証が通って"
                "いない場合はここで 401 が返るので、疎通確認としても最も軽い。書き込みは行わない。"
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="list_employees",
            description=(
                "社員情報をリストで取得する (GET /people/v1/individual/employees)。本コネクタの中心となる"
                "ツールで、社員番号・氏名・所属（position、現在の情報）などの基本情報が返る。"
                "embed にカテゴリキーをカンマ区切りで渡すと関連情報を同時に取得できる: "
                "personnelChanges（異動情報、異動日時点の情報）/ additionalPositions（兼務）/ "
                "addresses（自宅住所、最新1件）/ familyRegisters（戸籍）/ transportationExpenses（通勤費）/ "
                "salaries（給与）/ hourlyWageRevisions（時給改定）/ workingContacts（業務連絡先）/ "
                "preferredWorkAreas（希望する業務領域）。給与・住所・戸籍は機微情報なので、必要な"
                "カテゴリだけを embed に指定すること。enrollmentStatus で在籍区分を絞れる"
                "（10:在籍予定 / 20:在籍 / 30:出向 / 40:休職 / 50:再入社予定 / 90:退職、カンマ区切りで複数可）。"
                "fromUpdatedDate は「その日以降に異動・基本情報・embed対象が更新された社員」への絞り込みで、"
                "embed で取れる情報そのものの日付条件ではない点に注意。ページネーションは page / pageSize"
                "（既定100・上限100）。件数が多いと 504 が返ることがあり、その場合は 1,200 件を目安に"
                "期間や在籍区分で分割する。社員情報の登録・更新APIはCYDAS側に存在するが、本コネクタは"
                "読み取り専用のため未実装。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": _props({
                    "embed": {
                        "type": "string",
                        "description": (
                            "同時取得するカテゴリをカンマ区切りで指定（personnelChanges, additionalPositions, "
                            "addresses, familyRegisters, transportationExpenses, salaries, "
                            "hourlyWageRevisions, workingContacts, preferredWorkAreas）"
                        ),
                    },
                    "fromUpdatedDate": {
                        "type": "string",
                        "description": "この日付以降に更新のあった社員に絞り込む（YYYY-MM-DD）",
                    },
                    "enrollmentStatus": {
                        "type": "string",
                        "description": "在籍区分で絞り込む（10/20/30/40/50/90、カンマ区切りで複数可）",
                    },
                    "includesScheduled": {
                        "type": "boolean",
                        "description": "未来日で登録済みの情報（来月からの通勤費など）も含める（既定false）",
                    },
                }),
            },
        ),
        types.Tool(
            name="get_employee",
            description=(
                "社員1名の情報を取得する (GET /people/v1/individual/employees/{id})。既定は社員番号"
                "（employeeCode）での指定で、内部IDで引きたい場合は id_type に 'id' を渡す。"
                "embed で指定できる関連情報のカテゴリは list_employees と同じ（personnelChanges, "
                "additionalPositions, addresses, familyRegisters, transportationExpenses, salaries, "
                "hourlyWageRevisions, workingContacts, preferredWorkAreas）。1名だけを見る場合は"
                "こちらが読みやすいが、複数名を調べるなら list_employees を1回呼んで絞り込む方が"
                "リクエスト数を節約できる。該当社員が存在しない場合は 404 が返る。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "employee_code": {
                        "type": "string",
                        "description": "社員番号（id_type='id' のときは内部の社員ID）",
                    },
                    "id_type": {
                        "type": "string",
                        "enum": ["employeeCode", "id"],
                        "description": "employee_code の解釈（既定 employeeCode）",
                    },
                    "embed": {
                        "type": "string",
                        "description": "同時取得するカテゴリをカンマ区切りで指定（list_employees と同じキー）",
                    },
                },
                "required": ["employee_code"],
            },
        ),
        types.Tool(
            name="list_departments",
            description=(
                "部署情報をリストで取得する (GET /people/v1/organization/departments)。部署コード・部署名・"
                "階層関係などが返る。返るのはフラットなリストなので、階層ツリーが必要な場合は親子関係を"
                "辿って自分で組み立てる。「いつ時点の組織か」を指定するパラメータはこのエンドポイントには"
                "無く、現在有効な部署が返る。過去・未来の組織を見たい場合は list_department_histories"
                "（部署単位の履歴）または list_reorganizations（組織改編単位）を使う。部署マスタの種別"
                "（役職・職種などの選択肢定義）は list_organization_master_data 側。部署の登録・更新APIは"
                "CYDAS側に存在するが、本コネクタは読み取り専用のため未実装。書き込みは行わない。"
            ),
            inputSchema={"type": "object", "properties": _props()},
        ),
        types.Tool(
            name="list_department_managers",
            description=(
                "所属長（部署の責任者）をリストで取得する (GET /people/v1/organization/managers)。"
                "どの部署に誰が所属長として設定されているかの対応を返す。list_departments には"
                "所属長の情報が含まれないため、部署と責任者を突き合わせたい場合は両方を取得して"
                "部署コードで結合する。承認経路や誰にエスカレーションするかを調べる用途で使う。"
                "書き込みは行わない。"
            ),
            inputSchema={"type": "object", "properties": _props()},
        ),
        types.Tool(
            name="list_department_histories",
            description=(
                "部署履歴をリストで取得する (GET /people/v1/organization/department-histories)。"
                "target_effective_date にある日付を渡すと、その時点で有効だった部署情報が返るため、"
                "「去年の4月時点の組織はどうだったか」を調べられる。list_departments が現在の組織"
                "しか返さないのに対し、こちらは時点指定ができるのが違い。組織改編そのものの単位"
                "（いつどの改編が実施されたか）で見たい場合は list_reorganizations を使う。"
                "書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": _props({
                    "target_effective_date": {
                        "type": "string",
                        "description": "この日付時点で有効だった部署情報に絞り込む（YYYY-MM-DD）",
                    },
                }),
            },
        ),
        types.Tool(
            name="list_reorganizations",
            description=(
                "組織改編をリストで取得する (GET /people/v1/organization/reorganizations)。"
                "current を true にすると現在有効な改編1件のみ (GET .../reorganizations/current) を返す。"
                "改編の構造（その改編で部署がどう変わるか）まで見たい場合は、ここで得た改編IDを"
                "get_reorganization_structures に渡す。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": _props({
                    "current": {
                        "type": "boolean",
                        "description": "現在有効な組織改編1件のみを取得する",
                    },
                }),
            },
        ),
        types.Tool(
            name="get_reorganization_structures",
            description=(
                "指定した組織改編の構造情報を取得する "
                "(GET /people/v1/organization/reorganizations/{id}/structures)。"
                "その改編で組織がどういう形になるか（部署の新設・統廃合・親子関係など）が返る。"
                "reorganization_id は list_reorganizations で確認する。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": _props({
                    "reorganization_id": {"type": "string", "description": "組織改編ID"},
                }),
                "required": ["reorganization_id"],
            },
        ),
        types.Tool(
            name="list_organization_master_data",
            description=(
                "部署まわりのマスタデータをリストで取得する (GET /people/v1/organization/master-data)。"
                "types に種別をカンマ区切りで指定して絞り込む（省略時は全種別）。部署情報や社員情報の"
                "レスポンスに現れるコード値を、人間可読な名称へ変換する対応表として使う。"
                "人事異動側のマスタ（発令区分など）は list_personnel_change_master_data と別リソース。"
                "マスタの洗い替え登録APIはCYDAS側に存在するが、本コネクタは読み取り専用のため未実装。"
                "書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": _props({
                    "types": {
                        "type": "string",
                        "description": "マスタデータの種別（カンマ区切りで複数指定可、省略時は全種別）",
                    },
                }),
            },
        ),
        types.Tool(
            name="list_personnel_changes",
            description=(
                "異動情報（発令）をリストで取得する (GET /people/v2/personnel-change/announcements)。"
                "入社・配属・異動・出向・休職・退職・再入社といった発令の履歴が返る。v1 も存在するが"
                "本ツールは v2 を使う。start_date / end_date で発令日の期間を絞れる（end_date を指定する"
                "ときは start_date も必須）。employee_code はカンマ区切りで最大100名まで同時指定できる。"
                "「現在の所属」は list_employees の position で取れるので、こちらは異動の履歴・時系列を"
                "追いたいときに使う。異動情報の登録APIはCYDAS側に存在するが、本コネクタは読み取り専用の"
                "ため未実装。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": _props({
                    "start_date": {"type": "string", "description": "この日付以降の異動情報に絞り込む（YYYY-MM-DD）"},
                    "end_date": {
                        "type": "string",
                        "description": "期間の終わり（YYYY-MM-DD。指定するときは start_date も必要）",
                    },
                    "employee_code": {
                        "type": "string",
                        "description": "社員番号で絞り込む（カンマ区切りで最大100名）",
                    },
                }),
            },
        ),
        types.Tool(
            name="list_personnel_change_master_data",
            description=(
                "人事異動まわりのマスタデータをリストで取得する "
                "(GET /people/v1/personnel-change/master-data)。types に種別をカンマ区切りで指定して"
                "絞り込む（省略時は全種別）。list_personnel_changes が返す発令情報のコード値を名称へ"
                "変換する対応表として使う。部署まわりのマスタは list_organization_master_data と別リソース。"
                "書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": _props({
                    "types": {
                        "type": "string",
                        "description": "マスタデータの種別（カンマ区切りで複数指定可、省略時は全種別）",
                    },
                }),
            },
        ),
        types.Tool(
            name="list_personal_profile_definitions",
            description=(
                "パーソナルプロファイルの項目定義を取得する (GET /people/v1/personal-profile/definitions)。"
                "パーソナルプロファイルはテナントごとに項目をカスタム定義する仕組みなので、"
                "list_personal_profiles を呼ぶ前にこのツールで「どんなカテゴリ（categoryId）と項目が"
                "あるか」を確認するのが基本の流れ。list_personal_profiles は categoryId が必須で、"
                "その値はここでしか分からない。選択式項目の選択肢の実体は "
                "list_personal_profile_master_data 側にある。書き込みは行わない。"
            ),
            inputSchema={"type": "object", "properties": _props()},
        ),
        types.Tool(
            name="list_personal_profiles",
            description=(
                "パーソナルプロファイル（テナント独自に定義された社員情報）をリストで取得する "
                "(GET /people/v1/personal-profile/profiles)。category_id が必須で、値は "
                "list_personal_profile_definitions で確認する。employee_code はカンマ区切りで最大100名まで"
                "同時指定できる。from_updated_date で更新日以降に絞り込める。OpenAPI 上の "
                "filterEffectiveDate（日付項目に対する eq / le / ge での期間絞り込み）はオブジェクト型の"
                "パラメータで表現が複雑なため、本ツールでは未対応。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": _props({
                    "category_id": {
                        "type": "string",
                        "description": "カテゴリID（list_personal_profile_definitions で確認）",
                    },
                    "employee_code": {
                        "type": "string",
                        "description": "社員番号で絞り込む（カンマ区切りで最大100名）",
                    },
                    "from_updated_date": {
                        "type": "string",
                        "description": "この日付以降に更新された情報に絞り込む（YYYY-MM-DD）",
                    },
                }),
                "required": ["category_id"],
            },
        ),
        types.Tool(
            name="list_personal_profile_master_data",
            description=(
                "パーソナルプロファイルのマスタデータをリストで取得する "
                "(GET /people/v1/personal-profile/master-data)。プルダウンなど選択式項目の選択肢の実体で、"
                "list_personal_profiles が返すコード値を名称へ変換する対応表として使う。"
                "item_ids でカンマ区切りに項目を絞れる（項目IDは list_personal_profile_definitions で確認）。"
                "書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": _props({
                    "item_ids": {
                        "type": "string",
                        "description": "項目IDで絞り込む（カンマ区切りで複数指定可）",
                    },
                }),
            },
        ),
        types.Tool(
            name="list_projects",
            description=(
                "プロジェクト情報をリストで取得する (GET /people/v1/project/projects)。"
                "プロジェクトコード・名称・期間などが返る。個々のプロジェクトのアサイン状況は "
                "list_project_members、上位のくくりであるプログラム単位の情報は list_programs で取得する。"
                "プロジェクトの登録・更新APIはCYDAS側に存在するが、本コネクタは読み取り専用のため未実装。"
                "書き込みは行わない。"
            ),
            inputSchema={"type": "object", "properties": _props()},
        ),
        types.Tool(
            name="list_project_members",
            description=(
                "指定プロジェクトのアサイン状況を取得する "
                "(GET /people/v1/project/projects/{projectCode}/employees)。誰がそのプロジェクトに"
                "アサインされているかが返る。project_code は list_projects で確認する。"
                "プロジェクトマネージャー・評価者はアサインとは別リソース "
                "(.../managers, .../reviewers) で、本コネクタでは未実装。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_code": {"type": "string", "description": "プロジェクトコード（list_projects で確認）"},
                },
                "required": ["project_code"],
            },
        ),
        types.Tool(
            name="list_programs",
            description=(
                "プログラム情報をリストで取得する (GET /people/v1/project/programs)。"
                "プログラムは複数プロジェクトを束ねる上位の概念。個々のプロジェクトは list_projects で"
                "取得する。書き込みは行わない。"
            ),
            inputSchema={"type": "object", "properties": _props()},
        ),
        types.Tool(
            name="list_skillcheck_sheets",
            description=(
                "スキルチェックのシート情報をリストで取得する (GET /people/v1/skillcheck/sheets)。"
                "各シートの id は get_skillcheck_answers の入力になる。設問項目そのものの詳細は"
                "別エンドポイント (GET /people/v1/skillcheck/sheets/{id}) で、本コネクタでは未実装。"
                "書き込みは行わない。"
            ),
            inputSchema={"type": "object", "properties": _props()},
        ),
        types.Tool(
            name="get_skillcheck_answers",
            description=(
                "指定シートのスキルチェック回答結果を取得する "
                "(GET /people/v1/skillcheck/sheets/{id}/answers)。sheet_id は list_skillcheck_sheets で"
                "確認する。start_approved_date / end_approved_date で承認日の期間を絞れる。"
                "集計済みのサマリー (.../summaries) やレベルレンジ設定 (.../range-settings) は"
                "別エンドポイントで、本コネクタでは未実装。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": _props({
                    "sheet_id": {"type": "string", "description": "シートID（list_skillcheck_sheets で確認）"},
                    "start_approved_date": {"type": "string", "description": "承認日の開始（YYYY-MM-DD）"},
                    "end_approved_date": {"type": "string", "description": "承認日の終了（YYYY-MM-DD）"},
                }),
                "required": ["sheet_id"],
            },
        ),
        types.Tool(
            name="list_career_plan_forms",
            description=(
                "キャリアプランのフォームをリストで取得する (GET /people/v1/career-plan/forms)。"
                "list_career_plan_answers は form_id が必須なので、まずこのツールでフォームIDを確認する。"
                "フォーム内の項目定義は別エンドポイント (GET /people/v1/career-plan/forms/{id}/items) で、"
                "本コネクタでは未実装。書き込みは行わない。"
            ),
            inputSchema={"type": "object", "properties": _props()},
        ),
        types.Tool(
            name="list_career_plan_answers",
            description=(
                "キャリアプランの回答内容をリストで取得する (GET /people/v1/career-plan/answers)。"
                "form_id が必須で、値は list_career_plan_forms で確認する。target_date を指定すると"
                "その日付時点で最新の回答内容が返る（省略時は現在時点）。employee_code / employee_id で"
                "特定社員に絞れる。本人の異動希望やキャリア志向が入る機微な情報なので、必要な範囲だけ"
                "取得すること。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": _props({
                    "form_id": {"type": "string", "description": "フォームID（list_career_plan_forms で確認）"},
                    "target_date": {
                        "type": "string",
                        "description": "この日付時点で最新の回答を取得する（YYYY-MM-DD、省略時は現在）",
                    },
                    "employee_code": {"type": "string", "description": "社員番号で絞り込む"},
                }),
                "required": ["form_id"],
            },
        ),
        types.Tool(
            name="list_job_descriptions",
            description=(
                "ジョブディスクリプションを一覧で取得する (GET /people/v1/job/job-descriptions)。"
                "職務要件の定義が返る。from_updated_date で更新日以降に絞り込める。"
                "特定コードの履歴つき詳細 (.../{code}/histories/{startDate}) や、ジョブファミリー・"
                "ジョブレベルのマスタは別エンドポイントで、本コネクタでは未実装。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": _props({
                    "from_updated_date": {
                        "type": "string",
                        "description": "この日付以降に更新されたものに絞り込む（YYYY-MM-DD）",
                    },
                }),
            },
        ),
        types.Tool(
            name="list_personnel_applications",
            description=(
                "各種人事申請をリストで取得する (GET /people/v1/personnel-application/requests)。"
                "status で申請ステータスを絞れる（inProgress: 申請中 / approved: 承認済 / remand: 差戻し）。"
                "申請日 (start_application_date / end_application_date)・承認日 "
                "(start_approved_date / end_approved_date)・申請者 (applicant_employee_code)・"
                "フォーム (form_id、カンマ区切りで複数可) で絞り込める。申請フォームの一覧・詳細は"
                "別エンドポイント (GET /people/v1/personnel-application/forms) で、本コネクタでは未実装。"
                "承認・差戻しなどの操作は行わない（読み取り専用）。"
            ),
            inputSchema={
                "type": "object",
                "properties": _props({
                    "status": {
                        "type": "string",
                        "enum": ["inProgress", "approved", "remand"],
                        "description": "申請ステータス（inProgress:申請中 / approved:承認済 / remand:差戻し）",
                    },
                    "start_application_date": {"type": "string", "description": "申請日の開始（YYYY-MM-DD）"},
                    "end_application_date": {"type": "string", "description": "申請日の終了（YYYY-MM-DD）"},
                    "applicant_employee_code": {"type": "string", "description": "申請者の社員番号"},
                    "form_id": {"type": "string", "description": "申請フォームID（カンマ区切りで複数可）"},
                }),
            },
        ),
        types.Tool(
            name="list_monthly_attendance",
            description=(
                "月別勤怠情報をリストで取得する (GET /people/v1/attendance/monthly-workings)。"
                "date で対象月、department_code で部署を絞り込む。日単位の打刻レベルで見たい場合は"
                "list_daily_attendance を使う（件数が跳ね上がるので期間は短く区切ること）。"
                "勤怠情報の登録APIはCYDAS側に存在するが、本コネクタは読み取り専用のため未実装。"
                "書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": _props({
                    "date": {"type": "string", "description": "対象月（YYYY-MM-DD）"},
                    "department_code": {"type": "string", "description": "部署コードで絞り込む"},
                }),
            },
        ),
        types.Tool(
            name="list_daily_attendance",
            description=(
                "日別勤怠情報をリストで取得する (GET /people/v1/attendance/daily-workings)。"
                "start_date / end_date で期間、department_code で部署を絞り込む。日×人数のオーダーで"
                "件数が増え、多すぎるとAPI側が 504 を返すため、期間は短く（目安として1回1,200件以内に"
                "収まるよう）区切って呼ぶこと。月次の集計で足りる場合は list_monthly_attendance の方が軽い。"
                "書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": _props({
                    "start_date": {"type": "string", "description": "期間の開始（YYYY-MM-DD）"},
                    "end_date": {"type": "string", "description": "期間の終了（YYYY-MM-DD）"},
                    "department_code": {"type": "string", "description": "部署コードで絞り込む"},
                }),
            },
        ),
        types.Tool(
            name="list_accounts",
            description=(
                "アカウント情報をリストで取得する (GET /people/v1/user/idp-users)。ここでいうアカウントは"
                "CYDAS にログインする認証ユーザー（IdP ユーザー）であり、list_employees が返す"
                "「従業員としての社員」とは別概念。休眠アカウントの棚卸しや、社員とログインアカウントの"
                "対応確認に使う。アカウントの登録APIはCYDAS側に存在するが、本コネクタは読み取り専用の"
                "ため未実装。書き込みは行わない。"
            ),
            inputSchema={"type": "object", "properties": _props()},
        ),
        types.Tool(
            name="list_access_policies",
            description=(
                "権限設定をリストで取得する (GET /people/v1/access-control/policies)。"
                "status で 'active'（有効）/ 'deactive'（無効）に絞れる。誰がその権限を適用されているかは"
                "別エンドポイント (.../policies/{policyId}/actors) で、本コネクタでは未実装。"
                "「誰がどこまで見られるか」の権限棚卸し・監査に使う。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": _props({
                    "status": {
                        "type": "string",
                        "enum": ["active", "deactive"],
                        "description": "ステータス（active:有効 / deactive:無効）",
                    },
                }),
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "get_tenant_context":
                r = client.get("/people/v1/tenant/context")

            elif name == "list_employees":
                r = client.get(
                    "/people/v1/individual/employees",
                    params=_page_params(arguments, "embed", "fromUpdatedDate",
                                        "enrollmentStatus", "includesScheduled"),
                )

            elif name == "get_employee":
                params = {"idType": arguments.get("id_type", "employeeCode")}
                if embed := arguments.get("embed"):
                    params["embed"] = embed
                r = client.get(
                    f"/people/v1/individual/employees/{arguments['employee_code']}",
                    params=params,
                )

            elif name == "list_departments":
                r = client.get("/people/v1/organization/departments",
                               params=_page_params(arguments))

            elif name == "list_department_managers":
                r = client.get("/people/v1/organization/managers",
                               params=_page_params(arguments))

            elif name == "list_department_histories":
                params = _page_params(arguments)
                if d := arguments.get("target_effective_date"):
                    params["targetEffectiveDate"] = d
                r = client.get("/people/v1/organization/department-histories", params=params)

            elif name == "list_reorganizations":
                if arguments.get("current"):
                    # 現在有効な1件は専用エンドポイント。ページネーションは無い。
                    r = client.get("/people/v1/organization/reorganizations/current")
                else:
                    r = client.get("/people/v1/organization/reorganizations",
                                   params=_page_params(arguments))

            elif name == "get_reorganization_structures":
                r = client.get(
                    f"/people/v1/organization/reorganizations/{arguments['reorganization_id']}/structures",
                    params=_page_params(arguments),
                )

            elif name == "list_organization_master_data":
                r = client.get("/people/v1/organization/master-data",
                               params=_page_params(arguments, "types"))

            elif name == "list_personnel_changes":
                params = _page_params(arguments)
                for src, dst in (("start_date", "startDate"), ("end_date", "endDate"),
                                 ("employee_code", "employeeCode")):
                    if v := arguments.get(src):
                        params[dst] = v
                r = client.get("/people/v2/personnel-change/announcements", params=params)

            elif name == "list_personnel_change_master_data":
                r = client.get("/people/v1/personnel-change/master-data",
                               params=_page_params(arguments, "types"))

            elif name == "list_personal_profile_definitions":
                r = client.get("/people/v1/personal-profile/definitions",
                               params=_page_params(arguments))

            elif name == "list_personal_profiles":
                params = _page_params(arguments)
                params["categoryId"] = arguments["category_id"]
                for src, dst in (("employee_code", "employeeCode"),
                                 ("from_updated_date", "fromUpdatedDate")):
                    if v := arguments.get(src):
                        params[dst] = v
                r = client.get("/people/v1/personal-profile/profiles", params=params)

            elif name == "list_personal_profile_master_data":
                params = _page_params(arguments)
                if v := arguments.get("item_ids"):
                    params["itemIds"] = v
                r = client.get("/people/v1/personal-profile/master-data", params=params)

            elif name == "list_projects":
                r = client.get("/people/v1/project/projects", params=_page_params(arguments))

            elif name == "list_project_members":
                r = client.get(
                    f"/people/v1/project/projects/{arguments['project_code']}/employees"
                )

            elif name == "list_programs":
                r = client.get("/people/v1/project/programs", params=_page_params(arguments))

            elif name == "list_skillcheck_sheets":
                r = client.get("/people/v1/skillcheck/sheets", params=_page_params(arguments))

            elif name == "get_skillcheck_answers":
                params = _page_params(arguments)
                for src, dst in (("start_approved_date", "startApprovedDate"),
                                 ("end_approved_date", "endApprovedDate")):
                    if v := arguments.get(src):
                        params[dst] = v
                r = client.get(
                    f"/people/v1/skillcheck/sheets/{arguments['sheet_id']}/answers",
                    params=params,
                )

            elif name == "list_career_plan_forms":
                r = client.get("/people/v1/career-plan/forms", params=_page_params(arguments))

            elif name == "list_career_plan_answers":
                params = _page_params(arguments)
                params["formId"] = arguments["form_id"]
                for src, dst in (("target_date", "targetDate"),
                                 ("employee_code", "employeeCode")):
                    if v := arguments.get(src):
                        params[dst] = v
                r = client.get("/people/v1/career-plan/answers", params=params)

            elif name == "list_job_descriptions":
                params = _page_params(arguments)
                if v := arguments.get("from_updated_date"):
                    params["fromUpdatedDate"] = v
                r = client.get("/people/v1/job/job-descriptions", params=params)

            elif name == "list_personnel_applications":
                params = _page_params(arguments, "status")
                for src, dst in (("start_application_date", "startApplicationDate"),
                                 ("end_application_date", "endApplicationDate"),
                                 ("applicant_employee_code", "applicantEmployeeCode"),
                                 ("form_id", "formId")):
                    if v := arguments.get(src):
                        params[dst] = v
                r = client.get("/people/v1/personnel-application/requests", params=params)

            elif name == "list_monthly_attendance":
                params = _page_params(arguments, "date")
                if v := arguments.get("department_code"):
                    params["departmentCode"] = v
                r = client.get("/people/v1/attendance/monthly-workings", params=params)

            elif name == "list_daily_attendance":
                params = _page_params(arguments)
                for src, dst in (("start_date", "startDate"), ("end_date", "endDate"),
                                 ("department_code", "departmentCode")):
                    if v := arguments.get(src):
                        params[dst] = v
                r = client.get("/people/v1/attendance/daily-workings", params=params)

            elif name == "list_accounts":
                r = client.get("/people/v1/user/idp-users", params=_page_params(arguments))

            elif name == "list_access_policies":
                r = client.get("/people/v1/access-control/policies",
                               params=_page_params(arguments, "status"))

            else:
                raise ValueError(f"未知のツール: {name}")

            r.raise_for_status()
            return format_response(r.json())
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
