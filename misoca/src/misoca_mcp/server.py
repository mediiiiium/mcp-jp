import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("misoca-mcp")
BASE_URL = "https://app.misoca.jp/api/v3"


def _client() -> httpx.Client:
    access_token = os.environ.get("MISOCA_ACCESS_TOKEN")
    if not access_token:
        raise ValueError("MISOCA_ACCESS_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_invoices",
            description="請求書一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（最大100）", "default": 20},
                    "sent_at_from": {"type": "string", "description": "送付日（開始）YYYY-MM-DD"},
                    "sent_at_to": {"type": "string", "description": "送付日（終了）YYYY-MM-DD"},
                    "contact_id": {"type": "integer", "description": "取引先IDで絞り込み"},
                },
            },
        ),
        types.Tool(
            name="get_invoice",
            description="請求書の詳細情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_id": {"type": "integer", "description": "請求書ID"},
                },
                "required": ["invoice_id"],
            },
        ),
        types.Tool(
            name="create_invoice",
            description="新しい請求書を作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "integer", "description": "取引先ID"},
                    "title": {"type": "string", "description": "件名"},
                    "issue_date": {"type": "string", "description": "発行日（YYYY-MM-DD）"},
                    "due_date": {"type": "string", "description": "支払期限（YYYY-MM-DD）"},
                    "items": {
                        "type": "array",
                        "description": "請求明細リスト",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "品目名"},
                                "unit_price": {"type": "integer", "description": "単価"},
                                "quantity": {"type": "number", "description": "数量", "default": 1},
                                "tax_type": {"type": "string", "description": "税区分（taxable_10: 10%課税、taxable_8: 8%課税、tax_free: 非課税）", "default": "taxable_10"},
                            },
                            "required": ["name", "unit_price"],
                        },
                    },
                },
                "required": ["contact_id", "title", "issue_date"],
            },
        ),
        types.Tool(
            name="mark_invoice_paid",
            description="請求書を入金済みにする",
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_id": {"type": "integer", "description": "請求書ID"},
                    "paid_at": {"type": "string", "description": "入金日（YYYY-MM-DD）。省略時は今日の日付"},
                },
                "required": ["invoice_id"],
            },
        ),
        types.Tool(
            name="list_contacts",
            description="取引先一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数", "default": 20},
                    "name": {"type": "string", "description": "取引先名で絞り込み"},
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_invoices":
                params: dict = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 20),
                }
                if arguments.get("sent_at_from"):
                    params["sent_at_from"] = arguments["sent_at_from"]
                if arguments.get("sent_at_to"):
                    params["sent_at_to"] = arguments["sent_at_to"]
                if arguments.get("contact_id"):
                    params["contact_id"] = arguments["contact_id"]
                r = client.get("/invoices", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_invoice":
                r = client.get(f"/invoice/{arguments['invoice_id']}")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "create_invoice":
                payload: dict = {
                    "contact_id": arguments["contact_id"],
                    "title": arguments["title"],
                    "issue_date": arguments["issue_date"],
                }
                if arguments.get("due_date"):
                    payload["due_date"] = arguments["due_date"]
                if arguments.get("items"):
                    payload["items"] = arguments["items"]
                r = client.post("/invoice", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "mark_invoice_paid":
                payload = {}
                if arguments.get("paid_at"):
                    payload["paid_at"] = arguments["paid_at"]
                r = client.put(f"/invoice/{arguments['invoice_id']}/paid", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_contacts":
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 20),
                }
                if arguments.get("name"):
                    params["name"] = arguments["name"]
                r = client.get("/contacts", params=params)
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
