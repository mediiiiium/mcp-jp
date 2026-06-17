import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

BASE_URL = "https://api.freee.co.jp"

app = Server("freee-mcp")


def get_client() -> httpx.Client:
    token = os.environ.get("FREEE_ACCESS_TOKEN")
    if not token:
        raise ValueError("FREEE_ACCESS_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )


def company_id() -> int:
    cid = os.environ.get("FREEE_COMPANY_ID")
    if not cid:
        raise ValueError("FREEE_COMPANY_ID が設定されていません")
    return int(cid)


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_companies",
            description="freeeの事業所一覧を取得する（FREEE_COMPANY_ID確認にも使う）",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="list_deals",
            description="取引（収入・支出）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["income", "expense"],
                        "description": "取引種別（income=収入 / expense=支出）",
                    },
                    "partner_id": {"type": "integer", "description": "取引先ID"},
                    "start_issue_date": {"type": "string", "description": "発生日（開始）YYYY-MM-DD"},
                    "end_issue_date": {"type": "string", "description": "発生日（終了）YYYY-MM-DD"},
                    "limit": {"type": "integer", "description": "取得件数（最大100）", "default": 50},
                    "offset": {"type": "integer", "description": "オフセット", "default": 0},
                },
            },
        ),
        types.Tool(
            name="get_deal",
            description="取引の詳細を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "description": "取引ID"},
                },
                "required": ["id"],
            },
        ),
        types.Tool(
            name="create_deal",
            description="取引（収入・支出）を作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_date": {"type": "string", "description": "発生日 YYYY-MM-DD"},
                    "type": {
                        "type": "string",
                        "enum": ["income", "expense"],
                        "description": "収入 or 支出",
                    },
                    "amount": {"type": "integer", "description": "金額（税込）"},
                    "due_date": {"type": "string", "description": "支払期日 YYYY-MM-DD"},
                    "partner_id": {"type": "integer", "description": "取引先ID"},
                    "account_item_id": {"type": "integer", "description": "勘定科目ID"},
                    "tax_code": {"type": "integer", "description": "税区分コード"},
                    "description": {"type": "string", "description": "備考"},
                },
                "required": ["issue_date", "type", "amount", "account_item_id", "tax_code"],
            },
        ),
        types.Tool(
            name="list_invoices",
            description="請求書一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "partner_id": {"type": "integer", "description": "取引先ID"},
                    "invoice_status": {
                        "type": "string",
                        "enum": ["draft", "applying", "remanded", "rejected", "approved", "deleted", "issued"],
                        "description": "請求書ステータス",
                    },
                    "start_issue_date": {"type": "string", "description": "請求日（開始）YYYY-MM-DD"},
                    "end_issue_date": {"type": "string", "description": "請求日（終了）YYYY-MM-DD"},
                    "limit": {"type": "integer", "description": "取得件数（最大100）", "default": 50},
                    "offset": {"type": "integer", "description": "オフセット", "default": 0},
                },
            },
        ),
        types.Tool(
            name="create_invoice",
            description="請求書を作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "partner_id": {"type": "integer", "description": "取引先ID"},
                    "issue_date": {"type": "string", "description": "請求日 YYYY-MM-DD"},
                    "due_date": {"type": "string", "description": "支払期日 YYYY-MM-DD"},
                    "invoice_number": {"type": "string", "description": "請求書番号（省略で自動採番）"},
                    "title": {"type": "string", "description": "タイトル"},
                    "description": {"type": "string", "description": "備考"},
                    "invoice_lines": {
                        "type": "array",
                        "description": "明細行",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "品目名"},
                                "quantity": {"type": "number", "description": "数量"},
                                "unit_price": {"type": "integer", "description": "単価"},
                                "account_item_id": {"type": "integer", "description": "勘定科目ID"},
                                "tax_code": {"type": "integer", "description": "税区分コード"},
                            },
                            "required": ["name", "quantity", "unit_price", "account_item_id", "tax_code"],
                        },
                    },
                },
                "required": ["partner_id", "issue_date", "due_date", "invoice_lines"],
            },
        ),
        types.Tool(
            name="list_partners",
            description="取引先一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "取引先名で絞り込み（部分一致）"},
                    "limit": {"type": "integer", "description": "取得件数（最大100）", "default": 50},
                    "offset": {"type": "integer", "description": "オフセット", "default": 0},
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
                    "shortcut1": {"type": "string", "description": "ショートカット1"},
                    "long_name": {"type": "string", "description": "正式名称"},
                    "name_kana": {"type": "string", "description": "フリガナ"},
                    "phone": {"type": "string", "description": "電話番号"},
                    "email": {"type": "string", "description": "メールアドレス"},
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="list_account_items",
            description="勘定科目一覧を取得する（取引作成時のaccount_item_id確認に使う）",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_category": {
                        "type": "string",
                        "description": "勘定科目カテゴリ（例: Assets/Liabilities/Equity/Income/Expense）",
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    cid = company_id()
    with get_client() as client:
        if name == "list_companies":
            r = client.get("/api/1/companies")
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "list_deals":
            params = {"company_id": cid, "limit": arguments.get("limit", 50), "offset": arguments.get("offset", 0)}
            for key in ("type", "partner_id", "start_issue_date", "end_issue_date"):
                if v := arguments.get(key):
                    params[key] = v
            r = client.get("/api/1/deals", params=params)
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "get_deal":
            r = client.get(f"/api/1/deals/{arguments['id']}", params={"company_id": cid})
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "create_deal":
            payload = {
                "company_id": cid,
                "issue_date": arguments["issue_date"],
                "type": arguments["type"],
                "details": [
                    {
                        "account_item_id": arguments["account_item_id"],
                        "tax_code": arguments["tax_code"],
                        "amount": arguments["amount"],
                        "description": arguments.get("description", ""),
                    }
                ],
            }
            for key in ("due_date", "partner_id"):
                if v := arguments.get(key):
                    payload[key] = v
            r = client.post("/api/1/deals", json=payload)
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "list_invoices":
            params = {"company_id": cid, "limit": arguments.get("limit", 50), "offset": arguments.get("offset", 0)}
            for key in ("partner_id", "invoice_status", "start_issue_date", "end_issue_date"):
                if v := arguments.get(key):
                    params[key] = v
            r = client.get("/api/1/invoices", params=params)
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "create_invoice":
            payload = {
                "company_id": cid,
                "partner_id": arguments["partner_id"],
                "issue_date": arguments["issue_date"],
                "due_date": arguments["due_date"],
                "invoice_lines": arguments["invoice_lines"],
            }
            for key in ("invoice_number", "title", "description"):
                if v := arguments.get(key):
                    payload[key] = v
            r = client.post("/api/1/invoices", json=payload)
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "list_partners":
            params = {"company_id": cid, "limit": arguments.get("limit", 50), "offset": arguments.get("offset", 0)}
            if name_q := arguments.get("name"):
                params["name"] = name_q
            r = client.get("/api/1/partners", params=params)
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "create_partner":
            payload = {"company_id": cid, "name": arguments["name"]}
            for key in ("shortcut1", "long_name", "name_kana", "phone", "email"):
                if v := arguments.get(key):
                    payload[key] = v
            r = client.post("/api/1/partners", json=payload)
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        elif name == "list_account_items":
            params: dict = {"company_id": cid}
            if cat := arguments.get("account_category"):
                params["account_category"] = cat
            r = client.get("/api/1/account_items", params=params)
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        else:
            raise ValueError(f"未知のツール: {name}")


def main():
    import asyncio
    asyncio.run(stdio_server(app))


if __name__ == "__main__":
    main()
