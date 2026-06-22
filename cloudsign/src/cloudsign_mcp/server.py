import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("cloudsign-mcp")
BASE_URL = "https://api.cloudsign.jp"


def _get_token() -> str:
    client_id = os.environ.get("CLOUDSIGN_CLIENT_ID")
    if not client_id:
        raise ValueError("CLOUDSIGN_CLIENT_ID が設定されていません")
    r = httpx.post(
        f"{BASE_URL}/token",
        data={"client_id": client_id},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def _client() -> httpx.Client:
    token = _get_token()
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
            name="list_documents",
            description="書類一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "タイトルで絞り込み"},
                    "status": {
                        "type": "integer",
                        "description": "ステータス: 0=下書き, 1=送信済み, 2=完了, 3=差戻し, 4=却下, 5=無効",
                    },
                    "offset": {"type": "integer", "description": "取得開始位置", "default": 0},
                    "limit": {"type": "integer", "description": "取得件数（最大100）", "default": 20},
                },
            },
        ),
        types.Tool(
            name="get_document",
            description="書類の詳細情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "書類ID"},
                },
                "required": ["document_id"],
            },
        ),
        types.Tool(
            name="create_document",
            description="新しい書類を作成する（タイトル・テンプレートから）",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "書類タイトル"},
                    "template_id": {"type": "string", "description": "テンプレートID（省略時は空の書類）"},
                    "message": {"type": "string", "description": "署名依頼メッセージ"},
                },
                "required": ["title"],
            },
        ),
        types.Tool(
            name="set_participants",
            description="書類の署名者（参加者）情報を設定する",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "書類ID"},
                    "participants": {
                        "type": "array",
                        "description": "署名者リスト",
                        "items": {
                            "type": "object",
                            "properties": {
                                "email": {"type": "string", "description": "署名者のメールアドレス"},
                                "name": {"type": "string", "description": "署名者の氏名"},
                            },
                            "required": ["email", "name"],
                        },
                    },
                },
                "required": ["document_id", "participants"],
            },
        ),
        types.Tool(
            name="send_document",
            description="書類を署名依頼として送信する（ステータスを送信済みに変更）",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "書類ID"},
                },
                "required": ["document_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_documents":
                params = {
                    "offset": arguments.get("offset", 0),
                    "limit": arguments.get("limit", 20),
                }
                if arguments.get("title"):
                    params["title"] = arguments["title"]
                if arguments.get("status") is not None:
                    params["status"] = arguments["status"]
                r = client.get("/documents", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_document":
                r = client.get(f"/documents/{arguments['document_id']}")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "create_document":
                payload: dict = {"title": arguments["title"]}
                if arguments.get("template_id"):
                    payload["template_id"] = arguments["template_id"]
                if arguments.get("message"):
                    payload["message"] = arguments["message"]
                r = client.post("/documents", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "set_participants":
                document_id = arguments["document_id"]
                results = []
                for i, p in enumerate(arguments["participants"]):
                    payload = {"email": p["email"], "name": p["name"]}
                    r = client.put(f"/documents/{document_id}/participants/{i + 1}", json=payload)
                    r.raise_for_status()
                    results.append(r.json())
                return format_response(results)

            elif name == "send_document":
                r = client.put(
                    f"/documents/{arguments['document_id']}",
                    json={"status": 1},
                )
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
