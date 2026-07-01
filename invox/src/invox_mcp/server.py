import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response, MAX_CHARS

app = Server("invox-mcp")

BASE_URL = "https://api.invox.jp/api/public"


def _company_code() -> str:
    company_code = os.environ.get("INVOX_COMPANY_CODE")
    if not company_code:
        raise ValueError("INVOX_COMPANY_CODE が設定されていません")
    return company_code


def _client() -> httpx.Client:
    token = os.environ.get("INVOX_ACCESS_TOKEN")
    if not token:
        raise ValueError("INVOX_ACCESS_TOKEN が設定されていません")
    company_code = _company_code()
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        # invox_company_code は GET 系エンドポイントではクエリパラメータとして必須。
        # POST/PUT/DELETE 系エンドポイントは invox の API 仕様上、JSON ボディ側に
        # invox_company_code を含める必要があるため、書き込み系の呼び出しでは
        # 別途ペイロードにも invox_company_code を入れている（下記 call_tool 参照）。
        params={"invox_company_code": company_code},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_received_invoices",
            description=(
                "受取請求書の一覧を、請求日・計上日・部門・確定状態などの条件で絞り込んで取得する。"
                "fixed_only を省略すると true 扱いとなり、データ化中・確認待ち・未申請などまだ確定していない"
                "請求書は結果に含まれない点に注意（下書き段階のものも見たい場合は fixed_only=false を指定する）。"
                "レスポンスは count/next/previous/results 形式で、1ページ最大100件（page の開始番号は"
                "API ドキュメントに明記されていないため未確認、既定値1で試すこと）。仕入先名やワークフローの"
                "承認状態（承認待ち・差し戻し等）で直接絞り込むクエリパラメータは API 側に存在しないため、"
                "必要な場合は list_suppliers で仕入先コードを調べて突き合わせるか、取得結果をクライアント側で"
                "絞り込むこと。特定1件の詳細だけが必要な場合は get_received_invoice の方が効率的。書き込みは"
                "行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer",
                        "description": "ページ番号。1ページ最大100件（開始番号はドキュメント未記載、既定1で試すこと）。",
                        "default": 1,
                    },
                    "invoice_date_from": {
                        "type": "string",
                        "description": "請求日（発行日）の開始日。YYYY-MM-DD / YYYY/MM/DD / YYYYMMDD のいずれかの形式。",
                    },
                    "invoice_date_to": {
                        "type": "string",
                        "description": "請求日（発行日）の終了日。日付形式は invoice_date_from と同様。",
                    },
                    "posting_date_from": {
                        "type": "string",
                        "description": "仕訳計上日の開始日。日付形式は invoice_date_from と同様。",
                    },
                    "posting_date_to": {
                        "type": "string",
                        "description": "仕訳計上日の終了日。日付形式は invoice_date_from と同様。",
                    },
                    "fixed_only": {
                        "type": "boolean",
                        "description": (
                            "true（省略時の既定）の場合、確定済み以降のステータスの請求書のみを対象にする。"
                            "false にすると、データ化中・確認待ちなど未確定の請求書も含む。"
                        ),
                    },
                    "export_status": {
                        "type": "string",
                        "enum": [
                            "invoice_unexported",
                            "payment_unexported",
                            "expense_journal_unexported",
                        ],
                        "description": (
                            "出力状況で絞り込む: invoice_unexported=請求データ未出力、"
                            "payment_unexported=支払データ未出力、expense_journal_unexported=費用計上仕訳未出力。"
                        ),
                    },
                    "department_code": {
                        "type": "string",
                        "description": "部門コードで絞り込む。",
                    },
                    "include_sub_departments": {
                        "type": "boolean",
                        "description": "true の場合、department_code で指定した部門の下位部門の請求書も含める（department_code指定時のみ有効）。",
                    },
                },
            },
        ),
        types.Tool(
            name="get_received_invoice",
            description=(
                "受取請求書1件の詳細情報（仕入先・金額内訳・支払期日・添付ファイルURL・ワークフローの"
                "メッセージ履歴など）を取得する。一覧から絞り込むのではなく特定の invoice_id の詳細だけが"
                "必要な場合、list_received_invoices より少ないリクエストで済む。include_journal_info=true"
                "を指定した場合のみ、計上済みの仕訳情報（journal_info）がレスポンスに追加される（省略時や"
                "false の場合は含まれない）。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_id": {"type": "string", "description": "請求書ID"},
                    "include_journal_info": {
                        "type": "boolean",
                        "description": "true の場合、レスポンスに仕訳情報（journal_info）を含める。既定は含めない。",
                    },
                },
                "required": ["invoice_id"],
            },
        ),
        types.Tool(
            name="approve_received_invoice",
            description=(
                "ワークフロー申請済みの受取請求書を1件承認する（invox 側でワークフロー機能が有効になっており、"
                "対象の請求書が既に申請済み＝承認待ち状態である必要がある）。approve_task_name は承認する"
                "ワークフローのタスク名を指定する必須パラメータで、複数の承認ステップがある場合は該当ステップの"
                "名称と完全一致させる必要がある。呼び出すたびに1ステップ分の承認が進む操作であり、既に承認済みの"
                "請求書に対して再度呼び出すとエラーになる（べき等ではない）。ワークフローが無効、請求書の"
                "データ化が未完了、未申請、指定したタスク名が一致しない、承認条件を満たしていない、承認可能な"
                "ステップがない、などの場合もエラーを返す。請求書の申請（apply）・差し戻し（reject）を行う API も"
                "invox 側には存在するが、本コネクタでは未実装。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_id": {"type": "string", "description": "承認する請求書ID"},
                    "approve_task_name": {
                        "type": "string",
                        "description": "承認するワークフローのタスク名（承認ステップの名称と完全一致させる必要がある）。",
                    },
                    "appr_path_id": {
                        "type": "integer",
                        "description": "承認パスIDを明示的に指定する場合に指定する（省略可）。",
                    },
                },
                "required": ["invoice_id", "approve_task_name"],
            },
        ),
        types.Tool(
            name="list_suppliers",
            description=(
                "仕入先（取引先）マスタの一覧を、コード・名称・登録番号・登録日で絞り込んで取得する。"
                "code と name は部分一致、corporate_tax_no（インボイス登録番号、T+13桁）は完全一致で絞り込む。"
                "sort に code または name（カンマ区切りで複数指定可）を渡すと並び順を指定できる（省略時の"
                "既定ソート順は API ドキュメントに明記されていない）。レスポンスは count/next/previous/results"
                "形式で1ページ最大100件。仕入先の登録・更新（POST /invoice_receive/supplier）や削除"
                "（DELETE /invoice_receive/supplier/delete、未確定の請求書に紐づく仕入先は削除不可）を行う API も"
                "invox 側には存在するが、本コネクタは読み取り専用のため未実装。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1ページ最大100件）。", "default": 1},
                    "name": {"type": "string", "description": "仕入先名で絞り込み（部分一致）。"},
                    "code": {"type": "string", "description": "仕入先コードで絞り込み（部分一致）。"},
                    "corporate_tax_no": {
                        "type": "string",
                        "description": "インボイス登録番号（T+13桁）で絞り込み（完全一致）。",
                    },
                    "create_date_from": {
                        "type": "string",
                        "description": "登録日の開始日。YYYY-MM-DD / YYYY/MM/DD / YYYYMMDD のいずれかの形式。",
                    },
                    "create_date_to": {
                        "type": "string",
                        "description": "登録日の終了日。日付形式は create_date_from と同様。",
                    },
                    "sort": {
                        "type": "string",
                        "description": "並び順。code または name（カンマ区切りで複数指定可、例: 'code,name'）。",
                    },
                },
            },
        ),
        types.Tool(
            name="export_journal",
            description=(
                "invox 管理画面側の出力設定（会計ソフト向けの出力形式）に従って、費用計上仕訳"
                "（journal_type=expense）または支払計上仕訳（journal_type=payment）のデータをテキスト形式で"
                "エクスポートする。会計ソフトの種類や対象の請求書IDを直接指定するパラメータは API に存在せず、"
                "出力対象は department_code・posting_date_from/to 等の条件と、invox 管理画面側の出力設定で"
                "決まる。1回の呼び出しで最大100請求データ分しか出力されず、まだ出力可能なデータが残っている"
                "場合はテキストデータが返る。全件出力し終えると HTTP 204（本文なし）が返るため、本ツールを"
                "同じ条件で 204 が返るまで繰り返し呼び出す必要がある（本ツール自体はループせず1回分のみ実行"
                "する）。このエクスポート操作自体は請求書を「出力済み」に変更しない（別途 invoice/set_exported"
                "という invox 側の API を呼ぶ必要があるが、本コネクタでは未実装）ため、同じ条件で繰り返し"
                "呼び出すと同じデータが何度でも出力される点に注意。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "journal_type": {
                        "type": "string",
                        "enum": ["expense", "payment"],
                        "description": "仕訳種別: expense=費用計上仕訳、payment=支払計上仕訳。",
                    },
                    "department_code": {
                        "type": "string",
                        "description": "部門コードで絞り込む（省略可）。",
                    },
                    "include_sub_departments": {
                        "type": "boolean",
                        "description": "true の場合、department_code で指定した部門の下位部門分も含める（department_code指定時のみ有効）。",
                    },
                    "posting_date_from": {
                        "type": "string",
                        "description": "計上日の開始日。YYYY-MM-DD / YYYY/MM/DD / YYYYMMDD のいずれかの形式。",
                    },
                    "posting_date_to": {
                        "type": "string",
                        "description": "計上日の終了日。日付形式は posting_date_from と同様。",
                    },
                },
                "required": ["journal_type"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_received_invoices":
                params: dict = {"page": arguments.get("page", 1)}
                if arguments.get("invoice_date_from"):
                    params["invoice_date_from"] = arguments["invoice_date_from"]
                if arguments.get("invoice_date_to"):
                    params["invoice_date_to"] = arguments["invoice_date_to"]
                if arguments.get("posting_date_from"):
                    params["posting_date_from"] = arguments["posting_date_from"]
                if arguments.get("posting_date_to"):
                    params["posting_date_to"] = arguments["posting_date_to"]
                if arguments.get("fixed_only") is not None:
                    params["fixed_only"] = arguments["fixed_only"]
                if arguments.get("export_status"):
                    params["export_status"] = arguments["export_status"]
                if arguments.get("department_code"):
                    params["department_code"] = arguments["department_code"]
                if arguments.get("include_sub_departments") is not None:
                    params["include_sub_departments"] = arguments["include_sub_departments"]
                r = client.get("/invoice_receive/invoice/list", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_received_invoice":
                params = {"invoice_id": arguments["invoice_id"]}
                if arguments.get("include_journal_info") is not None:
                    params["include_journal_info"] = arguments["include_journal_info"]
                r = client.get("/invoice_receive/invoice/get", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "approve_received_invoice":
                # invox の POST 系エンドポイントは invox_company_code を JSON ボディ側に要求する。
                payload: dict = {
                    "invox_company_code": _company_code(),
                    "invoice_id": arguments["invoice_id"],
                    "approve_task_name": arguments["approve_task_name"],
                }
                if arguments.get("appr_path_id") is not None:
                    payload["appr_path_id"] = arguments["appr_path_id"]
                r = client.post("/invoice_receive/invoice/approve", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_suppliers":
                params = {"page": arguments.get("page", 1)}
                if arguments.get("name"):
                    params["name"] = arguments["name"]
                if arguments.get("code"):
                    params["code"] = arguments["code"]
                if arguments.get("corporate_tax_no"):
                    params["corporate_tax_no"] = arguments["corporate_tax_no"]
                if arguments.get("create_date_from"):
                    params["create_date_from"] = arguments["create_date_from"]
                if arguments.get("create_date_to"):
                    params["create_date_to"] = arguments["create_date_to"]
                if arguments.get("sort"):
                    params["sort"] = arguments["sort"]
                r = client.get("/invoice_receive/supplier/list", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "export_journal":
                # invox の POST 系エンドポイントは invox_company_code を JSON ボディ側に要求する。
                payload = {
                    "invox_company_code": _company_code(),
                    "journal_type": arguments["journal_type"],
                }
                if arguments.get("department_code"):
                    payload["department_code"] = arguments["department_code"]
                if arguments.get("include_sub_departments") is not None:
                    payload["include_sub_departments"] = arguments["include_sub_departments"]
                if arguments.get("posting_date_from"):
                    payload["posting_date_from"] = arguments["posting_date_from"]
                if arguments.get("posting_date_to"):
                    payload["posting_date_to"] = arguments["posting_date_to"]
                r = client.post("/invoice_receive/invoice/journal/export", json=payload)
                r.raise_for_status()
                # 204: 出力可能な仕訳データがこれ以上ない。200: text/plain の仕訳テキストが返る。
                if r.status_code == 204:
                    return [types.TextContent(
                        type="text",
                        text="出力可能な仕訳データはありません（すべて出力済みです）。",
                    )]
                text = r.text
                if len(text) > MAX_CHARS:
                    text = (
                        text[:MAX_CHARS]
                        + f"\n\n... (出力を省略しました。全 {len(text)} 文字。"
                        "1回の呼び出しにつき最大100請求データ分が返るため、"
                        "department_code や日付範囲で絞り込んで再実行してください)"
                    )
                return [types.TextContent(type="text", text=text)]

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
