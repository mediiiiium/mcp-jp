import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("pipedrive-mcp")
# 注意: 本コネクタは Pipedrive API v1 のエンドポイントを使用している。
# Pipedrive は 2025-04-14 に /persons, /persons/search, /deals, /activities 等の
# v1 エンドポイントの非推奨化を発表し、2025-12-31 をもって動作保証を終了した
# （公式チェンジログ: Deprecation of selected API v1 endpoints）。
# 現時点（2026年）でこれらの v1 エンドポイントが実際に 404/410 等のエラーを
# 返す可能性がある。後継の v2 エンドポイントはベース URL・認証方式
# （クエリパラメータ api_token ではなくヘッダ x-api-token）・ページネーション
# 方式（start/limit ではなく limit/cursor）が異なり、単純なパス置換では
# 移行できないため、本タスクでは v1 のまま据え置いている。動作しない場合は
# v2 への移行が必要。
BASE_URL = "https://api.pipedrive.com/v1"


def _client() -> httpx.Client:
    api_token = os.environ.get("PIPEDRIVE_API_TOKEN")
    if not api_token:
        raise ValueError("PIPEDRIVE_API_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Content-Type": "application/json"},
        params={"api_token": api_token},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_persons",
            description=(
                "人物（コンタクト）の一覧を取得する。条件を絞らずに全件を棚卸ししたい場合や、"
                "create_deal に渡す person_id を確認する目的で使う。名前・メール・電話番号などで"
                "絞り込みたい場合はこのツールにはフィルタパラメータがないため search_persons を使う方が"
                "効率的。ページネーションは start/limit 方式（本ツールの既定は start=0, limit=100。"
                "Pipedrive API 側の上限は limit=500）。レスポンスの additional_data.pagination."
                "more_items_in_collection が true の場合は次のページが存在するので、start を"
                "前回の start+limit にして再取得する。並び順は API 側の既定に従い、本コネクタで"
                "変更するパラメータは提供していない。読み取り専用。Pipedrive API には人物の新規作成・"
                "更新・削除エンドポイントも存在するが、本コネクタには実装されていない（必要な場合は"
                "Pipedrive の管理画面から操作する）。"
                "\n\n"
                "注意: 本ツールが呼び出す GET /v1/persons は Pipedrive が2025-12-31付けで動作保証を"
                "終了した v1 エンドポイントであり、現時点でエラーになる可能性がある（後継は "
                "GET /api/v2/persons だが、認証方式・ページネーション方式が異なるため本コネクタは"
                "未移行）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（デフォルト100、Pipedrive API側の上限は500）"},
                    "start": {"type": "integer", "description": "ページネーションのオフセット（デフォルト0。0始まりでレコード数単位。次ページ取得時は前回の start+limit を指定する）"},
                },
            },
        ),
        types.Tool(
            name="search_persons",
            description=(
                "人物（コンタクト）を名前・メール・電話番号・メモ・カスタムフィールドの値で検索する。"
                "list_persons には絞り込み条件がないため、特定の人物を素早く見つけたい場合はこちらを使う。"
                "term は2文字以上必要（exact_match=true を指定する場合のみ1文字から可）。fields を省略すると"
                "name・email・phone・notes・custom_fields のすべてが検索対象になる（カスタムフィールドは"
                "address/varchar/text/varchar_auto/double/monetary/phone 型のみ検索可能）。organization_id を"
                "指定すると、その組織に紐づく人物のみに絞り込める。ページネーションは start/limit 方式"
                "（本ツールの既定は start=0, limit=10）。読み取り専用。"
                "\n\n"
                "注意: 本ツールが呼び出す GET /v1/persons/search は Pipedrive が2025-12-31付けで動作保証を"
                "終了した v1 エンドポイントであり、現時点でエラーになる可能性がある（後継は "
                "GET /api/v2/persons/search だが、認証方式が異なるため本コネクタは未移行）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "term": {"type": "string", "description": "検索キーワード（2文字以上。exact_match=true の場合のみ1文字可）"},
                    "fields": {
                        "type": "string",
                        "description": "検索対象フィールドをカンマ区切りで指定（name, email, phone, notes, custom_fields）。省略時は全種類が対象",
                    },
                    "exact_match": {
                        "type": "boolean",
                        "description": "true にすると term と完全一致するもののみを返す（大文字小文字は区別しない）。省略時は部分一致",
                    },
                    "organization_id": {"type": "integer", "description": "指定した組織IDに紐づく人物のみに絞り込む"},
                    "limit": {"type": "integer", "description": "取得件数（デフォルト10）"},
                    "start": {"type": "integer", "description": "ページネーションのオフセット（デフォルト0）"},
                },
                "required": ["term"],
            },
        ),
        types.Tool(
            name="list_deals",
            description=(
                "案件（Deal）の一覧を取得する。パイプラインの棚卸しや、特定ステータスの案件の洗い出しに使う。"
                "status を省略した場合は Pipedrive API の既定である all_not_deleted（削除済み以外すべて）が"
                "適用される（open/won/lost/deleted/all_not_deleted から選択可能。カンマ区切りで複数指定も可）。"
                "ページネーションは start/limit 方式（本ツールの既定は start=0, limit=100。API 側の上限は"
                "limit=500）。additional_data.pagination.more_items_in_collection が true の場合は次のページが"
                "存在する。並び順は API 側の既定に従い、本コネクタで変更するパラメータは提供していない。"
                "読み取り専用。Pipedrive API には案件の更新・削除エンドポイントも存在するが、本コネクタには"
                "実装されていない（新規作成は create_deal で可能）。"
                "\n\n"
                "注意: 本ツールが呼び出す GET /v1/deals は Pipedrive が2025-12-31付けで動作保証を終了した "
                "v1 エンドポイントであり、現時点でエラーになる可能性がある（後継は GET /api/v2/deals だが、"
                "認証方式・ページネーション方式が異なるため本コネクタは未移行）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "ステータスで絞り込む: open（進行中）/ won（成約）/ lost（失注）/ deleted（削除済み、直近30日以内のみ）/ all_not_deleted（削除済み以外すべて）。カンマ区切りで複数指定可。省略時は all_not_deleted（API既定）",
                    },
                    "limit": {"type": "integer", "description": "取得件数（デフォルト100、API側の上限は500）"},
                    "start": {"type": "integer", "description": "ページネーションのオフセット（デフォルト0。次ページ取得時は前回の start+limit を指定する）"},
                },
            },
        ),
        types.Tool(
            name="create_deal",
            description=(
                "新しい案件（Deal）を1件作成する。呼び出すたびに新規レコードが作成され、重複防止"
                "（べき等性）の仕組みは Pipedrive API 側にない。同じ内容で誤って複数回呼び出すと同名の"
                "案件が重複して作成されるため、実行前に list_deals や search_persons 経由での重複確認を"
                "推奨する。title のみ必須で、value・currency・person_id・org_id・stage_id は省略可能"
                "（stage_id を省略すると、対象パイプラインの最初のステージに配置される）。currency を"
                "指定する場合は ISO 4217 形式（例: JPY, USD）で、value と組で指定するのが望ましい。"
                "作成後の案件の更新・削除エンドポイントは Pipedrive API には存在するが、本コネクタには"
                "実装されていない（必要な場合は Pipedrive 管理画面から操作する）。"
                "\n\n"
                "注意: 本ツールが呼び出す POST /v1/deals は Pipedrive が2025-12-31付けで動作保証を終了した "
                "v1 エンドポイントであり、現時点でエラーになる可能性がある（後継は POST /api/v2/deals だが、"
                "認証方式が異なるため本コネクタは未移行）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "案件のタイトル（必須）"},
                    "value": {"type": "number", "description": "案件の金額（省略可）"},
                    "currency": {"type": "string", "description": "通貨コード（ISO 4217形式、例: JPY, USD。省略可）"},
                    "person_id": {"type": "integer", "description": "紐づける担当者（Person）のID（省略可）"},
                    "org_id": {"type": "integer", "description": "紐づける組織（Organization）のID（省略可）"},
                    "stage_id": {"type": "integer", "description": "配置するパイプラインステージのID（省略時は対象パイプラインの最初のステージ）"},
                },
                "required": ["title"],
            },
        ),
        types.Tool(
            name="list_activities",
            description=(
                "アクティビティ（電話・訪問・タスクなどの商談活動）の一覧を取得する。担当者の稼働状況の"
                "確認や、未完了タスクの洗い出しに使う。done で完了状態を絞り込める（0=未完了, 1=完了。"
                "省略時は完了・未完了の両方が返る）。ページネーションは start/limit 方式（本ツールの既定は"
                "start=0, limit=100。API側の上限は limit=500）。additional_data.pagination."
                "more_items_in_collection が true の場合は次のページが存在する。並び順は API 側の既定に従い、"
                "本コネクタで変更するパラメータは提供していない。読み取り専用。Pipedrive API には"
                "アクティビティの新規作成・更新・削除エンドポイントも存在するが、本コネクタには実装されて"
                "いない（必要な場合は Pipedrive 管理画面から操作する）。"
                "\n\n"
                "注意: 本ツールが呼び出す GET /v1/activities は Pipedrive が2025-12-31付けで動作保証を"
                "終了した v1 エンドポイントであり、現時点でエラーになる可能性がある（後継は "
                "GET /api/v2/activities だが、認証方式・ページネーション方式が異なるため本コネクタは"
                "未移行）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "done": {"type": "integer", "description": "完了状態で絞り込む: 0=未完了, 1=完了（省略時は両方）"},
                    "limit": {"type": "integer", "description": "取得件数（デフォルト100、API側の上限は500）"},
                    "start": {"type": "integer", "description": "ページネーションのオフセット（デフォルト0。次ページ取得時は前回の start+limit を指定する）"},
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_persons":
                params = {
                    "limit": arguments.get("limit", 100),
                    "start": arguments.get("start", 0),
                }
                r = client.get("/persons", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "search_persons":
                params = {
                    "term": arguments["term"],
                    "limit": arguments.get("limit", 10),
                    "start": arguments.get("start", 0),
                }
                if arguments.get("fields"):
                    params["fields"] = arguments["fields"]
                if arguments.get("exact_match") is not None:
                    params["exact_match"] = arguments["exact_match"]
                if arguments.get("organization_id") is not None:
                    params["organization_id"] = arguments["organization_id"]
                r = client.get("/persons/search", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_deals":
                params = {
                    "limit": arguments.get("limit", 100),
                    "start": arguments.get("start", 0),
                }
                if arguments.get("status"):
                    params["status"] = arguments["status"]
                r = client.get("/deals", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "create_deal":
                payload = {"title": arguments["title"]}
                for field in ("value", "currency", "person_id", "org_id", "stage_id"):
                    if arguments.get(field) is not None:
                        payload[field] = arguments[field]
                r = client.post("/deals", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_activities":
                params = {
                    "limit": arguments.get("limit", 100),
                    "start": arguments.get("start", 0),
                }
                if arguments.get("done") is not None:
                    params["done"] = arguments["done"]
                r = client.get("/activities", params=params)
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
