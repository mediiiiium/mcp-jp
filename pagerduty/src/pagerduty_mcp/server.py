import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("pagerduty-mcp")
BASE_URL = "https://api.pagerduty.com"


def _client() -> httpx.Client:
    api_token = os.environ.get("PAGERDUTY_API_TOKEN")
    if not api_token:
        raise ValueError("PAGERDUTY_API_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "Authorization": f"Token token={api_token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.pagerduty+json;version=2",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_incidents",
            description="インシデント一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "statuses": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "ステータスフィルタ: triggered / acknowledged / resolved",
                    },
                    "limit": {"type": "integer", "description": "取得件数（デフォルト25）"},
                    "since": {"type": "string", "description": "この日時以降のインシデント（ISO8601形式）"},
                    "until": {"type": "string", "description": "この日時以前のインシデント（ISO8601形式）"},
                },
            },
        ),
        types.Tool(
            name="get_incident",
            description="インシデントの詳細を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "incident_id": {"type": "string", "description": "インシデントID"},
                },
                "required": ["incident_id"],
            },
        ),
        types.Tool(
            name="create_incident",
            description="新しいインシデントを作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "インシデントのタイトル"},
                    "service_id": {"type": "string", "description": "サービスID"},
                    "urgency": {"type": "string", "description": "緊急度: high / low"},
                    "body": {"type": "string", "description": "インシデントの詳細説明"},
                },
                "required": ["title", "service_id"],
            },
        ),
        types.Tool(
            name="list_services",
            description="サービス一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（デフォルト25）"},
                    "query": {"type": "string", "description": "サービス名で検索"},
                },
            },
        ),
        types.Tool(
            name="list_oncalls",
            description="現在オンコール中のユーザー一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "schedule_ids": {"type": "array", "items": {"type": "string"}, "description": "スケジュールIDでフィルタ"},
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "list_incidents":
        params = {"limit": arguments.get("limit", 25)}
        if arguments.get("statuses"):
            params["statuses[]"] = arguments["statuses"]
        if arguments.get("since"):
            params["since"] = arguments["since"]
        if arguments.get("until"):
            params["until"] = arguments["until"]
        r = client.get("/incidents", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_incident":
        incident_id = arguments["incident_id"]
        r = client.get(f"/incidents/{incident_id}")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "create_incident":
        payload = {
            "incident": {
                "type": "incident",
                "title": arguments["title"],
                "service": {"id": arguments["service_id"], "type": "service_reference"},
                "urgency": arguments.get("urgency", "high"),
            }
        }
        if arguments.get("body"):
            payload["incident"]["body"] = {"type": "incident_body", "details": arguments["body"]}
        r = client.post("/incidents", json=payload)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_services":
        params = {"limit": arguments.get("limit", 25)}
        if arguments.get("query"):
            params["query"] = arguments["query"]
        r = client.get("/services", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_oncalls":
        params = {}
        if arguments.get("schedule_ids"):
            params["schedule_ids[]"] = arguments["schedule_ids"]
        r = client.get("/oncalls", params=params)
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
