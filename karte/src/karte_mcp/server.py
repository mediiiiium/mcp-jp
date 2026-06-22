import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("karte-mcp")

BASE_URL = "https://api.karte.io"


def _client() -> httpx.Client:
    api_key = os.environ.get("KARTE_API_KEY")
    if not api_key:
        raise ValueError("KARTE_API_KEY が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="track_event",
            description="KARTE にイベントを送信してユーザー行動を記録する",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ユーザーID（ログイン済みユーザー）"},
                    "visitor_id": {"type": "string", "description": "訪問者ID（未ログインユーザー、vis- で始まる）"},
                    "event_name": {"type": "string", "description": "イベント名（例: purchase, view, add_to_cart）"},
                    "event_values": {
                        "type": "object",
                        "description": "イベントに紐づけるデータ（例: {\"item_id\": \"abc\", \"price\": 1000}）",
                    },
                },
                "required": ["event_name"],
            },
        ),
        types.Tool(
            name="get_user_events",
            description="指定ユーザーのイベント履歴を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ユーザーID"},
                    "event_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "取得するイベント名のリスト（最大10件、例: [\"view\", \"purchase\"]）",
                        "default": ["view"],
                    },
                },
                "required": ["user_id"],
            },
        ),
        types.Tool(
            name="track_event_exec_action",
            description="KARTE にイベントを送信し、サーバーサイドアクションを実行する",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ユーザーID（ログイン済みユーザー）"},
                    "visitor_id": {"type": "string", "description": "訪問者ID（未ログインユーザー）"},
                    "event_name": {"type": "string", "description": "イベント名"},
                    "event_values": {
                        "type": "object",
                        "description": "イベントに紐づけるデータ",
                    },
                },
                "required": ["event_name"],
            },
        ),
        types.Tool(
            name="get_campaign",
            description="接客サービス（キャンペーン）の詳細情報をIDで取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "campaign_id": {"type": "string", "description": "接客サービスのID"},
                },
                "required": ["campaign_id"],
            },
        ),
        types.Tool(
            name="get_campaign_stats",
            description="全接客サービスの設定と効果測定データをCSV形式で取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "集計開始日（YYYY-MM-DD 形式）",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "集計終了日（YYYY-MM-DD 形式）",
                    },
                    "range": {
                        "type": "string",
                        "description": "集計期間: latest_thirty_days / latest_a_week / latest_two_weeks / YYYY-MM",
                        "default": "latest_thirty_days",
                    },
                },
                "required": ["start_date", "end_date"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "track_event":
        keys: dict = {}
        if arguments.get("user_id"):
            keys["user_id"] = arguments["user_id"]
        elif arguments.get("visitor_id"):
            keys["visitor_id"] = arguments["visitor_id"]
        else:
            raise ValueError("user_id または visitor_id のいずれかが必要です")
        event: dict = {"event_name": arguments["event_name"]}
        if arguments.get("event_values"):
            event["values"] = arguments["event_values"]
        r = client.post("/v2/track/event/write", json={"keys": keys, "event": event})
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_user_events":
        payload = {
            "user_id": arguments["user_id"],
            "event_names": arguments.get("event_names", ["view"]),
        }
        r = client.post("/v2beta/track/event/get", json=payload)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "track_event_exec_action":
        keys = {}
        if arguments.get("user_id"):
            keys["user_id"] = arguments["user_id"]
        elif arguments.get("visitor_id"):
            keys["visitor_id"] = arguments["visitor_id"]
        else:
            raise ValueError("user_id または visitor_id のいずれかが必要です")
        event = {"event_name": arguments["event_name"]}
        if arguments.get("event_values"):
            event["values"] = arguments["event_values"]
        r = client.post("/v2beta/track/event/writeAndExecAction", json={"keys": keys, "event": event})
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_campaign":
        r = client.post("/v2beta/action/campaign/findById", json={"id": arguments["campaign_id"]})
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_campaign_stats":
        payload = {
            "start_date": arguments["start_date"],
            "end_date": arguments["end_date"],
            "range": arguments.get("range", "latest_thirty_days"),
        }
        r = client.post("/v2beta/action/campaign/getSettingsAndStats", json=payload)
        r.raise_for_status()
        return [types.TextContent(type="text", text=r.text)]

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
