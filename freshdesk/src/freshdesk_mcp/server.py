import os
import base64
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("freshdesk-mcp")


def _client() -> httpx.Client:
    api_key = os.environ.get("FRESHDESK_API_KEY")
    subdomain = os.environ.get("FRESHDESK_SUBDOMAIN")
    if not api_key:
        raise ValueError("FRESHDESK_API_KEY が設定されていません")
    if not subdomain:
        raise ValueError("FRESHDESK_SUBDOMAIN が設定されていません")
    credentials = base64.b64encode(f"{api_key}:X".encode()).decode()
    return httpx.Client(
        base_url=f"https://{subdomain}.freshdesk.com/api/v2",
        headers={"Authorization": f"Basic {credentials}", "Content-Type": "application/json"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_tickets",
            description=(
                "チケット一覧をページ単位で取得する。既定では作成日時の新しい順（order_by=created_at, "
                "order_type=desc）に並び、直近30日以内に作成されたチケットのみが対象となる（Freshdesk API の"
                "仕様）。それより古いチケットも含めたい場合は updated_since に ISO 8601 形式の日時を指定する。"
                "ページングは page 番号方式（1始まり）で、per_page は最大100件・既定30件。全体で最大300ページ"
                "（30000件）までしか取得できない。status・priority は本ツールの引数として受け付けるが、"
                "Freshdesk公式ドキュメントの一覧APIパラメータには含まれておらず、API側で無視され結果に反映"
                "されない可能性がある点に注意（確実に絞り込みたい場合は取得後にクライアント側でフィルタするか、"
                "本コネクタが未実装の検索API [/api/v2/search/tickets] を利用する必要がある）。公式に文書化"
                "されている絞り込みは filter・requester_id・email・company_id・updated_since。1件の詳細を"
                "見たい場合は get_ticket を使う。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "integer",
                        "description": (
                            "ステータス: 2=Open, 3=Pending, 4=Resolved, 5=Closed。"
                            "注意: Freshdesk公式ドキュメントには一覧APIの絞り込みパラメータとして記載がなく、"
                            "API側で無視される可能性がある"
                        ),
                    },
                    "priority": {
                        "type": "integer",
                        "description": (
                            "優先度: 1=Low, 2=Medium, 3=High, 4=Urgent。"
                            "注意: Freshdesk公式ドキュメントには一覧APIの絞り込みパラメータとして記載がなく、"
                            "API側で無視される可能性がある"
                        ),
                    },
                    "filter": {
                        "type": "string",
                        "enum": ["new_and_my_open", "watching", "spam", "deleted"],
                        "description": (
                            "Freshdesk側の定義済みビューで絞り込む。deleted を指定するとソフト削除済みチケットのみ"
                            "が返る（既定では削除済みチケットは一覧に含まれない）"
                        ),
                    },
                    "requester_id": {"type": "integer", "description": "この問い合わせ者IDが起票したチケットのみに絞り込む"},
                    "email": {"type": "string", "description": "この問い合わせ者メールアドレスが起票したチケットのみに絞り込む"},
                    "company_id": {"type": "integer", "description": "この会社IDに紐づくチケットのみに絞り込む"},
                    "updated_since": {
                        "type": "string",
                        "description": (
                            "この日時（ISO 8601形式、例: 2026-06-01T00:00:00Z）以降に更新されたチケットのみを取得。"
                            "既定の「直近30日以内」の制限を超えて古いチケットを取得したい場合にも使う"
                        ),
                    },
                    "order_by": {
                        "type": "string",
                        "enum": ["created_at", "due_by", "updated_at", "status"],
                        "description": "並び替えの基準列（既定 created_at）",
                    },
                    "order_type": {
                        "type": "string",
                        "enum": ["asc", "desc"],
                        "description": "並び順（既定 desc=新しい順）",
                    },
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（最大100、既定30）", "default": 30},
                    "page": {"type": "integer", "description": "ページ番号（1始まり、既定1）。続きは page を+1して呼び出す", "default": 1},
                },
            },
        ),
        types.Tool(
            name="get_ticket",
            description=(
                "チケットIDを指定して1件の詳細を取得する。一覧から対象を絞り込んだ後、本文や会話履歴など"
                "詳細情報を見たい場合に使う。include で会話（conversations）・問い合わせ者情報（requester）・"
                "会社情報（company）・統計情報（stats: closed_at/resolved_at/first_responded_at）を追加取得できる"
                "が、それぞれ1〜2APIクレジットを消費する（conversationsは2クレジット、他は1クレジットずつ加算）。"
                "conversationsを含めても直近10件までしか返らない。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "integer", "description": "チケットID"},
                    "include": {
                        "type": "string",
                        "description": (
                            "追加取得する情報をカンマ区切りで指定（conversations, requester, company, stats）。"
                            "1つ追加するごとにAPIクレジットを消費するため必要な項目のみ指定する"
                        ),
                    },
                },
                "required": ["ticket_id"],
            },
        ),
        types.Tool(
            name="create_ticket",
            description=(
                "新しいチケットを1件作成する（POST）。呼び出すたびに新規チケットが作成され、重複防止の"
                "冪等性キーのような仕組みはFreshdesk側に存在しないため、同じ内容で複数回呼び出すと重複チケットが"
                "できる点に注意（べき等ではない）。省略時、status は 2=Open、priority は 1=Low になる"
                "（Freshdesk API既定値）。添付ファイルはこのツールでは扱わない（Freshdesk側はmultipart/form-data"
                "でのアップロードが必要なため未対応）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "subject": {"type": "string", "description": "チケットの件名"},
                    "description": {"type": "string", "description": "チケットの内容（HTML可）"},
                    "email": {"type": "string", "description": "問い合わせ元のメールアドレス（requester_idの代わりに指定する起票者の識別方法）"},
                    "priority": {"type": "integer", "description": "優先度: 1=Low, 2=Medium, 3=High, 4=Urgent（省略時 1=Low）", "default": 1},
                    "status": {"type": "integer", "description": "ステータス: 2=Open, 3=Pending, 4=Resolved, 5=Closed（省略時 2=Open）", "default": 2},
                    "type": {"type": "string", "description": "チケット種別（例: Question, Incident, Problem, Feature Request。アカウントのカスタム設定に依存）"},
                    "group_id": {"type": "integer", "description": "割り当て先グループID"},
                    "responder_id": {"type": "integer", "description": "担当エージェントID"},
                    "cc_emails": {"type": "array", "items": {"type": "string"}, "description": "CCに含めるメールアドレスのリスト"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "タグ一覧"},
                },
                "required": ["subject", "description", "email"],
            },
        ),
        types.Tool(
            name="delete_ticket",
            description=(
                "チケットを1件削除する（ソフトデリート）。削除後は通常の一覧からは見えなくなるが、"
                "list_tickets を filter=deleted で呼び出すと確認できる（Freshdesk側はデータを完全には消さず、"
                "/api/v2/tickets/{id}/restore で復元できる仕様だが、復元用ツールは本コネクタには実装していない）。"
                "既に削除済み・存在しないチケットIDに対して再度呼び出した場合の挙動はFreshdesk側の実装に依存する"
                "ため、事前に get_ticket で存在確認してから呼び出すことを推奨する。この操作は元に戻せない可能性が"
                "あるため注意して使うこと。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "integer", "description": "削除するチケットID"},
                },
                "required": ["ticket_id"],
            },
        ),
        types.Tool(
            name="list_contacts",
            description=(
                "コンタクト（問い合わせ者・顧客）の一覧をページ単位で取得する。email・mobile・phone・company_id・"
                "state・updated_since で絞り込める（複数指定した場合はAND条件）。ページングは page 番号方式"
                "（1始まり）で、per_page は最大100件・既定30件。エージェント一覧・会社一覧はこのツールでは"
                "取得できない（別エンドポイント）。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "メールアドレスで絞り込む"},
                    "mobile": {"type": "string", "description": "携帯電話番号で絞り込む"},
                    "phone": {"type": "string", "description": "電話番号で絞り込む"},
                    "company_id": {"type": "integer", "description": "この会社IDに所属するコンタクトのみに絞り込む"},
                    "state": {
                        "type": "string",
                        "enum": ["verified", "unverified", "blocked", "deleted"],
                        "description": "コンタクトの状態で絞り込む",
                    },
                    "updated_since": {"type": "string", "description": "この日時（ISO 8601形式）以降に更新されたコンタクトのみを取得"},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（最大100、既定30）", "default": 30},
                    "page": {"type": "integer", "description": "ページ番号（1始まり、既定1）", "default": 1},
                },
            },
        ),
        types.Tool(
            name="get_contact",
            description=(
                "コンタクトIDを指定して1件の詳細を取得する。一覧で見つけた対象のカスタムフィールドや会社所属など"
                "詳細情報を確認したい場合に使う。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "integer", "description": "コンタクトID"},
                },
                "required": ["contact_id"],
            },
        ),
        types.Tool(
            name="delete_contact",
            description=(
                "コンタクトを1件削除する（ソフトデリート）。削除後はブロック状態のコンタクトと同様に扱われ、"
                "通常の一覧・チケット起票には使えなくなるが、データは完全には消えない。Freshdesk APIには恒久的に"
                "完全削除する /api/v2/contacts/{id}/hard_delete エンドポイントも存在するが、誤操作時に復元できず"
                "リスクが高いため本コネクタでは実装していない（ソフトデリートのみ提供）。既に削除済み・存在しない"
                "コンタクトIDに対して再度呼び出した場合の挙動はFreshdesk側の実装に依存するため、事前に "
                "get_contact で存在確認してから呼び出すことを推奨する。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "integer", "description": "削除するコンタクトID"},
                },
                "required": ["contact_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_tickets":
                params = {
                    "per_page": arguments.get("per_page", 30),
                    "page": arguments.get("page", 1),
                }
                if arguments.get("status"):
                    params["status"] = arguments["status"]
                if arguments.get("priority"):
                    params["priority"] = arguments["priority"]
                if arguments.get("filter"):
                    params["filter"] = arguments["filter"]
                if arguments.get("requester_id"):
                    params["requester_id"] = arguments["requester_id"]
                if arguments.get("email"):
                    params["email"] = arguments["email"]
                if arguments.get("company_id"):
                    params["company_id"] = arguments["company_id"]
                if arguments.get("updated_since"):
                    params["updated_since"] = arguments["updated_since"]
                if arguments.get("order_by"):
                    params["order_by"] = arguments["order_by"]
                if arguments.get("order_type"):
                    params["order_type"] = arguments["order_type"]
                r = client.get("/tickets", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_ticket":
                ticket_id = arguments["ticket_id"]
                params = {}
                if arguments.get("include"):
                    params["include"] = arguments["include"]
                r = client.get(f"/tickets/{ticket_id}", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "create_ticket":
                payload = {
                    "subject": arguments["subject"],
                    "description": arguments["description"],
                    "email": arguments["email"],
                    "priority": arguments.get("priority", 1),
                    "status": arguments.get("status", 2),
                }
                if arguments.get("type"):
                    payload["type"] = arguments["type"]
                if arguments.get("group_id"):
                    payload["group_id"] = arguments["group_id"]
                if arguments.get("responder_id"):
                    payload["responder_id"] = arguments["responder_id"]
                if arguments.get("cc_emails"):
                    payload["cc_emails"] = arguments["cc_emails"]
                if arguments.get("tags"):
                    payload["tags"] = arguments["tags"]
                r = client.post("/tickets", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "delete_ticket":
                ticket_id = arguments["ticket_id"]
                r = client.delete(f"/tickets/{ticket_id}")
                r.raise_for_status()
                if r.status_code == 204 or not r.content:
                    return format_response({"deleted": True, "ticket_id": ticket_id})
                return format_response(r.json())

            elif name == "list_contacts":
                params = {
                    "per_page": arguments.get("per_page", 30),
                    "page": arguments.get("page", 1),
                }
                if arguments.get("email"):
                    params["email"] = arguments["email"]
                if arguments.get("mobile"):
                    params["mobile"] = arguments["mobile"]
                if arguments.get("phone"):
                    params["phone"] = arguments["phone"]
                if arguments.get("company_id"):
                    params["company_id"] = arguments["company_id"]
                if arguments.get("state"):
                    params["state"] = arguments["state"]
                if arguments.get("updated_since"):
                    params["updated_since"] = arguments["updated_since"]
                r = client.get("/contacts", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_contact":
                contact_id = arguments["contact_id"]
                r = client.get(f"/contacts/{contact_id}")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "delete_contact":
                contact_id = arguments["contact_id"]
                r = client.delete(f"/contacts/{contact_id}")
                r.raise_for_status()
                if r.status_code == 204 or not r.content:
                    return format_response({"deleted": True, "contact_id": contact_id})
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
