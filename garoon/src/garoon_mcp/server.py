import os
import base64
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("garoon-mcp")


def _client() -> httpx.Client:
    login_name = os.environ.get("GAROON_LOGIN_NAME")
    password = os.environ.get("GAROON_PASSWORD")
    subdomain = os.environ.get("GAROON_SUBDOMAIN")
    if not login_name:
        raise ValueError("GAROON_LOGIN_NAME が設定されていません")
    if not password:
        raise ValueError("GAROON_PASSWORD が設定されていません")
    if not subdomain:
        raise ValueError("GAROON_SUBDOMAIN が設定されていません")
    token = base64.b64encode(f"{login_name}:{password}".encode()).decode()
    return httpx.Client(
        base_url=f"https://{subdomain}.cybozu.com/g/api/v1",
        headers={"X-Cybozu-Authorization": token, "Content-Type": "application/json"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_events",
            description="Garoon スケジュールの予定一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "range_start": {
                        "type": "string",
                        "description": "取得開始日時（RFC 3339形式、例: 2024-01-01T00:00:00Z）",
                    },
                    "range_end": {
                        "type": "string",
                        "description": "取得終了日時（RFC 3339形式、例: 2024-01-31T23:59:59Z）",
                    },
                    "target": {
                        "type": "string",
                        "description": "絞り込み対象のユーザーID・組織ID・施設ID",
                    },
                    "target_type": {
                        "type": "string",
                        "description": "targetの種別（user / organization / facility）",
                        "enum": ["user", "organization", "facility"],
                    },
                    "limit": {
                        "type": "integer",
                        "description": "取得件数（最大1000、デフォルト100）",
                        "default": 20,
                    },
                    "offset": {
                        "type": "integer",
                        "description": "取得開始位置（デフォルト0）",
                        "default": 0,
                    },
                },
            },
        ),
        types.Tool(
            name="create_event",
            description="Garoon スケジュールに予定を登録する",
            inputSchema={
                "type": "object",
                "properties": {
                    "subject": {
                        "type": "string",
                        "description": "予定のタイトル",
                    },
                    "event_type": {
                        "type": "string",
                        "description": "予定の種別（REGULAR: 通常予定 / ALL_DAY: 期間予定）",
                        "enum": ["REGULAR", "ALL_DAY"],
                        "default": "REGULAR",
                    },
                    "start_datetime": {
                        "type": "string",
                        "description": "開始日時（RFC 3339形式、例: 2024-01-15T10:00:00+09:00）",
                    },
                    "end_datetime": {
                        "type": "string",
                        "description": "終了日時（RFC 3339形式）",
                    },
                    "notes": {
                        "type": "string",
                        "description": "予定のメモ・詳細",
                    },
                    "attendee_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "参加者のユーザーIDリスト",
                    },
                    "visibility_type": {
                        "type": "string",
                        "description": "公開設定（PUBLIC: 公開 / PRIVATE: 非公開）",
                        "enum": ["PUBLIC", "PRIVATE"],
                        "default": "PUBLIC",
                    },
                },
                "required": ["subject", "start_datetime", "end_datetime"],
            },
        ),
        types.Tool(
            name="list_users",
            description="Garoon のユーザー一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "ユーザー名（表示名またはログイン名）で絞り込み",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "取得件数（最大1000、デフォルト100）",
                        "default": 50,
                    },
                    "offset": {
                        "type": "integer",
                        "description": "取得開始位置（デフォルト0）",
                        "default": 0,
                    },
                },
            },
        ),
        types.Tool(
            name="list_workflow_requests",
            description="Garoon ワークフローの申請一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "ステータスで絞り込み（IN_PROGRESS: 進行中, APPROVED: 承認済み, REJECTED: 却下, WITHDRAWN: 取り消し, COMPLETED: 完了）",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "取得件数（最大1000、デフォルト100）",
                        "default": 20,
                    },
                    "offset": {
                        "type": "integer",
                        "description": "取得開始位置（デフォルト0）",
                        "default": 0,
                    },
                    "order_by": {
                        "type": "string",
                        "description": "ソート条件（例: createdAt desc）",
                        "default": "createdAt desc",
                    },
                },
            },
        ),
        types.Tool(
            name="get_presence",
            description="指定ユーザーの在席情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "GaroonユーザーID",
                    },
                },
                "required": ["user_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "list_events":
        params: dict = {
            "limit": arguments.get("limit", 20),
            "offset": arguments.get("offset", 0),
        }
        if arguments.get("range_start"):
            params["rangeStart"] = arguments["range_start"]
        if arguments.get("range_end"):
            params["rangeEnd"] = arguments["range_end"]
        if arguments.get("target"):
            params["target"] = arguments["target"]
        if arguments.get("target_type"):
            params["targetType"] = arguments["target_type"]
        r = client.get("/schedule/events", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "create_event":
        body: dict = {
            "eventType": arguments.get("event_type", "REGULAR"),
            "subject": arguments["subject"],
            "start": {"dateTime": arguments["start_datetime"]},
            "end": {"dateTime": arguments["end_datetime"]},
            "visibilityType": arguments.get("visibility_type", "PUBLIC"),
        }
        if arguments.get("notes"):
            body["notes"] = arguments["notes"]
        if arguments.get("attendee_ids"):
            body["attendees"] = [{"type": "USER", "id": uid} for uid in arguments["attendee_ids"]]
        r = client.post("/schedule/events", content=json.dumps(body))
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_users":
        params = {
            "limit": arguments.get("limit", 50),
            "offset": arguments.get("offset", 0),
        }
        if arguments.get("name"):
            params["name"] = arguments["name"]
        r = client.get("/base/users", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_workflow_requests":
        params = {
            "limit": arguments.get("limit", 20),
            "offset": arguments.get("offset", 0),
            "orderBy": arguments.get("order_by", "createdAt desc"),
        }
        if arguments.get("status"):
            params["status"] = arguments["status"]
        r = client.get("/workflow/admin/requests", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_presence":
        user_id = arguments["user_id"]
        r = client.get(f"/presence/users/{user_id}")
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
