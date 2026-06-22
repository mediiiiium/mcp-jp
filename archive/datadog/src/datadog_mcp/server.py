import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("datadog-mcp")
BASE_URL = "https://api.datadoghq.com"


def _client() -> httpx.Client:
    api_key = os.environ.get("DATADOG_API_KEY")
    app_key = os.environ.get("DATADOG_APP_KEY")
    if not api_key:
        raise ValueError("DATADOG_API_KEY が設定されていません")
    if not app_key:
        raise ValueError("DATADOG_APP_KEY が設定されていません")
    site = os.environ.get("DATADOG_SITE", "datadoghq.com")
    return httpx.Client(
        base_url=f"https://api.{site}",
        headers={
            "DD-API-KEY": api_key,
            "DD-APPLICATION-KEY": app_key,
            "Content-Type": "application/json",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_monitors",
            description="モニター一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "モニター名でフィルタ"},
                    "tags": {"type": "string", "description": "タグでフィルタ（例: env:prod,team:backend）"},
                    "page_size": {"type": "integer", "description": "1ページあたりの件数（デフォルト100）"},
                },
            },
        ),
        types.Tool(
            name="get_monitor",
            description="モニターの詳細を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "monitor_id": {"type": "integer", "description": "モニターID"},
                },
                "required": ["monitor_id"],
            },
        ),
        types.Tool(
            name="list_dashboards",
            description="ダッシュボード一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter_shared": {"type": "boolean", "description": "共有ダッシュボードのみ表示"},
                },
            },
        ),
        types.Tool(
            name="query_metrics",
            description="メトリクスデータをクエリする",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "メトリクスクエリ（例: avg:system.cpu.user{host:myhost}）"},
                    "from_time": {"type": "integer", "description": "開始時刻（Unixタイムスタンプ秒）"},
                    "to_time": {"type": "integer", "description": "終了時刻（Unixタイムスタンプ秒）"},
                },
                "required": ["query", "from_time", "to_time"],
            },
        ),
        types.Tool(
            name="list_events",
            description="イベント一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "start": {"type": "integer", "description": "開始時刻（Unixタイムスタンプ秒）"},
                    "end": {"type": "integer", "description": "終了時刻（Unixタイムスタンプ秒）"},
                    "priority": {"type": "string", "description": "優先度: low / normal"},
                    "tags": {"type": "string", "description": "タグでフィルタ"},
                },
                "required": ["start", "end"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "list_monitors":
        params = {"page_size": arguments.get("page_size", 100)}
        if arguments.get("name"):
            params["name"] = arguments["name"]
        if arguments.get("tags"):
            params["tags"] = arguments["tags"]
        r = client.get("/api/v1/monitor", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_monitor":
        monitor_id = arguments["monitor_id"]
        r = client.get(f"/api/v1/monitor/{monitor_id}")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_dashboards":
        params = {}
        if arguments.get("filter_shared"):
            params["filter[shared]"] = arguments["filter_shared"]
        r = client.get("/api/v1/dashboard", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "query_metrics":
        params = {
            "query": arguments["query"],
            "from": arguments["from_time"],
            "to": arguments["to_time"],
        }
        r = client.get("/api/v1/query", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_events":
        params = {
            "start": arguments["start"],
            "end": arguments["end"],
        }
        if arguments.get("priority"):
            params["priority"] = arguments["priority"]
        if arguments.get("tags"):
            params["tags"] = arguments["tags"]
        r = client.get("/api/v1/events", params=params)
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
