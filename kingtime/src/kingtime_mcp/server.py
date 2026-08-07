import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

BASE_URL = "https://api.kingtime.jp/v1.0"

app = Server("kingtime-mcp")


def get_client() -> httpx.Client:
    token = os.environ.get("KINGTIME_ACCESS_TOKEN")
    if not token:
        raise ValueError("KINGTIME_ACCESS_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )


# 毎日この時間帯（JST）は、打刻登録系API（record_time）以外のほとんどのAPIが利用できない
# （KING OF TIME WebAPI仕様「利用禁止時間帯」より: 8:30〜10:00 / 17:30〜18:30）。
_BLACKOUT_NOTE = (
    "毎日 8:30〜10:00 と 17:30〜18:30（JST）はKING OF TIME側の制限によりこのAPIが利用できない"
    "（打刻登録APIのみこの時間帯でも例外的に利用可能）。"
)


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_employees",
            description=(
                "従業員マスタの一覧を取得する。レスポンスに含まれる従業員コード（code、人事異動等で変わりうる社員番号）"
                "とは別に、record_time など他のツールで従業員を指定する際に必須となる不変の識別子 key（従業員識別キー）"
                "もここで確認できる。date を指定するとその時点（過去は最大3年前、未来は最大1年後まで）の在籍状況を返す"
                "（省略時は当日時点）。division で所属コードによる絞り込みが可能。include_resigner=true で退職済み"
                "従業員も含める。limit/offset のようなページネーションは提供されておらず、条件に合致する全従業員を"
                "1回のレスポンスで返す。書き込みは行わない（従業員の新規登録・更新・削除APIはKING OF TIME側に存在"
                "するが、本コネクタには未実装）。" + _BLACKOUT_NOTE
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "在籍状況の基準日 YYYY-MM-DD（省略時は当日。過去は最大3年前、未来は最大1年後まで指定可）",
                    },
                    "division": {"type": "string", "description": "所属コードで絞り込む（省略時は全所属が対象）"},
                    "include_resigner": {
                        "type": "boolean",
                        "description": "true にすると基準日時点で退職済みの従業員も含める（既定 false）",
                    },
                    "additional_fields": {
                        "type": "string",
                        "description": (
                            "レスポンスに追加するプロパティをカンマ区切りで指定"
                            "（例: emailAddresses,hiredDate,birthDate,resignationDate,"
                            "lastNamePhonetics,firstNamePhonetics,allDayRegardingWorkInMinute）"
                        ),
                    },
                },
            },
        ),
        types.Tool(
            name="get_employee",
            description=(
                "従業員コード（code）を指定して従業員1名の情報を取得する。get_employees の絞り込み版で、"
                "対象の従業員コードが既にわかっている場合に全件取得を避けられる。employee_code には従業員コード"
                "（code。人事異動等で変わりうる社員番号）を指定する（record_time 等が要求する不変の識別子 key ではない"
                "点に注意）。date を指定するとその時点（過去は最大3年前、未来は最大1年後まで）の情報を返す（省略時は"
                "当日時点）。include_resigner=true で退職済みでも取得可能にする。書き込みは行わない。" + _BLACKOUT_NOTE
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "employee_code": {"type": "string", "description": "従業員コード（get_employees のレスポンスの code）"},
                    "date": {
                        "type": "string",
                        "description": "基準日 YYYY-MM-DD（省略時は当日。過去は最大3年前、未来は最大1年後まで指定可）",
                    },
                    "include_resigner": {
                        "type": "boolean",
                        "description": "true にすると基準日時点で退職済みでも取得できるようにする（既定 false）",
                    },
                    "additional_fields": {
                        "type": "string",
                        "description": "get_employees と同様、レスポンスに追加するプロパティをカンマ区切りで指定",
                    },
                },
                "required": ["employee_code"],
            },
        ),
        types.Tool(
            name="get_divisions",
            description=(
                "所属（division）データの一覧を取得する。code（所属コード）と name（所属名）、dayBorderTime"
                "（日またぎの締め時刻）を返す。get_employees / get_daily_workings / get_monthly_workings / "
                "get_daily_schedules / get_timerecords の division 引数に渡せる有効な所属コードを事前に確認するのに使う"
                "（これらのAPIは従業員単位の絞り込みができず division 絞り込みが前提のため、まず本ツールで所属コード一覧を"
                "把握しておくと組み立てやすい）。パラメータは無く、常に全所属を返す。書き込みは行わない。" + _BLACKOUT_NOTE
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="get_working_types",
            description=(
                "雇用区分（正社員・契約社員・アルバイト等）のマスタデータ一覧を取得する。code（雇用区分コード）と "
                "name（雇用区分名）を返す。get_employees のレスポンスに含まれる typeCode の意味を確認するのに使う。"
                "パラメータは無く、常に全雇用区分を返す。書き込みは行わない。" + _BLACKOUT_NOTE
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="get_employee_groups",
            description=(
                "従業員グループのマスタデータ一覧を取得する。code（グループコード）と name（グループ名）、"
                "additional_fields=category 指定時はカテゴリ情報も返す。対象企業が従業員グループ機能を利用できない場合"
                "はデータを取得できない（空またはエラーになりうる）。書き込みは行わない。" + _BLACKOUT_NOTE
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "additional_fields": {
                        "type": "string",
                        "description": "レスポンスに追加するプロパティをカンマ区切りで指定（例: category）",
                    },
                },
            },
        ),
        types.Tool(
            name="get_timerecords",
            description=(
                "指定期間の実際の打刻イベント一覧（出勤・退勤・休憩開始/終了・外出・外出から戻りの各打刻時刻そのもの）を"
                "取得する。get_daily_workings が返す分単位の集計値とは異なり、個々の打刻時刻（time）・打刻種別（code/name）"
                "・打刻時の所属（divisionCode/divisionName）・位置情報（latitude/longitude）を日付ごとにグループ化して"
                "返す。employee_keys（従業員識別キー。カンマ区切りで複数指定可）と division（所属コード）は同時指定不可"
                "（どちらか一方のみ使用可能。両方省略した場合の挙動は未確認）。ondivision は division 指定時のみ有効で、"
                "true=所属基準、false=出勤先基準の打刻データ（既定 true）。start_date/end_date は省略可能（省略時は"
                "当日が対象）だが、指定する場合は両方同時に指定する必要があり、期間は最大62日まで。additional_fields="
                "currentDateEmployee を指定するとレスポンスに従業員名・従業員コードが展開される。書き込みは行わない。"
                + _BLACKOUT_NOTE
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "employee_keys": {
                        "type": "string",
                        "description": "従業員識別キーをカンマ区切りで指定（division と同時指定不可）",
                    },
                    "division": {
                        "type": "string",
                        "description": "所属コードで絞り込む（employee_keys と同時指定不可）",
                    },
                    "ondivision": {
                        "type": "boolean",
                        "description": "division 指定時のみ有効。true=所属基準、false=出勤先基準の打刻データ（既定 true）",
                    },
                    "start_date": {"type": "string", "description": "開始日 YYYY-MM-DD（省略可。指定する場合は end_date と同時指定必須。過去は最大3年前まで）"},
                    "end_date": {"type": "string", "description": "終了日 YYYY-MM-DD（start_date との期間は最大62日、未来は最大1年後まで）"},
                    "additional_fields": {
                        "type": "string",
                        "description": "レスポンスに追加するプロパティ（例: currentDateEmployee で従業員名・コード等を展開）",
                    },
                },
            },
        ),
        types.Tool(
            name="get_daily_workings",
            description=(
                "指定期間の日別勤怠集計データ（従業員ごとの所定時間・残業時間・深夜時間・遅刻/早退時間・休憩時間などの"
                "分単位の集計値）を取得する。実際の出勤・退勤の打刻時刻そのもの（timeRecord）はこのAPIのレスポンスには"
                "含まれない点に注意（打刻時刻一覧を取得するAPIはKING OF TIME側に daily-workings/timerecord として"
                "存在するが、本コネクタには未実装）。start_date/end_date は同時指定が必須で、指定できる期間は最大62日"
                "まで（開始日は過去最大3年前、終了日は未来最大1年後まで）。従業員単位の絞り込みパラメータはAPI側に"
                "存在しないため、division（所属コード）で絞り込んだ上でレスポンス内の employeeKey で判別すること。"
                "division 指定時のみ ondivision で「所属基準」か「出勤先基準」かを選べる。additional_fields="
                "currentDateEmployee を指定するとレスポンスに従業員名・従業員コードが展開され、employeeKey と"
                "ひもづけやすくなる。書き込みは行わない。" + _BLACKOUT_NOTE
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "開始日 YYYY-MM-DD（過去は最大3年前まで）"},
                    "end_date": {
                        "type": "string",
                        "description": "終了日 YYYY-MM-DD（start_date との期間は最大62日、未来は最大1年後まで）",
                    },
                    "division": {"type": "string", "description": "所属コードで絞り込む（省略時は全所属が対象）"},
                    "ondivision": {
                        "type": "boolean",
                        "description": "division 指定時のみ有効。true=所属基準、false=出勤先基準の勤怠データ（既定 true）",
                    },
                    "additional_fields": {
                        "type": "string",
                        "description": "レスポンスに追加するプロパティ（例: currentDateEmployee で従業員名・コード等を展開）",
                    },
                },
                "required": ["start_date", "end_date"],
            },
        ),
        types.Tool(
            name="get_monthly_workings",
            description=(
                "指定月の月別勤怠集計データ（総労働時間・残業時間・深夜労働・遅刻/早退回数・取得休暇など）を取得する。"
                "対象年月はAPI仕様上URLパスの一部として指定される（過去は最大3年前、未来は最大1年後の月まで指定可）。"
                "従業員単位の絞り込みパラメータはAPI側に存在しないため、division（所属コード）で絞り込んだ上で"
                "レスポンス内の employeeKey で判別すること。additional_fields=currentDateEmployee を指定すると"
                "レスポンスに従業員名・従業員コードが展開される。書き込みは行わない。" + _BLACKOUT_NOTE
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "year_month": {
                        "type": "string",
                        "description": "対象年月 YYYY-MM（過去は最大3年前、未来は最大1年後の月まで指定可）",
                    },
                    "division": {"type": "string", "description": "所属コードで絞り込む（省略時は全所属が対象）"},
                    "additional_fields": {
                        "type": "string",
                        "description": "レスポンスに追加するプロパティ（例: currentDateEmployee で従業員名・コード等を展開）",
                    },
                },
                "required": ["year_month"],
            },
        ),
        types.Tool(
            name="get_daily_schedules",
            description=(
                "指定期間のシフト・スケジュール（出勤予定時刻・退勤予定時刻・休憩予定・休暇予定など）を取得する。"
                "start_date/end_date は同時指定が必須で、指定できる期間は最大62日まで。従業員単位の絞り込みパラメータ"
                "はAPI側に存在しないため、division（所属コード）で絞り込んだ上でレスポンス内の employeeKey で判別"
                "すること。division 指定時のみ ondivision で「所属基準」か「出勤先基準」かを選べる。KING OF TIME側"
                "にはスケジュールの登録・更新（PUT /daily-schedules/{employeeKey}/{date}）および削除（DELETE 同"
                "エンドポイント）のAPIも存在するが、本コネクタでは取得のみ実装しており登録・更新・削除は未実装のため、"
                "シフトの変更は管理画面から行う必要がある。書き込みは行わない。" + _BLACKOUT_NOTE
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "開始日 YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "終了日 YYYY-MM-DD（start_date との期間は最大62日）"},
                    "division": {"type": "string", "description": "所属コードで絞り込む（省略時は全所属が対象）"},
                    "ondivision": {
                        "type": "boolean",
                        "description": "division 指定時のみ有効。true=所属基準、false=出勤先基準のスケジュール（既定 true）",
                    },
                    "additional_fields": {
                        "type": "string",
                        "description": "レスポンスに追加するプロパティ（例: currentDateEmployee で従業員名・コード等を展開）",
                    },
                },
                "required": ["start_date", "end_date"],
            },
        ),
        types.Tool(
            name="record_time",
            description=(
                "従業員1名の打刻を1件登録する。呼び出すたびに新しい打刻イベントが1件追加される操作であり、同じ内容で"
                "複数回呼んでも1回にまとまることはない（べき等ではない）ため、二重打刻に注意すること。employee_key には"
                "従業員コードではなく、get_employees のレスポンスに含まれる不変の識別子 key（従業員識別キー）を指定する。"
                "time はタイムゾーン付きのISO 8601形式で指定する（例: 2026-07-02T09:00:00+09:00）。code（打刻種別: "
                "1=出勤 / 2=退勤 / 3=休憩開始 / 4=休憩終了 / 7=外出 / 8=外出から戻り）を省略すると、KING OF TIME側が"
                "直前の打刻等の文脈から自動判定する。is_omitted_working_day=true の場合、勤務日への自動割当を許容する"
                "代わりに code の指定が必須になる。false または省略時（既定）は date の指定が必須になる代わりに code"
                "は省略できる。登録可能な打刻日時は、対象勤務日の翌日23時59分59秒まで（勤務日省略時は打刻登録日の"
                "翌日23時59分59秒まで）という制限がある。この打刻登録APIは、他の取得系APIが利用できない"
                "8:30〜10:00・17:30〜18:30（JST）の時間帯でも例外的に利用できる。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "employee_key": {
                        "type": "string",
                        "description": "従業員識別キー（get_employees のレスポンスの key。従業員コードではない）",
                    },
                    "time": {
                        "type": "string",
                        "description": "打刻日時（タイムゾーン付きISO 8601形式。例: 2026-07-02T09:00:00+09:00）",
                    },
                    "date": {
                        "type": "string",
                        "description": (
                            "打刻を紐づける勤務日 YYYY-MM-DD。is_omitted_working_day が false または省略の場合は必須"
                            "（省略すると time の日付等からKING OF TIME側が勤務日を自動判定する）"
                        ),
                    },
                    "code": {
                        "type": "string",
                        "description": (
                            "打刻種別コード（1=出勤 / 2=退勤 / 3=休憩開始 / 4=休憩終了 / 7=外出 / 8=外出から戻り）。"
                            "is_omitted_working_day=true の場合は必須。省略時はKING OF TIME側が自動判定する"
                        ),
                        "enum": ["1", "2", "3", "4", "7", "8"],
                    },
                    "is_omitted_working_day": {
                        "type": "boolean",
                        "description": (
                            "true=勤務日への自動割当を許容する（この場合 code が必須）。"
                            "false（既定）=date の指定が必須になる代わりに code は省略可"
                        ),
                    },
                    "division_code": {
                        "type": "string",
                        "description": "打刻先の所属コード（省略時は従業員本来の所属コードが使われる）",
                    },
                    "latitude": {"type": "number", "description": "打刻位置の緯度（任意）"},
                    "longitude": {"type": "number", "description": "打刻位置の経度（任意）"},
                },
                "required": ["employee_key", "time"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        return _dispatch(name, arguments)
    except Exception as exc:  # noqa: BLE001 — MCP では例外を意味のある文字列で返す
        return error_response(exc)


def _dispatch(name: str, arguments: dict) -> list[types.TextContent]:
    with get_client() as client:
        if name == "get_employees":
            params = {}
            if date := arguments.get("date"):
                params["date"] = date
            if division := arguments.get("division"):
                params["division"] = division
            if "include_resigner" in arguments:
                params["includeResigner"] = arguments["include_resigner"]
            if additional_fields := arguments.get("additional_fields"):
                params["additionalFields"] = additional_fields
            r = client.get("/employees", params=params)

        elif name == "get_employee":
            employee_code = arguments["employee_code"]
            params = {}
            if date := arguments.get("date"):
                params["date"] = date
            if "include_resigner" in arguments:
                params["includeResigner"] = arguments["include_resigner"]
            if additional_fields := arguments.get("additional_fields"):
                params["additionalFields"] = additional_fields
            r = client.get(f"/employees/{employee_code}", params=params)

        elif name == "get_divisions":
            r = client.get("/divisions")

        elif name == "get_working_types":
            r = client.get("/working-types")

        elif name == "get_employee_groups":
            params = {}
            if additional_fields := arguments.get("additional_fields"):
                params["additionalFields"] = additional_fields
            r = client.get("/employee-groups", params=params)

        elif name == "get_timerecords":
            params = {}
            if employee_keys := arguments.get("employee_keys"):
                params["employeeKeys"] = employee_keys
            if division := arguments.get("division"):
                params["division"] = division
            if "ondivision" in arguments:
                params["ondivision"] = arguments["ondivision"]
            if start_date := arguments.get("start_date"):
                params["start"] = start_date
            if end_date := arguments.get("end_date"):
                params["end"] = end_date
            if additional_fields := arguments.get("additional_fields"):
                params["additionalFields"] = additional_fields
            r = client.get("/daily-workings/timerecord", params=params)

        elif name == "get_daily_workings":
            params = {
                "start": arguments["start_date"],
                "end": arguments["end_date"],
            }
            if division := arguments.get("division"):
                params["division"] = division
            if "ondivision" in arguments:
                params["ondivision"] = arguments["ondivision"]
            if additional_fields := arguments.get("additional_fields"):
                params["additionalFields"] = additional_fields
            r = client.get("/daily-workings", params=params)

        elif name == "get_monthly_workings":
            params = {}
            if division := arguments.get("division"):
                params["division"] = division
            if additional_fields := arguments.get("additional_fields"):
                params["additionalFields"] = additional_fields
            year_month = arguments["year_month"]
            r = client.get(f"/monthly-workings/{year_month}", params=params)

        elif name == "get_daily_schedules":
            params = {
                "start": arguments["start_date"],
                "end": arguments["end_date"],
            }
            if division := arguments.get("division"):
                params["division"] = division
            if "ondivision" in arguments:
                params["ondivision"] = arguments["ondivision"]
            if additional_fields := arguments.get("additional_fields"):
                params["additionalFields"] = additional_fields
            r = client.get("/daily-schedules", params=params)

        elif name == "record_time":
            employee_key = arguments["employee_key"]
            payload = {"time": arguments["time"]}
            if date := arguments.get("date"):
                payload["date"] = date
            if code := arguments.get("code"):
                payload["code"] = code
            if "is_omitted_working_day" in arguments:
                payload["isOmittedWorkingDay"] = arguments["is_omitted_working_day"]
            if division_code := arguments.get("division_code"):
                payload["divisionCode"] = division_code
            if "latitude" in arguments:
                payload["latitude"] = arguments["latitude"]
            if "longitude" in arguments:
                payload["longitude"] = arguments["longitude"]
            r = client.post(f"/daily-workings/timerecord/{employee_key}", json=payload)

        else:
            raise ValueError(f"未知のツール: {name}")

        r.raise_for_status()
        return format_response(r.json())


def main():
    import asyncio

    async def _run():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

    asyncio.run(_run())


if __name__ == "__main__":
    main()
