import os
import json
import base64
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("makeleaps-mcp")
BASE_URL = "https://api.makeleaps.com"

_token_cache: str | None = None


def _get_token() -> str:
    global _token_cache
    if _token_cache:
        return _token_cache
    client_id = os.environ.get("MAKELEAPS_CLIENT_ID")
    client_secret = os.environ.get("MAKELEAPS_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise ValueError("MAKELEAPS_CLIENT_ID と MAKELEAPS_CLIENT_SECRET が設定されていません")
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    r = httpx.post(
        f"{BASE_URL}/user/oauth2/token/",
        headers={"Authorization": f"Basic {credentials}"},
        data={"grant_type": "client_credentials"},
        timeout=30,
    )
    r.raise_for_status()
    _token_cache = r.json()["access_token"]
    return _token_cache


def _partner_mid() -> str:
    mid = os.environ.get("MAKELEAPS_PARTNER_MID")
    if not mid:
        raise ValueError("MAKELEAPS_PARTNER_MID が設定されていません")
    return mid


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
            name="list_clients",
            description="取引先（クライアント）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": "取引先名で全文検索"},
                    "archived": {"type": "boolean", "description": "アーカイブ済みを含むか（デフォルト: false）"},
                },
            },
        ),
        types.Tool(
            name="list_documents",
            description="書類（請求書・見積書等）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_type": {"type": "string", "description": "書類種別: invoice（請求書）、quote（見積書）、delivery（納品書）"},
                    "search": {"type": "string", "description": "書類番号・件名で検索"},
                    "page": {"type": "integer", "description": "ページ番号", "default": 1},
                },
            },
        ),
        types.Tool(
            name="get_document",
            description="書類の詳細情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_mid": {"type": "string", "description": "書類のMID"},
                },
                "required": ["document_mid"],
            },
        ),
        types.Tool(
            name="create_document",
            description="新しい書類（請求書・見積書等）を作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_type": {"type": "string", "description": "書類種別: invoice（請求書）、quote（見積書）", "default": "invoice"},
                    "document_number": {"type": "string", "description": "書類番号"},
                    "client_mid": {"type": "string", "description": "取引先のMID"},
                    "date": {"type": "string", "description": "発行日（YYYY-MM-DD）"},
                    "due_date": {"type": "string", "description": "支払期限（YYYY-MM-DD）"},
                    "title": {"type": "string", "description": "件名"},
                    "currency": {"type": "string", "description": "通貨コード（例: JPY）", "default": "JPY"},
                    "line_items": {
                        "type": "array",
                        "description": "明細行",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string", "description": "品目名"},
                                "unit_price": {"type": "string", "description": "単価（文字列で指定）"},
                                "quantity": {"type": "string", "description": "数量", "default": "1"},
                            },
                            "required": ["description", "unit_price"],
                        },
                    },
                },
                "required": ["document_type", "client_mid", "date", "line_items"],
            },
        ),
        types.Tool(
            name="send_document",
            description="書類をメールで送付する",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_mid": {"type": "string", "description": "送付する書類のMID"},
                    "recipient_email": {"type": "string", "description": "送付先メールアドレス"},
                    "subject": {"type": "string", "description": "メール件名"},
                    "message": {"type": "string", "description": "メール本文"},
                },
                "required": ["document_mid", "recipient_email"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    global _token_cache
    try:
        client = _client()
    except Exception:
        _token_cache = None
        client = _client()
    mid = _partner_mid()

    if name == "list_clients":
        params: dict = {}
        if arguments.get("search"):
            params["search"] = arguments["search"]
        if arguments.get("archived") is not None:
            params["archived"] = arguments["archived"]
        r = client.get(f"/api/partner/{mid}/client/", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_documents":
        params = {}
        if arguments.get("document_type"):
            params["document_type"] = arguments["document_type"]
        if arguments.get("search"):
            params["search"] = arguments["search"]
        if arguments.get("page"):
            params["page"] = arguments["page"]
        r = client.get(f"/api/partner/{mid}/document/", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_document":
        doc_mid = arguments["document_mid"]
        r = client.get(f"/api/partner/{mid}/document/{doc_mid}/")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "create_document":
        payload: dict = {
            "document_type": arguments["document_type"],
            "client": f"{BASE_URL}/api/partner/{mid}/client/{arguments['client_mid']}/",
            "date": arguments["date"],
            "currency": arguments.get("currency", "JPY"),
            "autocalculate": True,
            "line_items": arguments["line_items"],
        }
        if arguments.get("document_number"):
            payload["document_number"] = arguments["document_number"]
        if arguments.get("due_date"):
            payload["due_date"] = arguments["due_date"]
        if arguments.get("title"):
            payload["title"] = arguments["title"]
        r = client.post(f"/api/partner/{mid}/document/", json=payload)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "send_document":
        doc_mid = arguments["document_mid"]
        doc_url = f"{BASE_URL}/api/partner/{mid}/document/{doc_mid}/"
        order_payload: dict = {
            "recipient_emails": [{"address": arguments["recipient_email"]}],
        }
        if arguments.get("subject"):
            order_payload["subject"] = arguments["subject"]
        if arguments.get("message"):
            order_payload["message"] = arguments["message"]
        order_r = client.post(f"/api/partner/{mid}/sending/order/", json=order_payload)
        order_r.raise_for_status()
        order = order_r.json()
        items_url = order.get("items_url", f"{BASE_URL}/api/partner/{mid}/sending/order/{order['mid']}/item/")
        item_r = client.post(items_url, json={"document": doc_url})
        item_r.raise_for_status()
        send_url = order.get("send_url", f"{BASE_URL}/api/partner/{mid}/sending/order/{order['mid']}/send/")
        send_r = client.post(send_url, json={})
        send_r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(send_r.json(), ensure_ascii=False, indent=2))]

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
