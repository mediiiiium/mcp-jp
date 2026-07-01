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
        # ── 請求書 ──
        types.Tool(
            name="list_invoices",
            description=(
                "請求書一覧を取得する。既定では type=active（ごみ箱・処理済を除く未処理のみ）を、作成日時の新しい順"
                "（order_by=created_at, order=desc）で返す。請求日（from/to）・支払期限（due_date_from/to）・"
                "更新日（updated_at_from/to）の範囲、入金ステータス（payment_status）、請求ステータス"
                "（invoice_status）、取引先ID（contact_group_id。list_contact_groups で取得できる取引先＝顧客企業の"
                "ID。請求書の宛先である「送り先」IDとは別物）、キーワード（condition：請求書番号・取引先名・件名・"
                "社内メモを対象に部分一致）で絞り込める。日付は YYYY/MM/DD 形式。ページングは page/per_page"
                "（省略時 page=1, per_page=25。per_page の上限は100）。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（省略時1）"},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（1〜100、省略時25）"},
                    "type": {
                        "type": "string",
                        "enum": ["active", "archived", "trashed", "untrashed"],
                        "description": "取得する請求書の種類（active: 未処理[既定] / archived: 処理済 / trashed: ごみ箱 / untrashed: 未処理と処理済）",
                    },
                    "from": {"type": "string", "description": "請求日（発行日）の範囲開始。YYYY/MM/DD形式"},
                    "to": {"type": "string", "description": "請求日（発行日）の範囲終了。YYYY/MM/DD形式"},
                    "due_date_from": {"type": "string", "description": "支払期限の範囲開始。YYYY/MM/DD形式"},
                    "due_date_to": {"type": "string", "description": "支払期限の範囲終了。YYYY/MM/DD形式"},
                    "updated_at_from": {"type": "string", "description": "更新日の範囲開始。YYYY/MM/DD形式"},
                    "updated_at_to": {"type": "string", "description": "更新日の範囲終了。YYYY/MM/DD形式"},
                    "payment_status": {
                        "type": "string",
                        "enum": ["paid", "unpaid"],
                        "description": "入金ステータスで絞り込む（paid: 入金済 / unpaid: 未入金）",
                    },
                    "invoice_status": {
                        "type": "string",
                        "enum": ["submitted", "unsubmitted"],
                        "description": "請求ステータスで絞り込む（submitted: 請求済 / unsubmitted: 未請求）",
                    },
                    "contact_group_id": {"type": "integer", "description": "取引先（顧客企業）IDで絞り込む。list_contact_groups で取得"},
                    "condition": {"type": "string", "description": "請求書番号・取引先名・件名・社内メモに含まれるキーワードで検索"},
                    "order": {"type": "string", "enum": ["asc", "desc"], "description": "並び順（既定 desc=降順）"},
                    "order_by": {
                        "type": "string",
                        "enum": ["created_at", "updated_at", "issue_date", "payment_due_on"],
                        "description": "並び替えの基準項目（既定 created_at=作成日）",
                    },
                },
            },
        ),
        types.Tool(
            name="get_invoice",
            description=(
                "請求書1件の詳細（明細行・金額内訳・入金/請求ステータス・宛先情報など）を取得する。"
                "invoice_id は list_invoices のレスポンスに含まれる id を指定する。"
            ),
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
            description=(
                "新しい請求書を作成する。issue_date（発行日）と contact_id が必須。contact_id は「送り先」"
                "（list_contacts で取得できるID）であり、取引先そのもののID（list_contact_groups の id）とは異なる"
                "点に注意。作成直後は未請求・未入金の状態で、請求済みにするには別途 mark_invoice_submitted、"
                "入金済みにするには mark_invoice_paid を呼ぶ必要がある（本APIが自動でステータスを変えることはない）。"
                "呼び出すたびに新しい請求書が作成されるため、べき等ではない（二重送信に注意）。"
                "items[].tax_type は 'STANDARD_TAX_10'（10%課税）/ 'STANDARD_TAX_8'（8%課税）/ "
                "'REDUCED_TAX_8'（軽減税率8%）/ 'STANDARD_TAX_5'（5%課税）/ 'EXEMPTED_TAX'（対象外）のいずれか。"
                "自社情報・消費税表示方法・源泉徴収税設定・振込先などを個別指定したい場合は body オブジェクトに"
                "Misoca API v3 ドキュメントの postInvoice.body 定義に従ったフィールドをそのまま渡せる"
                "（省略時は取引先・自社設定の既定値が使われる）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "integer", "description": "送り先ID（list_contacts で取得。取引先IDではない）"},
                    "issue_date": {"type": "string", "description": "発行日（YYYY-MM-DD）"},
                    "invoice_number": {"type": "string", "description": "請求書番号（省略可）"},
                    "subject": {"type": "string", "description": "件名（省略可）"},
                    "payment_due_on": {"type": "string", "description": "支払期限（YYYY-MM-DD、省略可）"},
                    "body": {
                        "type": "object",
                        "description": (
                            "自社情報・消費税表示（tax_option）・端数処理（tax_rounding_policy）・源泉徴収税設定"
                            "（withholding_tax_type）・振込先（bank_accounts）などの追加設定。省略可（未指定項目は"
                            "取引先・自社の既定値が使われる）"
                        ),
                    },
                    "items": {
                        "type": "array",
                        "description": "請求明細リスト（省略した場合、明細のない請求書になる）",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "品目名"},
                                "unit_price": {"type": "number", "description": "単価"},
                                "quantity": {"type": "number", "description": "数量（省略時1）"},
                                "unit_name": {"type": "string", "description": "単位（例: 個、時間）。省略可"},
                                "transaction_date": {"type": "string", "description": "納品日（YYYY-MM-DD）。省略可"},
                                "tax_type": {
                                    "type": "string",
                                    "enum": ["STANDARD_TAX_10", "STANDARD_TAX_8", "REDUCED_TAX_8", "STANDARD_TAX_5", "EXEMPTED_TAX"],
                                    "description": "消費税区分（省略時は取引先・自社の既定設定に従う）",
                                },
                                "excluding_withholding_tax": {"type": "boolean", "description": "この明細を源泉徴収税の対象外にする場合true（省略時false）"},
                            },
                            "required": ["name", "unit_price"],
                        },
                    },
                },
                "required": ["contact_id", "issue_date"],
            },
        ),
        types.Tool(
            name="mark_invoice_paid",
            description=(
                "請求書を入金済みにする（PUT /invoice/{id}/paid）。入金日 paid_on を省略した場合、その請求書に"
                "支払期限が設定されていればそれを入金日として扱い、支払期限も未設定なら入金日は設定されない"
                "（「今日の日付」が使われるわけではない点に注意）。既に入金済みの請求書に対して再実行しても"
                "状態は変わらずべき等。取り消すには mark_invoice_unpaid を使う。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_id": {"type": "integer", "description": "請求書ID"},
                    "paid_on": {"type": "string", "description": "入金日（YYYY-MM-DD）。省略時の挙動は上記説明を参照"},
                },
                "required": ["invoice_id"],
            },
        ),
        types.Tool(
            name="mark_invoice_unpaid",
            description=(
                "請求書を未入金の状態に戻す（DELETE /invoice/{id}/paid）。mark_invoice_paid を誤って実行した場合の"
                "取り消しなどに使う。既に未入金の請求書に対して実行しても状態は変わらずべき等。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_id": {"type": "integer", "description": "請求書ID"},
                },
                "required": ["invoice_id"],
            },
        ),
        types.Tool(
            name="mark_invoice_submitted",
            description=(
                "請求書を請求済みステータスにする（PUT /invoice/{id}/submitted）。既に請求済みの場合は状態が"
                "変わらずべき等。取り消すには mark_invoice_unsubmitted を使う。本APIはステータスを変更するのみで"
                "取引先へのメール送信は行わない（請求書をメールで送付するAPIはMisoca API v3には提供されていない。"
                "郵送で送付する send_by_postal_mail というAPIは存在するが、実行すると実際に郵送費用が発生するため"
                "本コネクタには実装していない）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_id": {"type": "integer", "description": "請求書ID"},
                },
                "required": ["invoice_id"],
            },
        ),
        types.Tool(
            name="mark_invoice_unsubmitted",
            description=(
                "請求書を未請求ステータスに戻す（DELETE /invoice/{id}/submitted）。mark_invoice_submitted を"
                "誤って実行した場合の取り消しなどに使う。既に未請求の場合は状態が変わらずべき等。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_id": {"type": "integer", "description": "請求書ID"},
                },
                "required": ["invoice_id"],
            },
        ),
        types.Tool(
            name="trash_invoice",
            description=(
                "請求書をごみ箱に移動する（PUT /invoice/{id}/trashed）。Misoca API v3には請求書を完全に削除する"
                "エンドポイントは提供されておらず、この「ごみ箱への移動」が実質的な削除操作にあたる。"
                "list_invoices に type=trashed を指定するとごみ箱内の請求書を確認できる。誤って移動した場合は"
                "restore_invoice で元に戻せる。既にごみ箱にある請求書に対して実行しても状態は変わらずべき等。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_id": {"type": "integer", "description": "請求書ID"},
                },
                "required": ["invoice_id"],
            },
        ),
        types.Tool(
            name="restore_invoice",
            description=(
                "ごみ箱に移動した請求書を元に戻す（DELETE /invoice/{id}/trashed）。trash_invoice で移動した請求書を"
                "復元する場合に使う。ごみ箱にない請求書に対して実行しても状態は変わらずべき等。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_id": {"type": "integer", "description": "請求書ID"},
                },
                "required": ["invoice_id"],
            },
        ),
        # ── 取引先・送り先 ──
        types.Tool(
            name="list_contact_groups",
            description=(
                "取引先（顧客企業単位のマスタ情報）の一覧を取得する。ここで得られる id は list_invoices の "
                "contact_group_id 絞り込みに使う（請求書の宛先として create_invoice に渡す「送り先」IDとは別物。"
                "送り先は list_contacts で取得する）。既定では非表示にした取引先は含まれない（trashed=true を"
                "指定すると非表示のものも取得できる）。ページングパラメータはなく、常に全件を一度に返す。"
                "読み取り専用（取引先の作成・更新・非表示化のAPIも存在するが本コネクタには実装していない）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "trashed": {"type": "boolean", "description": "trueにすると非表示にした取引先も取得する（既定false）"},
                },
            },
        ),
        types.Tool(
            name="list_contacts",
            description=(
                "送り先（取引先ごとに登録できる請求書の宛先。同じ取引先内の複数部署・複数担当者などを表す）の"
                "一覧を取得する。ここで得られる id が create_invoice の contact_id に渡すべきIDである（取引先"
                "そのもの＝list_contact_groups とは別の資源）。contact_group_id を指定すると特定の取引先に紐づく"
                "送り先のみに絞り込める。既定では非表示にした送り先は含まれない（trashed=true で非表示のものも"
                "取得可能）。名前によるキーワード検索パラメータはAPI側に提供されていない（絞り込みは"
                "contact_group_id のみ）。ページングパラメータはなく、常に全件を一度に返す。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_group_id": {"type": "integer", "description": "この取引先IDに紐づく送り先のみに絞り込む"},
                    "trashed": {"type": "boolean", "description": "trueにすると非表示にした送り先も取得する（既定false）"},
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        return _dispatch(name, arguments)
    except Exception as exc:  # noqa: BLE001 — MCP では例外を意味のある文字列で返す
        return error_response(exc)


def _dispatch(name: str, arguments: dict) -> list[types.TextContent]:
    with _client() as client:
        # ── 請求書 ──
        if name == "list_invoices":
            params: dict = {}
            if "page" in arguments:
                params["page"] = arguments["page"]
            if "per_page" in arguments:
                params["per_page"] = arguments["per_page"]
            for key in (
                "type",
                "from",
                "to",
                "due_date_from",
                "due_date_to",
                "updated_at_from",
                "updated_at_to",
                "payment_status",
                "invoice_status",
                "contact_group_id",
                "condition",
                "order",
                "order_by",
            ):
                if arguments.get(key) is not None:
                    params[key] = arguments[key]
            r = client.get("/invoices", params=params)

        elif name == "get_invoice":
            r = client.get(f"/invoice/{arguments['invoice_id']}")

        elif name == "create_invoice":
            payload: dict = {
                "contact_id": arguments["contact_id"],
                "issue_date": arguments["issue_date"],
            }
            if arguments.get("invoice_number"):
                payload["invoice_number"] = arguments["invoice_number"]
            if arguments.get("subject"):
                payload["subject"] = arguments["subject"]
            if arguments.get("payment_due_on"):
                payload["payment_due_on"] = arguments["payment_due_on"]
            if arguments.get("body"):
                payload["body"] = arguments["body"]
            if arguments.get("items"):
                payload["items"] = arguments["items"]
            r = client.post("/invoice", json=payload)

        elif name == "mark_invoice_paid":
            body = {}
            if arguments.get("paid_on"):
                body["paid_on"] = arguments["paid_on"]
            r = client.put(f"/invoice/{arguments['invoice_id']}/paid", json=body)

        elif name == "mark_invoice_unpaid":
            r = client.request("DELETE", f"/invoice/{arguments['invoice_id']}/paid")

        elif name == "mark_invoice_submitted":
            r = client.put(f"/invoice/{arguments['invoice_id']}/submitted", json={})

        elif name == "mark_invoice_unsubmitted":
            r = client.request("DELETE", f"/invoice/{arguments['invoice_id']}/submitted")

        elif name == "trash_invoice":
            r = client.put(f"/invoice/{arguments['invoice_id']}/trashed", json={})

        elif name == "restore_invoice":
            r = client.request("DELETE", f"/invoice/{arguments['invoice_id']}/trashed")

        # ── 取引先・送り先 ──
        elif name == "list_contact_groups":
            params = {}
            if "trashed" in arguments:
                params["trashed"] = arguments["trashed"]
            r = client.get("/contact_groups", params=params)

        elif name == "list_contacts":
            params = {}
            if arguments.get("contact_group_id") is not None:
                params["contact_group_id"] = arguments["contact_group_id"]
            if "trashed" in arguments:
                params["trashed"] = arguments["trashed"]
            r = client.get("/contacts", params=params)

        else:
            raise ValueError(f"未知のツール: {name}")

        r.raise_for_status()
        return format_response(r.json())


def main():
    import asyncio

    async def _run():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

    asyncio.run(_run())


if __name__ == "__main__":
    main()
