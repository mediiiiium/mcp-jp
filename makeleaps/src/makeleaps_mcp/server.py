import os
import base64
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

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


def _build_lineitem(item: dict) -> dict:
    """ツール入力の明細行を MakeLeaps API の Line Item 形式に変換する。

    API のフィールド名は description/quantity/unit_cost/price/tax_rate/tax_type/is_taxable で、
    kind（normal/simple/text/subtotal）が必須。normal は数量・単価から金額を自動計算できるが、
    simple は description と price のみを持つ（quantity・unit_cost は無視される）。
    """
    kind = item.get("kind") or "normal"
    payload: dict = {"kind": kind, "description": item.get("description", "")}
    if kind == "normal":
        payload["quantity"] = item.get("quantity", "1")
        if item.get("unit_cost") is not None:
            payload["unit_cost"] = item["unit_cost"]
    if item.get("price") is not None:
        payload["price"] = item["price"]
    if item.get("tax_rate") is not None:
        payload["tax_rate"] = item["tax_rate"]
    if item.get("tax_type"):
        payload["tax_type"] = item["tax_type"]
    if item.get("is_taxable") is not None:
        payload["is_taxable"] = item["is_taxable"]
    return payload


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_clients",
            description=(
                "取引先（クライアント）一覧を取得する。取引先名の全文検索や、create_document で使う "
                "client_mid（取引先URLから読み取れるID）を調べる起点として使う。search は取引先名の"
                "部分一致検索、archived はアーカイブ済み取引先も含めるかどうかのフィルタ（MakeLeaps API "
                "側で archived を省略した場合の既定挙動は公式ドキュメントに明記されていない）。ページネーション"
                "方式（page/limit 等のパラメータ名）は公式ドキュメントに明記されておらず未検証。読み取り専用。"
                "MakeLeaps API には取引先の作成（POST）・更新（PUT/PATCH）・削除（DELETE、書類から参照されて"
                "いない場合のみ可）エンドポイントも存在するが、本コネクタには実装されていない（MakeLeaps 管理"
                "画面から操作する）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": "取引先名で全文検索（部分一致）"},
                    "archived": {"type": "boolean", "description": "true にするとアーカイブ済み取引先のみ/を含めて絞り込む（API既定の挙動は非公開）"},
                    "has_virtual_bank_accounts": {"type": "boolean", "description": "バーチャル口座が割り当てられている取引先のみに絞り込む"},
                },
            },
        ),
        types.Tool(
            name="list_documents",
            description=(
                "書類（請求書・見積書・発注書・納品書等）一覧を取得する。特定取引先・特定期間・ステータスで"
                "書類を棚卸ししたい場合に使う。document_type・client_mid・client_contact_mid・currency・tags で"
                "絞り込み、date/date_from/date_to で発行日を絞り込める（date_from は date__gte、date_to は "
                "date__lte として送信）。sent/confirmed/accepted/viewed/paid/cancelled の各真偽値フィルタで"
                "書類のステータスを絞り込める。search は書類番号・件名等の全文検索。並び順の既定値は公式"
                "ドキュメントに明記されていない。ページネーションの page パラメータは MakeLeaps 側のドキュメント"
                "に明記された正式なパラメータ名ではなく、効果は未検証（結果が多い場合は date_from/date_to や "
                "search 等の絞り込み条件を使うことを推奨）。読み取り専用。書類の詳細（明細行を含む全フィールド）"
                "を見たい場合は get_document を使う。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "document_type": {"type": "string", "description": "書類種別: invoice（請求書）/ quote（見積書）/ order（発注書）/ orderslip（注文請書）/ orderconfirmation（注文確認書）/ deliveryslip（納品書）/ acceptance（検収書）/ receipt（領収書）/ paymentnotice（支払通知書）/ timesheet（勤務表）"},
                    "search": {"type": "string", "description": "書類番号・件名等の全文検索"},
                    "client_mid": {"type": "string", "description": "この取引先MIDに紐づく書類のみに絞り込む"},
                    "client_contact_mid": {"type": "string", "description": "この取引先担当者（コンタクト）MIDに紐づく書類のみに絞り込む"},
                    "currency": {"type": "string", "description": "通貨コードで絞り込む（例: JPY）"},
                    "tags": {"type": "string", "description": "タグで絞り込む。カンマ区切りで複数指定するとOR条件になる（例: 2024,2025）"},
                    "date": {"type": "string", "description": "発行日（YYYY-MM-DD）が完全一致する書類のみに絞り込む"},
                    "date_from": {"type": "string", "description": "発行日の開始日（YYYY-MM-DD、この日を含む）"},
                    "date_to": {"type": "string", "description": "発行日の終了日（YYYY-MM-DD、この日を含む）"},
                    "sent": {"type": "boolean", "description": "送付済みかどうかで絞り込む"},
                    "confirmed": {"type": "boolean", "description": "確認済みかどうかで絞り込む"},
                    "accepted": {"type": "boolean", "description": "受注承認済みかどうかで絞り込む"},
                    "viewed": {"type": "boolean", "description": "取引先が閲覧済みかどうかで絞り込む"},
                    "paid": {"type": "boolean", "description": "支払済みかどうかで絞り込む"},
                    "cancelled": {"type": "boolean", "description": "キャンセル済みかどうかで絞り込む"},
                    "page": {"type": "integer", "description": "ページ番号（パラメータ名・効果は未検証）", "default": 1},
                },
            },
        ),
        types.Tool(
            name="get_document",
            description=(
                "指定した1件の書類の詳細情報（明細行・金額・送付ステータス等の全フィールド）を取得する。"
                "list_documents で対象を絞り込んだ後、その1件の内容を詳しく確認したい場合に使う。expand に "
                "client や client_contact 等のフィールド名をカンマ区切りで指定すると、URL参照ではなくその"
                "参照先オブジェクトの内容が展開されて返る（例: expand=client,client_contact）。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "document_mid": {"type": "string", "description": "書類のMID（list_documents の url 末尾から取得できる）"},
                    "expand": {"type": "string", "description": "展開するトップレベルフィールド名をカンマ区切りで指定（例: client,client_contact）"},
                },
                "required": ["document_mid"],
            },
        ),
        types.Tool(
            name="list_document_templates",
            description=(
                "指定した書類種別（document_type）で使用できる書類テンプレートの一覧を取得する。create_document "
                "は document_template を必須で要求するため、有効なテンプレートコード（例: ja_JP_pro_4）を"
                "事前に調べる目的で使う。各テンプレートの use_advanced_tax_settings が true の場合、明細行の "
                "tax_type と tax_rate の両方を指定する必要がある（false の場合は tax_rate のみで legacy 方式）。"
                "読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "document_type": {"type": "string", "description": "書類種別: invoice/quote/order/orderslip/orderconfirmation/deliveryslip/acceptance/receipt/paymentnotice/timesheet"},
                },
                "required": ["document_type"],
            },
        ),
        types.Tool(
            name="create_document",
            description=(
                "新しい書類（請求書・見積書等）を1件作成する。呼び出すたびに新規書類が作成され、MakeLeaps API "
                "側に重複防止（べき等性）の仕組みはない。同一の document_number で type が重複する書類が既に"
                "存在するとAPIはエラーを返すが、document_number を省略・変更すれば同内容でも重複作成できてしまう"
                "ため、誤操作防止には実行前に list_documents で既存書類を確認することを推奨する。document_type・"
                "document_template・client_mid・client_contact_mid・date・line_items が必須（client_contact_mid "
                "は取引先の担当者コンタクトMIDで、list_clients や get_document の contacts フィールドから確認"
                "できる）。document_template は list_document_templates で調べた有効なテンプレートコードを"
                "指定する。autocalculate を true（既定）にすると各明細行の quantity・unit_cost・tax_rate（advanced "
                "税区分テンプレートの場合は tax_type も）から金額・税額が自動計算される。line_items の kind は "
                "normal（数量・単価あり）/ simple（description と price のみ）/ text（説明のみ）/ subtotal（小計"
                "行）から選べ、既定は normal。作成後の書類は update_document に相当する更新用ツールは本コネクタ"
                "には実装されていないが、MakeLeaps API 自体には書類の PUT/PATCH/DELETE エンドポイントが存在する"
                "（本コネクタでは未実装。必要な場合は MakeLeaps 管理画面や API を直接使う）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "document_type": {"type": "string", "description": "書類種別: invoice（請求書）/ quote（見積書）/ order（発注書）/ orderslip（注文請書）/ orderconfirmation（注文確認書）/ deliveryslip（納品書）/ acceptance（検収書）/ receipt（領収書）/ paymentnotice（支払通知書）/ timesheet（勤務表）"},
                    "document_template": {"type": "string", "description": "書類テンプレートコード（必須。list_document_templates で有効なコードを確認する。例: ja_JP_pro_4）"},
                    "document_number": {"type": "string", "description": "書類番号（省略可。同一 document_type・番号の書類が既に存在するとAPIエラーになる）"},
                    "client_mid": {"type": "string", "description": "取引先のMID（必須）"},
                    "client_contact_mid": {"type": "string", "description": "取引先担当者（コンタクト）のMID（必須。list_clients の contacts フィールドや MakeLeaps 管理画面から確認できる）"},
                    "date": {"type": "string", "description": "発行日（YYYY-MM-DD、必須）"},
                    "due_date": {"type": "string", "description": "支払期限（YYYY-MM-DD、省略可。API上のフィールド名は date_due）"},
                    "title": {"type": "string", "description": "件名（省略可）"},
                    "currency": {"type": "string", "description": "通貨コード（例: JPY）", "default": "JPY"},
                    "autocalculate": {"type": "boolean", "description": "true にすると明細行の数量・単価・税率から金額・税額・合計を自動計算する（既定: true）。false にする場合は各明細行に price を明示的に指定する必要がある", "default": True},
                    "line_items": {
                        "type": "array",
                        "description": "明細行（必須、1件以上）",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string", "description": "品目・説明"},
                                "kind": {
                                    "type": "string",
                                    "enum": ["normal", "simple", "text", "subtotal"],
                                    "description": "明細行の種類。normal=数量・単価・税率を持つ通常行（既定）、simple=説明と金額のみ、text=説明のみで金額なし、subtotal=直前までの行の小計行",
                                    "default": "normal",
                                },
                                "quantity": {"type": "string", "description": "数量（文字列で指定。kind=normal のみ有効）", "default": "1"},
                                "unit_cost": {"type": "string", "description": "単価（文字列で指定。autocalculate=true かつ kind=normal のとき、quantity と掛け合わせて price が自動計算される）"},
                                "price": {"type": "string", "description": "金額（文字列で指定）。kind=simple の場合や autocalculate=false の場合はここに直接金額を指定する"},
                                "tax_rate": {"type": "string", "description": "税率（%、文字列で指定）。autocalculate=true の場合、集計のため各行への指定を推奨"},
                                "tax_type": {
                                    "type": "string",
                                    "enum": ["standard", "reduced", "non_taxable", "untaxable", "duty_free", "legacy_tax", "legacy_no_tax"],
                                    "description": "税区分。Advanced税区分対応テンプレート（list_document_templates の use_advanced_tax_settings=true）では standard/reduced/non_taxable/untaxable/duty_free のいずれかが必須。非対応テンプレートでは legacy_tax/legacy_no_tax を使う（省略時は is_taxable から自動判定）",
                                },
                                "is_taxable": {"type": "boolean", "description": "課税対象かどうか（tax_type省略時にこの値から legacy_tax/legacy_no_tax が判定される）"},
                            },
                            "required": ["description"],
                        },
                    },
                },
                "required": ["document_type", "document_template", "client_mid", "client_contact_mid", "date", "line_items"],
            },
        ),
        types.Tool(
            name="send_document",
            description=(
                "作成済みの書類をメールで送付する（MakeLeapsの「Secure Send」機能を使用）。document_mid の書類を"
                "取得して紐づく取引先を特定した上で、送付オーダーを作成 → 書類を送付オーダーに追加 → 送付実行、の"
                "3ステップをまとめて行う。呼び出すたびに新しい送付オーダーが作成され、べき等性はない（同じ書類を"
                "2回送付すると2通メールが送られる）。副作用として実際に取引先へメールが送信される。MakeLeaps API "
                "は送付オーダー実行前に非同期でバリデーションを行うため、作成直後は ready_to_order が false のまま"
                "実行がエラーになることがある（その場合は少し時間をおいて再実行が必要な場合がある。この待機時間の"
                "仕様は公式ドキュメントに明記されていない）。MakeLeaps API は Secure Send 以外にも Client Inbox "
                "送付・郵送（Send by Post）・Peppol送付などの方式や、宛先を複数指定する（to_emails配列）ことに"
                "対応しているが、本ツールはメール1件への Secure Send 送付のみをサポートする。送付後のキャンセル"
                "（PATCH status_url）は本コネクタには実装されていない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "document_mid": {"type": "string", "description": "送付する書類のMID"},
                    "recipient_email": {"type": "string", "description": "送付先メールアドレス（1件のみ指定可能）"},
                    "subject": {"type": "string", "description": "メール件名（省略可）"},
                    "message": {"type": "string", "description": "メール本文（省略可）"},
                },
                "required": ["document_mid", "recipient_email"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    global _token_cache
    try:
        try:
            client = _client()
        except Exception:
            _token_cache = None
            client = _client()
        mid = _partner_mid()

        with client:
            if name == "list_clients":
                params: dict = {}
                if arguments.get("search"):
                    params["search"] = arguments["search"]
                if arguments.get("archived") is not None:
                    params["archived"] = arguments["archived"]
                if arguments.get("has_virtual_bank_accounts") is not None:
                    params["has_virtual_bank_accounts"] = arguments["has_virtual_bank_accounts"]
                r = client.get(f"/api/partner/{mid}/client/", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_documents":
                params = {}
                if arguments.get("document_type"):
                    params["document_type"] = arguments["document_type"]
                if arguments.get("search"):
                    params["search"] = arguments["search"]
                if arguments.get("client_mid"):
                    params["client"] = arguments["client_mid"]
                if arguments.get("client_contact_mid"):
                    params["client_contact"] = arguments["client_contact_mid"]
                if arguments.get("currency"):
                    params["currency"] = arguments["currency"]
                if arguments.get("tags"):
                    params["tags"] = arguments["tags"]
                if arguments.get("date"):
                    params["date"] = arguments["date"]
                if arguments.get("date_from"):
                    params["date__gte"] = arguments["date_from"]
                if arguments.get("date_to"):
                    params["date__lte"] = arguments["date_to"]
                for flag in ("sent", "confirmed", "accepted", "viewed", "paid", "cancelled"):
                    if arguments.get(flag) is not None:
                        params[flag] = arguments[flag]
                if arguments.get("page"):
                    params["page"] = arguments["page"]
                r = client.get(f"/api/partner/{mid}/document/", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_document":
                doc_mid = arguments["document_mid"]
                params = {}
                if arguments.get("expand"):
                    params["expand"] = arguments["expand"]
                r = client.get(f"/api/partner/{mid}/document/{doc_mid}/", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_document_templates":
                doc_type = arguments["document_type"]
                r = client.get(f"/api/partner/{mid}/template/{doc_type}/")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "create_document":
                payload: dict = {
                    "document_type": arguments["document_type"],
                    "document_template": arguments["document_template"],
                    "client": f"{BASE_URL}/api/partner/{mid}/client/{arguments['client_mid']}/",
                    "client_contact": f"{BASE_URL}/api/partner/{mid}/contact/{arguments['client_contact_mid']}/",
                    "date": arguments["date"],
                    "currency": arguments.get("currency", "JPY"),
                    "autocalculate": arguments.get("autocalculate", True),
                    "lineitems": [_build_lineitem(item) for item in arguments["line_items"]],
                }
                if arguments.get("document_number"):
                    payload["document_number"] = arguments["document_number"]
                if arguments.get("due_date"):
                    payload["date_due"] = arguments["due_date"]
                if arguments.get("title"):
                    payload["title"] = arguments["title"]
                r = client.post(f"/api/partner/{mid}/document/", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "send_document":
                doc_mid = arguments["document_mid"]
                doc_url = f"{BASE_URL}/api/partner/{mid}/document/{doc_mid}/"
                doc_r = client.get(doc_url)
                doc_r.raise_for_status()
                document = doc_r.json()
                client_url = document.get("client")
                if not client_url:
                    raise ValueError("書類に紐づく取引先(client)情報が取得できませんでした")

                order_payload: dict = {
                    "recipient_organization": client_url,
                    "securesend_selected": True,
                    "to_emails": [arguments["recipient_email"]],
                }
                if arguments.get("subject"):
                    order_payload["subject"] = arguments["subject"]
                if arguments.get("message"):
                    order_payload["message"] = arguments["message"]
                order_r = client.post(f"/api/partner/{mid}/sending/order/", json=order_payload)
                order_r.raise_for_status()
                order = order_r.json()
                items_url = order.get("items_url", f"{BASE_URL}/api/partner/{mid}/sending/order/{order['mid']}/item/")
                item_r = client.post(items_url, json={"document": doc_url, "position": 0})
                item_r.raise_for_status()
                send_url = order.get("send_url", f"{BASE_URL}/api/partner/{mid}/sending/order/{order['mid']}/send/")
                send_r = client.post(send_url, json={})
                send_r.raise_for_status()
                return format_response(send_r.json())

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
