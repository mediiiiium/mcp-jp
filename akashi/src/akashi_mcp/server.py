import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("akashi-mcp")

BASE_URL = "https://atnd.ak4.jp/api/cooperation"


def _company_id() -> str:
    cid = os.environ.get("AKASHI_COMPANY_ID")
    if not cid:
        raise ValueError("AKASHI_COMPANY_ID が設定されていません")
    return cid


def _token() -> str:
    tok = os.environ.get("AKASHI_TOKEN")
    if not tok:
        raise ValueError("AKASHI_TOKEN が設定されていません")
    return tok


def _get(path: str, params: dict | None = None) -> dict:
    p = {**(params or {}), "token": _token()}
    r = httpx.get(f"{BASE_URL}{path}", params=p, timeout=30)
    r.raise_for_status()
    return r.json()


def _post(path: str, body: dict) -> dict:
    r = httpx.post(f"{BASE_URL}{path}", json={**body, "token": _token()}, timeout=30)
    r.raise_for_status()
    return r.json()


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_stamps",
            description=(
                "自身、または管理下の従業員1名の指定期間の打刻記録（出勤・退勤・休憩などのイベント履歴）を取得する。"
                "staff_id を省略するとトークンに紐づく本人の打刻を返す。start_date/end_date で指定できる期間は"
                "最長6ヶ月まで、かつ1回のリクエストで取得できる打刻は最大1000件までという API 側の制限があり、"
                "超える場合は期間を分割して複数回呼び出す必要がある（カーソル等によるページネーションは提供されて"
                "いない）。並び順は API 仕様上明記されていない。複数の従業員をまとめて取得する API（multiple_stamps、"
                "勤怠期間は最長1日・最大50名まで）は Akashi 側に存在するが、本コネクタでは未実装のため、複数従業員分が"
                "必要な場合は staff_id を変えて複数回呼び出すこと。書き込みは行わない。打刻の更新・削除 API は"
                "Akashi 側に存在しないため、誤った打刻を修正する手段はこのAPI経由では提供されていない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "取得開始日時（yyyymmddHHMMSS 形式、例: 20240101000000）。start_date〜end_dateは最長6ヶ月まで指定可能。",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "取得終了日時（yyyymmddHHMMSS 形式、例: 20240131235959）。この期間内で最大1000件までしか取得できない。",
                    },
                    "staff_id": {
                        "type": "integer",
                        "description": "取得対象の従業員ID（従業員番号ではない）。省略時はトークンに紐づく本人の打刻を取得する。",
                    },
                },
                "required": ["start_date", "end_date"],
            },
        ),
        types.Tool(
            name="post_stamp",
            description=(
                "トークンに紐づく従業員の打刻を1件記録する（出勤・退勤・直行・直帰・休憩入・休憩戻）。"
                "呼び出すたびに新しい打刻イベントが1件追加される操作であり、同じ内容で複数回呼んでも1回にまとまる"
                "ことはない（べき等ではない）ため、二重打刻に注意すること。stamp_type を省略すると、Akashi 側が"
                "その従業員の打刻履歴をもとに出勤・退勤のどちらかを自動判定する。stamped_at はクライアント側の"
                "参考時刻であり、実際に記録される打刻時刻は Akashi サーバー側の受信時刻になる（timezone は"
                "stamped_at のタイムゾーンを +09:00 のような形式で伝えるためのもの）。打刻の更新・削除 API は"
                "提供されていないため、誤って記録した打刻を本APIで取り消すことはできない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "stamp_type": {
                        "type": "integer",
                        "description": (
                            "打刻種別: 11=出勤, 12=退勤, 21=直行, 22=直帰, 31=休憩入, 32=休憩戻。"
                            "省略した場合、Akashi が打刻履歴から出勤・退勤のいずれかを自動判定する。"
                        ),
                    },
                    "stamped_at": {
                        "type": "string",
                        "description": "クライアント側の打刻日時（yyyy/mm/dd HH:MM:SS 形式、省略時はサーバー受信時刻が使われる）。実際に記録される時刻はサーバー側の時刻が優先される。",
                    },
                    "timezone": {
                        "type": "string",
                        "description": "stamped_at のタイムゾーンを +09:00 のような形式で指定する（省略可）。",
                    },
                },
                "required": [],
            },
        ),
        types.Tool(
            name="list_staffs",
            description=(
                "トークンに紐づく従業員本人、および管理下にある従業員の一覧を取得する。1ページあたり最大20名まで"
                "しか返らないため、全件取得するには page を0から順に増やしながら、レスポンスの TotalCount を"
                "参考に繰り返し呼び出す必要がある（例: page=0 で1〜20人目、page=1 で21〜40人目）。特定の1名の詳細"
                "だけが必要な場合は get_staff の方が効率的。Akashi API には従業員の新規登録・更新（PATCH）や"
                "退職・削除（DELETE）の API も用意されているが、本コネクタでは読み取り専用のためこれらは未実装。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer",
                        "description": "ページ番号（0から開始。0が1〜20人目、1が21〜40人目…）。既定0。",
                        "default": 0,
                    },
                },
            },
        ),
        types.Tool(
            name="get_staff",
            description=(
                "従業員ID（従業員番号ではなく Akashi 内部の staff_id）を指定して、その1名の詳細情報（氏名・所属組織・"
                "雇用区分・権限グループ・管理対象組織など）を取得する。一覧から探すのではなく特定の1名の情報だけが"
                "欲しい場合に list_staffs より少ないリクエストで済む。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "staff_id": {
                        "type": "integer",
                        "description": "取得対象の従業員ID（従業員番号ではない、get_staffやlist_staffsのレスポンスに含まれるstaffId）",
                    },
                },
                "required": ["staff_id"],
            },
        ),
        types.Tool(
            name="get_alerts",
            description=(
                "トークンに紐づく従業員本人の勤怠アラート一覧を取得する。アラート種別は "
                "1=打刻忘れ, 2=欠勤疑い, 3=休憩過小/超過, 4=出勤打刻乖離, 5=退勤打刻乖離, 6=休日出勤, 7=遅刻, "
                "8=早退, 9=残業時間閾値超え, 10=無断出勤 のいずれか。日付範囲や従業員IDによる絞り込みパラメータは"
                "APIとして提供されておらず、常にトークンに紐づく本人分の全アラートが返る。ページネーションもない。"
                "書き込みは行わない。"
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
        company_id = _company_id()

        if name == "get_stamps":
            params: dict = {
                "start_date": arguments["start_date"],
                "end_date": arguments["end_date"],
            }
            if arguments.get("staff_id") is not None:
                path = f"/{company_id}/stamps/{arguments['staff_id']}"
            else:
                path = f"/{company_id}/stamps"
            result = _get(path, params)
            return format_response(result)

        elif name == "post_stamp":
            body: dict = {}
            if arguments.get("stamp_type") is not None:
                body["type"] = arguments["stamp_type"]
            if arguments.get("stamped_at"):
                body["stampedAt"] = arguments["stamped_at"]
            if arguments.get("timezone"):
                body["timezone"] = arguments["timezone"]
            result = _post(f"/{company_id}/stamps", body)
            return format_response(result)

        elif name == "list_staffs":
            params = {"page": arguments.get("page", 0)}
            result = _get(f"/{company_id}/staffs", params)
            return format_response(result)

        elif name == "get_staff":
            result = _get(f"/{company_id}/staffs/{arguments['staff_id']}")
            return format_response(result)

        elif name == "get_alerts":
            result = _get(f"/{company_id}/alerts")
            return format_response(result)

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
