import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("payjp-mcp")

BASE_URL = "https://api.pay.jp/v1"


def _client() -> httpx.Client:
    secret_key = os.environ.get("PAYJP_SECRET_KEY")
    if not secret_key:
        raise ValueError("PAYJP_SECRET_KEY が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        auth=(secret_key, ""),
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_charges",
            description=(
                "決済（charge）の一覧を取得する。作成日時の新しい順（降順）で返る。日次の売上確認や、"
                "特定顧客・特定サブスクリプションに紐づく決済履歴の確認に使う。ページネーションは "
                "limit（1〜100、既定10）と offset（既定0）方式：offset を増やしながら繰り返し呼ぶことで"
                "続きを取得する（レスポンスの has_more で次ページの有無を確認できる）。customer / "
                "subscription で絞り込み可能、since / until は UNIX タイムスタンプで作成日時の範囲を指定する。"
                "読み取り専用で副作用はない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（1〜100、既定10）", "default": 10},
                    "offset": {"type": "integer", "description": "スキップ件数（既定0）", "default": 0},
                    "customer": {"type": "string", "description": "顧客IDで絞り込み"},
                    "subscription": {"type": "string", "description": "サブスクリプションIDで絞り込み"},
                    "since": {"type": "integer", "description": "UNIX タイムスタンプ（この日時以降に作成）"},
                    "until": {"type": "integer", "description": "UNIX タイムスタンプ（この日時以前に作成）"},
                },
            },
        ),
        types.Tool(
            name="get_charge",
            description=(
                "指定した課金ID（ch_ で始まる）の決済詳細を1件取得する。返金済みかどうか（refunded）・"
                "返金済み額（amount_refunded）・与信のみで未確定か（captured=false）などのステータス確認に使う。"
                "refund_charge を呼ぶ前後の状態確認（二重返金の回避）にも使える。読み取り専用で副作用はない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "charge_id": {"type": "string", "description": "課金ID（ch_ で始まる）"},
                },
                "required": ["charge_id"],
            },
        ),
        types.Tool(
            name="refund_charge",
            description=(
                "指定した決済を返金する。amount を省略すると残額を全額返金、金額を指定すると部分返金になる。"
                "返金は決済の作成日から180日以内のみ可能。refund_reason で返金理由（自由記述、最大255文字）を"
                "任意で記録できる。"
                "重要（べき等性・二重返金リスク）: PAY.JP の v1 API（本コネクタが利用しているエンドポイント）は "
                "Idempotency-Key ヘッダーによるべき等性保証を提供していない（べき等リクエストは v2 API のみの"
                "機能）。全額返金済みの決済に対して同じリクエストを再実行した場合は「既に返金済み」という"
                "エラー（HTTP 400）になり金額面での二重返金は防げるが、amount を指定した部分返金を繰り返し"
                "呼び出すと、その都度追加で返金が実行されてしまい実際に二重（多重）返金になる。通信タイムアウト等で"
                "成否が確認できない場合は、再実行する前に get_charge で refunded / amount_refunded を確認すること。"
                "決済（charge）そのものの削除APIは存在せず、取り消しは本ツールでの返金のみが手段となる。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "charge_id": {"type": "string", "description": "課金ID（ch_ で始まる）"},
                    "amount": {"type": "integer", "description": "返金額（省略時は残額を全額返金）"},
                    "refund_reason": {"type": "string", "description": "返金理由（自由記述、最大255文字、任意）"},
                },
                "required": ["charge_id"],
            },
        ),
        types.Tool(
            name="list_customers",
            description=(
                "顧客の一覧を取得する。作成日時の新しい順（降順）で返る。ページネーションは limit（1〜100、"
                "既定10）と offset（既定0）方式。since / until で作成日時の範囲を絞り込める（UNIX タイムスタンプ）。"
                "読み取り専用で副作用はない。なお PAY.JP API には顧客の新規作成・更新（POST /v1/customers/:id）・"
                "削除（DELETE /v1/customers/:id）のエンドポイントが存在するが、本コネクタではツールとして"
                "提供していない（一覧・詳細参照のみ）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（1〜100、既定10）", "default": 10},
                    "offset": {"type": "integer", "description": "スキップ件数（既定0）", "default": 0},
                    "since": {"type": "integer", "description": "UNIX タイムスタンプ（この日時以降に作成）"},
                    "until": {"type": "integer", "description": "UNIX タイムスタンプ（この日時以前に作成）"},
                },
            },
        ),
        types.Tool(
            name="list_subscriptions",
            description=(
                "サブスクリプション（定期課金）の一覧を取得する。作成日時の新しい順（降順）で返る。"
                "ページネーションは limit（1〜100、既定10）と offset（既定0）方式。customer / plan / status "
                "（trial・active・canceled・paused）に加え、since / until（UNIX タイムスタンプ、作成日時の範囲）"
                "でも絞り込み可能。読み取り専用で副作用はない。なお一時停止（pause）・再開（resume）・"
                "キャンセル（cancel）・削除（delete）のエンドポイントは PAY.JP API 側に存在するが、本コネクタでは"
                "ツールとして提供していない（一覧参照のみ）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（1〜100、既定10）", "default": 10},
                    "offset": {"type": "integer", "description": "スキップ件数（既定0）", "default": 0},
                    "customer": {"type": "string", "description": "顧客IDで絞り込み"},
                    "plan": {"type": "string", "description": "プランIDで絞り込み"},
                    "status": {
                        "type": "string",
                        "description": "ステータスで絞り込み: trial / active / canceled / paused",
                    },
                    "since": {"type": "integer", "description": "UNIX タイムスタンプ（この日時以降に作成）"},
                    "until": {"type": "integer", "description": "UNIX タイムスタンプ（この日時以前に作成）"},
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_charges":
                params: dict = {}
                if arguments.get("limit") is not None:
                    params["limit"] = arguments["limit"]
                if arguments.get("offset") is not None:
                    params["offset"] = arguments["offset"]
                if arguments.get("customer"):
                    params["customer"] = arguments["customer"]
                if arguments.get("subscription"):
                    params["subscription"] = arguments["subscription"]
                if arguments.get("since"):
                    params["since"] = arguments["since"]
                if arguments.get("until"):
                    params["until"] = arguments["until"]
                r = client.get("/charges", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_charge":
                r = client.get(f"/charges/{arguments['charge_id']}")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "refund_charge":
                body: dict = {}
                if arguments.get("amount") is not None:
                    body["amount"] = arguments["amount"]
                if arguments.get("refund_reason"):
                    body["refund_reason"] = arguments["refund_reason"]
                r = client.post(f"/charges/{arguments['charge_id']}/refund", data=body)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_customers":
                params = {}
                if arguments.get("limit") is not None:
                    params["limit"] = arguments["limit"]
                if arguments.get("offset") is not None:
                    params["offset"] = arguments["offset"]
                if arguments.get("since"):
                    params["since"] = arguments["since"]
                if arguments.get("until"):
                    params["until"] = arguments["until"]
                r = client.get("/customers", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_subscriptions":
                params = {}
                if arguments.get("limit") is not None:
                    params["limit"] = arguments["limit"]
                if arguments.get("offset") is not None:
                    params["offset"] = arguments["offset"]
                if arguments.get("customer"):
                    params["customer"] = arguments["customer"]
                if arguments.get("plan"):
                    params["plan"] = arguments["plan"]
                if arguments.get("status"):
                    params["status"] = arguments["status"]
                if arguments.get("since"):
                    params["since"] = arguments["since"]
                if arguments.get("until"):
                    params["until"] = arguments["until"]
                r = client.get("/subscriptions", params=params)
                r.raise_for_status()
                return format_response(r.json())

            else:
                raise ValueError(f"未知のツール: {name}")
    except Exception as exc:  # noqa: BLE001 — MCP では例外を意味のある文字列で返す
        return error_response(exc)


def main():
    import asyncio

    async def _run():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

    asyncio.run(_run())


if __name__ == "__main__":
    main()
