import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("hubspot-mcp")

BASE_URL = "https://api.hubapi.com"

CONTACT_PROPS = ["firstname", "lastname", "email", "phone", "company", "jobtitle", "lifecyclestage", "createdate", "lastmodifieddate"]
DEAL_PROPS = ["dealname", "amount", "dealstage", "closedate", "pipeline", "hs_deal_stage_probability", "createdate"]
COMPANY_PROPS = ["name", "domain", "industry", "phone", "city", "country", "numberofemployees", "annualrevenue"]


def _client() -> httpx.Client:
    token = os.environ.get("HUBSPOT_ACCESS_TOKEN")
    if not token:
        raise ValueError("HUBSPOT_ACCESS_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="search_contacts",
            description="HubSpot CRM のコンタクト（連絡先）を名前・メール・会社名で検索する",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "検索キーワード（名前・メールアドレス・会社名等）",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "取得件数（最大100、デフォルト20）",
                        "default": 20,
                    },
                    "after": {
                        "type": "string",
                        "description": "ページネーション用カーソル（レスポンスの paging.next.after から取得）",
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="get_contact",
            description="コンタクトIDを指定して詳細情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {
                        "type": "string",
                        "description": "コンタクトID",
                    },
                },
                "required": ["contact_id"],
            },
        ),
        types.Tool(
            name="create_contact",
            description="HubSpot CRM に新しいコンタクトを作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "メールアドレス（推奨。重複チェックキー）",
                    },
                    "firstname": {
                        "type": "string",
                        "description": "名（ファーストネーム）",
                    },
                    "lastname": {
                        "type": "string",
                        "description": "姓（ラストネーム）",
                    },
                    "phone": {
                        "type": "string",
                        "description": "電話番号",
                    },
                    "company": {
                        "type": "string",
                        "description": "会社名",
                    },
                    "jobtitle": {
                        "type": "string",
                        "description": "役職",
                    },
                },
            },
        ),
        types.Tool(
            name="list_deals",
            description="HubSpot CRM の商談（ディール）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "取得件数（最大100、デフォルト20）",
                        "default": 20,
                    },
                    "after": {
                        "type": "string",
                        "description": "ページネーション用カーソル",
                    },
                    "archived": {
                        "type": "boolean",
                        "description": "アーカイブ済みを含めるか（デフォルト: false）",
                        "default": False,
                    },
                },
            },
        ),
        types.Tool(
            name="create_deal",
            description="HubSpot CRM に新しい商談（ディール）を作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "dealname": {
                        "type": "string",
                        "description": "商談名",
                    },
                    "amount": {
                        "type": "string",
                        "description": "金額（数値を文字列で指定、例: '100000'）",
                    },
                    "dealstage": {
                        "type": "string",
                        "description": "商談ステージ（例: appointmentscheduled, qualifiedtobuy, presentationscheduled, decisionmakerboughtin, contractsent, closedwon, closedlost）",
                    },
                    "closedate": {
                        "type": "string",
                        "description": "クローズ予定日（Unix ミリ秒タイムスタンプ、例: '1735689600000'）",
                    },
                    "pipeline": {
                        "type": "string",
                        "description": "パイプライン名（例: default）",
                        "default": "default",
                    },
                },
                "required": ["dealname"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "search_contacts":
        body: dict = {
            "query": arguments["query"],
            "limit": arguments.get("limit", 20),
            "properties": CONTACT_PROPS,
        }
        if arguments.get("after"):
            body["after"] = arguments["after"]
        r = client.post("/crm/v3/objects/contacts/search", content=json.dumps(body))
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_contact":
        cid = arguments["contact_id"]
        params = {"properties": ",".join(CONTACT_PROPS)}
        r = client.get(f"/crm/v3/objects/contacts/{cid}", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "create_contact":
        props: dict = {}
        for field in ["email", "firstname", "lastname", "phone", "company", "jobtitle"]:
            if arguments.get(field):
                props[field] = arguments[field]
        r = client.post("/crm/v3/objects/contacts", content=json.dumps({"properties": props}))
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_deals":
        params: dict = {
            "limit": arguments.get("limit", 20),
            "properties": ",".join(DEAL_PROPS),
            "archived": str(arguments.get("archived", False)).lower(),
        }
        if arguments.get("after"):
            params["after"] = arguments["after"]
        r = client.get("/crm/v3/objects/deals", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "create_deal":
        props = {"dealname": arguments["dealname"], "pipeline": arguments.get("pipeline", "default")}
        if arguments.get("amount"):
            props["amount"] = arguments["amount"]
        if arguments.get("dealstage"):
            props["dealstage"] = arguments["dealstage"]
        if arguments.get("closedate"):
            props["closedate"] = arguments["closedate"]
        r = client.post("/crm/v3/objects/deals", content=json.dumps({"properties": props}))
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
