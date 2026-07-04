import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("hrmos-kintai-mcp")

_token_cache: str | None = None


def _base_url() -> str:
    company_url = os.environ.get("HRMOS_COMPANY_URL")
    if not company_url:
        raise ValueError("HRMOS_COMPANY_URL が設定されていません")
    return f"https://ieyasu.co/api/{company_url}/v1"


def _get_token() -> str:
    global _token_cache
    if _token_cache:
        return _token_cache
    api_key = os.environ.get("HRMOS_API_KEY")
    if not api_key:
        raise ValueError("HRMOS_API_KEY が設定されていません")
    r = httpx.get(
        f"{_base_url()}/authentication/token",
        auth=(api_key, ""),
        timeout=30,
    )
    r.raise_for_status()
    token = r.json().get("token")
    if not token:
        raise ValueError("認証レスポンスに 'token' フィールドがありません")
    _token_cache = token
    return _token_cache


def _client() -> httpx.Client:
    token = _get_token()
    return httpx.Client(
        base_url=_base_url(),
        headers={
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_monthly_attendance",
            description=(
                "指定月の日次勤怠データ（1日ごとの出退勤・休憩時刻や実働時間などの明細行）を全社員分、"
                "1日1行の形式で取得する。社員ごとに設定された締め日を考慮した「対象月」で絞り込まれる点に"
                "注意（暦月と一致しない場合がある）。月ごとの合計値（総労働時間・残業時間などを社員1人1行に"
                "集計したレポート）が欲しい場合は本APIではなく別エンドポイント（work_output_months、本コネクタ"
                "未実装）が必要になる点に注意。user_id を指定するとその社員のみに絞り込める。from/to は"
                "勤怠日ではなく「レコードの更新日時（ISO 8601形式）」による絞り込みで、差分同期などに使う"
                "（当月分をすべて取りたいだけなら指定不要）。1ページ最大100件（既定50件、API側の既定は25件）。"
                "レスポンスヘッダーに総件数・総ページ数が入るが本ツールはボディのみ返すため、次ページの有無は"
                "件数が0件になるまで page を増やして確認すること。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "month": {"type": "string", "description": "対象月（YYYY-MM形式。例: 2026-06。社員ごとの締め日を考慮した月）"},
                    "user_id": {"type": "integer", "description": "この社員IDのみに絞り込む（list_users の id フィールド。省略時は全社員）"},
                    "from": {"type": "string", "description": "レコードの更新日時がこの日時以降のものだけに絞り込む（ISO 8601形式。勤怠日そのものの絞り込みではない）"},
                    "to": {"type": "string", "description": "レコードの更新日時がこの日時以前のものだけに絞り込む（ISO 8601形式。勤怠日そのものの絞り込みではない）"},
                    "page": {"type": "integer", "description": "ページ番号（既定1）", "default": 1, "minimum": 1},
                    "limit": {"type": "integer", "description": "1ページあたりの件数（最大100、既定50）", "default": 50, "minimum": 1, "maximum": 100},
                },
                "required": ["month"],
            },
        ),
        types.Tool(
            name="get_daily_attendance",
            description=(
                "指定日の日次勤怠データ（出退勤・休憩時刻や実働時間などの明細行）を全社員分1行ずつ取得する。"
                "get_monthly_attendance と異なり、このAPIには社員IDによる絞り込みパラメータが提供されていない"
                "（1人分だけ確認したい場合でも全社員分を取得してからクライアント側で絞り込む必要がある）。"
                "from/to は勤怠日ではなく「レコードの更新日時（ISO 8601形式）」による絞り込みで、差分同期などに"
                "使う。1ページ最大100件（既定50件、API側の既定は25件）。レスポンスヘッダーに総件数・総ページ数が"
                "入るが本ツールはボディのみ返すため、次ページの有無は件数が0件になるまで page を増やして確認する"
                "こと。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "day": {"type": "string", "description": "対象日（YYYY-MM-DD形式。例: 2026-06-15）"},
                    "from": {"type": "string", "description": "レコードの更新日時がこの日時以降のものだけに絞り込む（ISO 8601形式。勤怠日そのものの絞り込みではない）"},
                    "to": {"type": "string", "description": "レコードの更新日時がこの日時以前のものだけに絞り込む（ISO 8601形式。勤怠日そのものの絞り込みではない）"},
                    "page": {"type": "integer", "description": "ページ番号（既定1）", "default": 1, "minimum": 1},
                    "limit": {"type": "integer", "description": "1ページあたりの件数（最大100、既定50）", "default": 50, "minimum": 1, "maximum": 100},
                },
                "required": ["day"],
            },
        ),
        types.Tool(
            name="list_users",
            description=(
                "会社に登録されているユーザー（社員）の一覧を取得する。他のツール（get_monthly_attendance の "
                "user_id、get_user_stamps の user_id など）に渡す社員IDは、ここで返る各要素の `id` フィールド"
                "（内部ID）であり、`number`（社員番号）ではない点に注意。from/to はレコードの更新日時（ISO 8601"
                "形式）による絞り込みで、差分同期などに使う。1ページ最大100件（既定50件、API側の既定は25件）。"
                "レスポンスヘッダーに総件数・総ページ数が入るが本ツールはボディのみ返すため、次ページの有無は"
                "件数が0件になるまで page を増やして確認すること。社員の新規登録・更新用APIはHRMOS勤怠側に"
                "存在するが本コネクタでは未実装のため読み取り専用（書き込みは行わない）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "from": {"type": "string", "description": "レコードの更新日時がこの日時以降のものだけに絞り込む（ISO 8601形式）"},
                    "to": {"type": "string", "description": "レコードの更新日時がこの日時以前のものだけに絞り込む（ISO 8601形式）"},
                    "page": {"type": "integer", "description": "ページ番号（既定1）", "default": 1, "minimum": 1},
                    "limit": {"type": "integer", "description": "1ページあたりの件数（最大100、既定50）", "default": 50, "minimum": 1, "maximum": 100},
                },
            },
        ),
        types.Tool(
            name="list_departments",
            description=(
                "部署一覧を取得する。ページネーション（page/limit）に対応しており、1ページ最大100件"
                "（既定50件、API側の既定は25件）。部署数が多い会社では1回の呼び出しで全件揃わないことがあるため、"
                "件数が0件になるまで page を増やして確認すること。from/to はレコードの更新日時（ISO 8601形式）"
                "による絞り込み。部署の作成・更新・削除APIはHRMOS勤怠側に提供されていないため、このツールは"
                "常に読み取り専用となる。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "from": {"type": "string", "description": "レコードの更新日時がこの日時以降のものだけに絞り込む（ISO 8601形式）"},
                    "to": {"type": "string", "description": "レコードの更新日時がこの日時以前のものだけに絞り込む（ISO 8601形式）"},
                    "page": {"type": "integer", "description": "ページ番号（既定1）", "default": 1, "minimum": 1},
                    "limit": {"type": "integer", "description": "1ページあたりの件数（最大100、既定50）", "default": 50, "minimum": 1, "maximum": 100},
                },
            },
        ),
        types.Tool(
            name="get_monthly_report",
            description=(
                "指定月の月次集計レポート（社員1人1行、総労働時間・残業時間・遅刻日数・有給残日数などを"
                "集計した値）を取得する。get_monthly_attendance が返す1日1行の明細とは異なるエンドポイント"
                "（work_output_months）で、月締め状態（status）も含む。number（社員番号のカンマ区切り、"
                "list_users の number フィールド。id ではない点に注意）で絞り込み可能。status で月締め状況を"
                "絞り込める（0=未申請, 1=申請可能, 2=申請中, 3=承認, 99=強制承認。カンマ区切りで複数指定可）。"
                "from/to は勤怠月そのものではなく「レコードの更新日時（ISO 8601形式）」による絞り込み（差分"
                "同期用）。1ページ最大100件（既定50件、API側の既定は25件）。レスポンスヘッダーに総件数・"
                "総ページ数が入るが本ツールはボディのみ返すため、次ページの有無は件数が0件になるまで page を"
                "増やして確認すること。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "month": {"type": "string", "description": "対象月（YYYY-MM形式。例: 2026-06）"},
                    "number": {"type": "string", "description": "社員番号で絞り込む（list_users の number フィールド。カンマ区切りで複数指定可。例: A0001,B0001）"},
                    "status": {"type": "string", "description": "月締め状況で絞り込む（0=未申請, 1=申請可能, 2=申請中, 3=承認, 99=強制承認。カンマ区切りで複数指定可。例: 3,99）"},
                    "from": {"type": "string", "description": "レコードの更新日時がこの日時以降のものだけに絞り込む（ISO 8601形式。勤怠月そのものの絞り込みではない）"},
                    "to": {"type": "string", "description": "レコードの更新日時がこの日時以前のものだけに絞り込む（ISO 8601形式。勤怠月そのものの絞り込みではない）"},
                    "page": {"type": "integer", "description": "ページ番号（既定1）", "default": 1, "minimum": 1},
                    "limit": {"type": "integer", "description": "1ページあたりの件数（最大100、既定50）", "default": 50, "minimum": 1, "maximum": 100},
                },
                "required": ["month"],
            },
        ),
        types.Tool(
            name="list_paid_holidays",
            description=(
                "会社に設定されている休暇（有給休暇の種類。例: 一般社員向け年次有給休暇など）の一覧を取得する。"
                "ここで返る `id` は get_paid_holiday_balance に渡す休暇設定IDとして使う。from/to はレコードの"
                "更新日時（ISO 8601形式）による絞り込み。1ページ最大100件（既定50件、API側の既定は25件）。"
                "レスポンスヘッダーに総件数・総ページ数が入るが本ツールはボディのみ返すため、次ページの有無は"
                "件数が0件になるまで page を増やして確認すること。書き込みは行わない（休暇設定の作成・更新・"
                "削除APIはHRMOS勤怠側に提供されていない）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "from": {"type": "string", "description": "レコードの更新日時がこの日時以降のものだけに絞り込む（ISO 8601形式）"},
                    "to": {"type": "string", "description": "レコードの更新日時がこの日時以前のものだけに絞り込む（ISO 8601形式）"},
                    "page": {"type": "integer", "description": "ページ番号（既定1）", "default": 1, "minimum": 1},
                    "limit": {"type": "integer", "description": "1ページあたりの件数（最大100、既定50）", "default": 50, "minimum": 1, "maximum": 100},
                },
            },
        ),
        types.Tool(
            name="get_paid_holiday_balance",
            description=(
                "指定した社員・年度・休暇設定について、休暇の付与・取得・残数の履歴（1レコード=1時点のスナップ"
                "ショット。残日数 remaining_days/remaining_hours、付与 received_days、取得 taken_days、失効 "
                "expired_days などを含む）を取得する。現在の残日数だけを知りたい場合は、返ってきたレコードのうち"
                "最新のものを見ればよい（このAPI自体に「最新のみ返す」オプションはない）。paid_holiday_id は "
                "list_paid_holidays の id、user_id は list_users の id を使う。from/to はレコードの更新日時"
                "（ISO 8601形式）による絞り込み。1ページ最大100件（既定50件、API側の既定は25件）。書き込みは"
                "行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "paid_holiday_id": {"type": "integer", "description": "休暇設定ID（list_paid_holidays の id フィールド）"},
                    "user_id": {"type": "integer", "description": "社員ID（list_users の id フィールド。社員番号 number ではない）"},
                    "year": {"type": "integer", "description": "年度（例: 2026）"},
                    "from": {"type": "string", "description": "レコードの更新日時がこの日時以降のものだけに絞り込む（ISO 8601形式）"},
                    "to": {"type": "string", "description": "レコードの更新日時がこの日時以前のものだけに絞り込む（ISO 8601形式）"},
                    "page": {"type": "integer", "description": "ページ番号（既定1）", "default": 1, "minimum": 1},
                    "limit": {"type": "integer", "description": "1ページあたりの件数（最大100、既定50）", "default": 50, "minimum": 1, "maximum": 100},
                },
                "required": ["paid_holiday_id", "user_id", "year"],
            },
        ),
        types.Tool(
            name="get_user_stamps",
            description=(
                "指定ユーザー1人分の打刻履歴（出勤・退勤・休憩開始・休憩終了の各イベント）を、最新のものから"
                "順に取得する（並び順の変更はできない）。stamp_type を指定するとイベント種別で絞り込める"
                "（1=出勤, 2=退勤, 7=休憩開始, 8=休憩終了）。from/to は打刻日時そのものではなく「レコードの"
                "更新日時（ISO 8601形式）」による絞り込みである点に注意（打刻直後に更新されることが多いため"
                "実務上は打刻日時に近い値になるが、後から打刻が修正された場合はその修正日時が基準になる）。"
                "1ページ最大100件（既定50件、API側の既定は25件）。レスポンスヘッダーに総件数・総ページ数が"
                "入るが本ツールはボディのみ返すため、次ページの有無は件数が0件になるまで page を増やして確認"
                "すること。打刻の新規登録APIはHRMOS勤怠側に存在するが本コネクタでは未実装であり、また打刻の"
                "更新・削除APIはHRMOS勤怠側にも存在しないため、誤った打刻の修正はこのAPI経由ではできない"
                "（管理画面から行う必要がある）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ユーザーID（list_users の id フィールド。社員番号 number ではない）"},
                    "stamp_type": {
                        "type": "integer",
                        "description": "打刻区分で絞り込む（1=出勤, 2=退勤, 7=休憩開始, 8=休憩終了）。省略時は全種別",
                    },
                    "from": {"type": "string", "description": "レコードの更新日時がこの日時以降のものだけに絞り込む（ISO 8601形式。打刻日時そのものの絞り込みではない）"},
                    "to": {"type": "string", "description": "レコードの更新日時がこの日時以前のものだけに絞り込む（ISO 8601形式。打刻日時そのものの絞り込みではない）"},
                    "page": {"type": "integer", "description": "ページ番号（既定1）", "default": 1, "minimum": 1},
                    "limit": {"type": "integer", "description": "1ページあたりの件数（最大100、既定50）", "default": 50, "minimum": 1, "maximum": 100},
                },
                "required": ["user_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    global _token_cache
    try:
        try:
            client = _client()
        except httpx.HTTPStatusError:
            _token_cache = None
            client = _client()

        with client:
            if name == "get_monthly_attendance":
                month = arguments["month"]
                params: dict = {
                    "page": arguments.get("page", 1),
                    "limit": arguments.get("limit", 50),
                }
                if arguments.get("user_id") is not None:
                    params["user_id"] = arguments["user_id"]
                if arguments.get("from"):
                    params["from"] = arguments["from"]
                if arguments.get("to"):
                    params["to"] = arguments["to"]
                r = client.get(f"/work_outputs/monthly/{month}", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_daily_attendance":
                day = arguments["day"]
                params = {
                    "page": arguments.get("page", 1),
                    "limit": arguments.get("limit", 50),
                }
                if arguments.get("from"):
                    params["from"] = arguments["from"]
                if arguments.get("to"):
                    params["to"] = arguments["to"]
                r = client.get(f"/work_outputs/daily/{day}", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_users":
                params = {
                    "page": arguments.get("page", 1),
                    "limit": arguments.get("limit", 50),
                }
                if arguments.get("from"):
                    params["from"] = arguments["from"]
                if arguments.get("to"):
                    params["to"] = arguments["to"]
                r = client.get("/users", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_departments":
                params = {
                    "page": arguments.get("page", 1),
                    "limit": arguments.get("limit", 50),
                }
                if arguments.get("from"):
                    params["from"] = arguments["from"]
                if arguments.get("to"):
                    params["to"] = arguments["to"]
                r = client.get("/departments", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_monthly_report":
                month = arguments["month"]
                params = {
                    "page": arguments.get("page", 1),
                    "limit": arguments.get("limit", 50),
                }
                if arguments.get("number"):
                    params["number"] = arguments["number"]
                if arguments.get("status"):
                    params["status"] = arguments["status"]
                if arguments.get("from"):
                    params["from"] = arguments["from"]
                if arguments.get("to"):
                    params["to"] = arguments["to"]
                r = client.get(f"/work_output_months/monthly/{month}", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_paid_holidays":
                params = {
                    "page": arguments.get("page", 1),
                    "limit": arguments.get("limit", 50),
                }
                if arguments.get("from"):
                    params["from"] = arguments["from"]
                if arguments.get("to"):
                    params["to"] = arguments["to"]
                r = client.get("/paid_holidays", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_paid_holiday_balance":
                paid_holiday_id = arguments["paid_holiday_id"]
                user_id = arguments["user_id"]
                year = arguments["year"]
                params = {
                    "page": arguments.get("page", 1),
                    "limit": arguments.get("limit", 50),
                }
                if arguments.get("from"):
                    params["from"] = arguments["from"]
                if arguments.get("to"):
                    params["to"] = arguments["to"]
                r = client.get(
                    f"/paid_holidays/{paid_holiday_id}/users/{user_id}/year/{year}",
                    params=params,
                )
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_user_stamps":
                user_id = arguments["user_id"]
                params = {
                    "page": arguments.get("page", 1),
                    "limit": arguments.get("limit", 50),
                }
                if arguments.get("stamp_type") is not None:
                    params["stamp_type"] = arguments["stamp_type"]
                if arguments.get("from"):
                    params["from"] = arguments["from"]
                if arguments.get("to"):
                    params["to"] = arguments["to"]
                r = client.get(f"/stamp_logs/user/{user_id}", params=params)
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
