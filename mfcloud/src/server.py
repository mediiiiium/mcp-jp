import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

BASE_URL = "https://invoice.moneyforward.com/api/v3"

app = Server("mfcloud-mcp")


def get_client() -> httpx.Client:
    token = os.environ.get("MFCLOUD_ACCESS_TOKEN")
    if not token:
        raise ValueError("MFCLOUD_ACCESS_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_office",
            description="事業者（自社）情報を取得する",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="list_partners",
            description="取引先一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1〜）", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（最大100）", "default": 50},
                },
            },
        ),
        types.Tool(
            name="create_partner",
            description="取引先を作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "取引先名"},
                    "name_kana": {"type": "string", "description": "取引先名（カナ）"},
                    "zip": {"type": "string", "description": "郵便番号"},
                    "prefecture": {"type": "string", "description": "都道府県"},
                    "address1": {"type": "string", "description": "住所1"},
                    "address2": {"type": "string", "description": "住所2"},
                    "tel": {"type": "string", "description": "電話番号"},
                    "email": {"type": "string", "description": "メールアドレス"},
                    "memo": {"type": "string", "description": "メモ"},
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="list_items",
            description="品目一覧を取得する（請求書明細の品目IDに使う）",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数", "default": 50},
                },
            },
        ),
        types.Tool(
            name="create_item",
            description="品目を作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "品目名"},
                    "unit_price": {"type": "integer", "description": "単価"},
                    "quantity": {"type": "number", "description": "数量", "default": 1},
                    "unit": {"type": "string", "description": "単位（式・個・時間など）"},
                    "detail": {"type": "string", "description": "詳細・備考"},
                    "excise": {
                        "type": "string",
                        "enum": ["non_taxable", "tax_8", "tax_10", "tax_8_reduced"],
                        "description": "税区分",
                    },
                },
                "required": ["name", "unit_price"],
            },
        ),
        types.Tool(
            name="list_billings",
            description="請求書一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数", "default": 50},
                    "billing_date_from": {"type": "string", "description": "請求日（開始）YYYY-MM-DD"},
                    "billing_date_to": {"type": "string", "description": "請求日（終了）YYYY-MM-DD"},
                    "due_date_from": {"type": "string", "description": "支払期日（開始）YYYY-MM-DD"},
                    "due_date_to": {"type": "string", "description": "支払期日（終了）YYYY-MM-DD"},
                    "partner_id": {"type": "string", "description": "取引先ID"},
                    "status": {
                        "type": "string",
                        "enum": ["draft", "unconfirmed", "confirmed", "payment_completed"],
                        "description": "ステータス",
                    },
                },
            },
        ),
        types.Tool(
            name="get_billing",
            description="請求書の詳細を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "請求書ID"},
                },
                "required": ["id"],
            },
        ),
        types.Tool(
            name="create_billing",
            description="請求書を作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "partner_id": {"type": "string", "description": "取引先ID"},
                    "billing_date": {"type": "string", "description": "請求日 YYYY-MM-DD"},
                    "due_date": {"type": "string", "description": "支払期日 YYYY-MM-DD"},
                    "billing_number": {"type": "string", "description": "請求書番号（省略で自動採番）"},
                    "title": {"type": "string", "description": "タイトル"},
                    "memo": {"type": "string", "description": "備考"},
                    "items": {
                        "type": "array",
                        "description": "明細行",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "品目名"},
                                "quantity": {"type": "number", "description": "数量"},
                                "unit_price": {"type": "integer", "description": "単価"},
                                "unit": {"type": "string", "description": "単位"},
                                "detail": {"type": "string", "description": "詳細"},
                                "excise": {
                                    "type": "string",
                                    "enum": ["non_taxable", "tax_8", "tax_10", "tax_8_reduced"],
                                    "description": "税区分",
                                },
                            },
                            "required": ["name", "quantity", "unit_price"],
                        },
                    },
                },
                "required": ["partner_id", "billing_date", "due_date", "items"],
            },
        ),
        types.Tool(
            name="update_billing",
            description="請求書を更新する（下書き状態のみ）",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "請求書ID"},
                    "billing_date": {"type": "string", "description": "請求日 YYYY-MM-DD"},
                    "due_date": {"type": "string", "description": "支払期日 YYYY-MM-DD"},
                    "title": {"type": "string", "description": "タイトル"},
                    "memo": {"type": "string", "description": "備考"},
                },
                "required": ["id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    with get_client() as client:
        if name == "get_office":
            r = client.get("/office")
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "list_partners":
            params = {"page": arguments.get("page", 1), "per_page": arguments.get("per_page", 50)}
            r = client.get("/partners", params=params)
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "create_partner":
            payload: dict = {"name": arguments["name"]}
            for key in ("name_kana", "zip", "prefecture", "address1", "address2", "tel", "email", "memo"):
                if v := arguments.get(key):
                    payload[key] = v
            r = client.post("/partners", json={"partner": payload})
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "list_items":
            params = {"page": arguments.get("page", 1), "per_page": arguments.get("per_page", 50)}
            r = client.get("/items", params=params)
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "create_item":
            payload = {
                "name": arguments["name"],
                "unit_price": arguments["unit_price"],
                "quantity": arguments.get("quantity", 1),
            }
            for key in ("unit", "detail", "excise"):
                if v := arguments.get(key):
                    payload[key] = v
            r = client.post("/items", json={"item": payload})
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "list_billings":
            params = {"page": arguments.get("page", 1), "per_page": arguments.get("per_page", 50)}
            for key in ("billing_date_from", "billing_date_to", "due_date_from", "due_date_to", "partner_id", "status"):
                if v := arguments.get(key):
                    params[key] = v
            r = client.get("/billings", params=params)
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "get_billing":
            r = client.get(f"/billings/{arguments['id']}")
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "create_billing":
            billing: dict = {
                "partner_id": arguments["partner_id"],
                "billing_date": arguments["billing_date"],
                "due_date": arguments["due_date"],
                "items": arguments["items"],
            }
            for key in ("billing_number", "title", "memo"):
                if v := arguments.get(key):
                    billing[key] = v
            r = client.post("/billings", json={"billing": billing})
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "update_billing":
            billing_id = arguments["id"]
            payload: dict = {}
            for key in ("billing_date", "due_date", "title", "memo"):
                if v := arguments.get(key):
                    payload[key] = v
            r = client.patch(f"/billings/{billing_id}", json={"billing": payload})
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        else:
            raise ValueError(f"未知のツール: {name}")


def main():
    import asyncio
    asyncio.run(stdio_server(app))


if __name__ == "__main__":
    main()
