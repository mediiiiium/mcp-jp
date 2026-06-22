import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("trello-mcp")
BASE_URL = "https://api.trello.com/1"


def _params() -> dict:
    api_key = os.environ.get("TRELLO_API_KEY")
    token = os.environ.get("TRELLO_TOKEN")
    if not api_key:
        raise ValueError("TRELLO_API_KEY が設定されていません")
    if not token:
        raise ValueError("TRELLO_TOKEN が設定されていません")
    return {"key": api_key, "token": token}


def _client() -> httpx.Client:
    return httpx.Client(base_url=BASE_URL, timeout=30)


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_boards",
            description="ボード一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="list_lists",
            description="ボード内のリスト一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "board_id": {"type": "string", "description": "ボードID"},
                },
                "required": ["board_id"],
            },
        ),
        types.Tool(
            name="list_cards",
            description="リスト内のカード一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_id": {"type": "string", "description": "リストID"},
                },
                "required": ["list_id"],
            },
        ),
        types.Tool(
            name="create_card",
            description="新しいカードを作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_id": {"type": "string", "description": "カードを追加するリストID"},
                    "name": {"type": "string", "description": "カード名"},
                    "desc": {"type": "string", "description": "カードの説明"},
                    "due": {"type": "string", "description": "期限日（ISO8601形式）"},
                },
                "required": ["list_id", "name"],
            },
        ),
        types.Tool(
            name="move_card",
            description="カードを別のリストに移動する",
            inputSchema={
                "type": "object",
                "properties": {
                    "card_id": {"type": "string", "description": "カードID"},
                    "list_id": {"type": "string", "description": "移動先リストID"},
                },
                "required": ["card_id", "list_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()
    auth = _params()

    if name == "list_boards":
        r = client.get("/members/me/boards", params=auth)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_lists":
        board_id = arguments["board_id"]
        r = client.get(f"/boards/{board_id}/lists", params=auth)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_cards":
        list_id = arguments["list_id"]
        r = client.get(f"/lists/{list_id}/cards", params=auth)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "create_card":
        params = {**auth, "idList": arguments["list_id"], "name": arguments["name"]}
        if arguments.get("desc"):
            params["desc"] = arguments["desc"]
        if arguments.get("due"):
            params["due"] = arguments["due"]
        r = client.post("/cards", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "move_card":
        card_id = arguments["card_id"]
        params = {**auth, "idList": arguments["list_id"]}
        r = client.put(f"/cards/{card_id}", params=params)
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
