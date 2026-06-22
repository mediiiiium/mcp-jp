import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("invox-mcp")

BASE_URL = "https://api.invox.jp/api/public"


def _client() -> httpx.Client:
    token = os.environ.get("INVOX_ACCESS_TOKEN")
    company_code = os.environ.get("INVOX_COMPANY_CODE")
    if not token:
        raise ValueError("INVOX_ACCESS_TOKEN が設定されていません")
    if not company_code:
        raise ValueError("INVOX_COMPANY_CODE が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        # invox_company_code はすべてのリクエストで必須
        params={"invox_company_code": company_code},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_received_invoices",
            description="受取請求書の一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり）", "default": 1},
                    "status": {
                        "type": "string",
                        "description": "ステータスで絞り込み（例: 未確認、確認済、申請中、承認済）",
                    },
                    "issue_date_from": {"type": "string", "description": "発行日（開始）YYYY-MM-DD"},
                    "issue_date_to": {"type": "string", "description": "発行日（終了）YYYY-MM-DD"},
                    "supplier_name": {"type": "string", "description": "仕入先名で絞り込み（部分一致）"},
                },
            },
        ),
        types.Tool(
            name="get_received_invoice",
            description="受取請求書の詳細情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_id": {"type": "string", "description": "請求書ID"},
                },
                "required": ["invoice_id"],
            },
        ),
        types.Tool(
            name="approve_received_invoice",
            description="受取請求書のワークフロー申請を承認する",
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_id": {"type": "string", "description": "承認する請求書ID"},
                    "comment": {"type": "string", "description": "承認コメント"},
                },
                "required": ["invoice_id"],
            },
        ),
        types.Tool(
            name="list_suppliers",
            description="仕入先（取引先）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり）", "default": 1},
                    "name": {"type": "string", "description": "仕入先名で絞り込み（部分一致）"},
                },
            },
        ),
        types.Tool(
            name="export_journal",
            description="受取請求書の仕訳データをエクスポートする",
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "エクスポートする請求書IDのリスト",
                    },
                    "accounting_software": {
                        "type": "string",
                        "description": "会計ソフト種別（例: freee、マネーフォワード、弥生会計）",
                    },
                },
                "required": ["invoice_ids"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_received_invoices":
                params: dict = {"page": arguments.get("page", 1)}
                if arguments.get("status"):
                    params["status"] = arguments["status"]
                if arguments.get("issue_date_from"):
                    params["issue_date_from"] = arguments["issue_date_from"]
                if arguments.get("issue_date_to"):
                    params["issue_date_to"] = arguments["issue_date_to"]
                if arguments.get("supplier_name"):
                    params["supplier_name"] = arguments["supplier_name"]
                r = client.get("/invoice_receive/invoice/list", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_received_invoice":
                r = client.get("/invoice_receive/invoice/get", params={"invoice_id": arguments["invoice_id"]})
                r.raise_for_status()
                return format_response(r.json())

            elif name == "approve_received_invoice":
                payload: dict = {"invoice_id": arguments["invoice_id"]}
                if arguments.get("comment"):
                    payload["comment"] = arguments["comment"]
                r = client.post("/invoice_receive/invoice/approve", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_suppliers":
                params = {"page": arguments.get("page", 1)}
                if arguments.get("name"):
                    params["name"] = arguments["name"]
                r = client.get("/invoice_receive/supplier/list", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "export_journal":
                payload = {"invoice_ids": arguments["invoice_ids"]}
                if arguments.get("accounting_software"):
                    payload["accounting_software"] = arguments["accounting_software"]
                r = client.post("/invoice_receive/invoice/journal/export", json=payload)
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
