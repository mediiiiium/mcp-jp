import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

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


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_employees",
            description="従業員一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（最大500）", "default": 100},
                    "offset": {"type": "integer", "description": "オフセット", "default": 0},
                },
            },
        ),
        types.Tool(
            name="get_daily_workings",
            description="指定期間の日次勤怠データを取得する（出退勤時刻・残業時間等）",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "開始日 YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "終了日 YYYY-MM-DD"},
                    "employee_code": {"type": "string", "description": "従業員コード（省略時は全員）"},
                    "additional_fields": {
                        "type": "string",
                        "description": "追加フィールド（例: currentDateEmployee）",
                    },
                },
                "required": ["start_date", "end_date"],
            },
        ),
        types.Tool(
            name="get_monthly_workings",
            description="指定月の月次勤怠集計データを取得する（総労働時間・残業時間・有休等）",
            inputSchema={
                "type": "object",
                "properties": {
                    "year_month": {"type": "string", "description": "対象年月 YYYY-MM"},
                    "employee_code": {"type": "string", "description": "従業員コード（省略時は全員）"},
                },
                "required": ["year_month"],
            },
        ),
        types.Tool(
            name="get_daily_schedules",
            description="指定期間のシフト・スケジュールを取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "開始日 YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "終了日 YYYY-MM-DD"},
                    "employee_code": {"type": "string", "description": "従業員コード（省略時は全員）"},
                },
                "required": ["start_date", "end_date"],
            },
        ),
        types.Tool(
            name="record_time",
            description="打刻を記録する（出勤・退勤・外出・戻り等）",
            inputSchema={
                "type": "object",
                "properties": {
                    "employee_code": {"type": "string", "description": "従業員コード"},
                    "date": {"type": "string", "description": "打刻日 YYYY-MM-DD"},
                    "time": {"type": "string", "description": "打刻時刻 HH:MM"},
                    "type_code": {
                        "type": "string",
                        "description": "打刻種別コード（11=出勤 / 12=退勤 / 21=外出 / 22=戻り）",
                        "enum": ["11", "12", "21", "22"],
                    },
                },
                "required": ["employee_code", "date", "time", "type_code"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = get_client()

    if name == "get_employees":
        params = {
            "limit": arguments.get("limit", 100),
            "offset": arguments.get("offset", 0),
        }
        r = client.get("/employees", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_daily_workings":
        params = {
            "start": arguments["start_date"],
            "end": arguments["end_date"],
        }
        if arguments.get("employee_code"):
            params["employeeCode"] = arguments["employee_code"]
        if arguments.get("additional_fields"):
            params["additionalFields"] = arguments["additional_fields"]
        r = client.get("/daily-workings", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_monthly_workings":
        params = {"yearMonth": arguments["year_month"].replace("-", "")}
        if arguments.get("employee_code"):
            params["employeeCode"] = arguments["employee_code"]
        r = client.get("/monthly-workings", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_daily_schedules":
        params = {
            "start": arguments["start_date"],
            "end": arguments["end_date"],
        }
        if arguments.get("employee_code"):
            params["employeeCode"] = arguments["employee_code"]
        r = client.get("/daily-schedules", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "record_time":
        payload = {
            "employeeCode": arguments["employee_code"],
            "date": arguments["date"],
            "time": arguments["time"],
            "typeCode": arguments["type_code"],
        }
        r = client.post("/daily-workings/timerecord", json=payload)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    else:
        raise ValueError(f"未知のツール: {name}")


def main():
    import asyncio

    async def _run():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

    asyncio.run(_run())


if __name__ == "__main__":
    main()
