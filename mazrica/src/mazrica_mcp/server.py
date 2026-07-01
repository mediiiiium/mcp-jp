import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("mazrica-mcp")

BASE_URL = "https://senses-open-api.mazrica.com/v1"


def _client() -> httpx.Client:
    api_key = os.environ.get("MAZRICA_API_KEY")
    if not api_key:
        raise ValueError("MAZRICA_API_KEY が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "X-Api-Key": api_key,
            "Content-Type": "application/json",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        # ── 取引先 ──
        types.Tool(
            name="list_customers",
            description=(
                "取引先（顧客企業）の一覧を取得する。特定顧客の create_deal 用 customer_id を調べる、"
                "または取引先を横断的に棚卸しする目的で使う。既定では更新日時の降順（新しい順）で返り、"
                "sort パラメータで並び順を変更できる。ページネーションは page/limit 方式（本ツールの既定は"
                "page=1, limit=100。Mazrica API 側の上限は limit=1000）。search_word を指定すると取引先名の"
                "部分一致で絞り込める。updated_at_from/updated_at_to で更新日時の範囲を絞り込める。読み取り専用。"
                "Mazrica Open API には取引先の更新（PATCH /customers/{id}）・削除（DELETE /customers/{id}、"
                "紐づく案件・アクション・コンタクトも連動して削除される）エンドポイントも存在するが、"
                "本コネクタには実装されていない（必要な場合は Mazrica 管理画面から操作する）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり）", "default": 1},
                    "limit": {"type": "integer", "description": "1ページあたりの件数（Mazrica API 上限1000、省略時100）", "default": 100},
                    "search_word": {"type": "string", "description": "取引先名で絞り込む（部分一致。API 側パラメータ名は searchWord）"},
                    "sort": {
                        "type": "string",
                        "description": (
                            "並び順。updatedAt または createdAt を指定（既定は更新日時の降順）。"
                            "先頭に - を付けると降順（例: -updatedAt）。カンマ区切りで複数指定可（例: -updatedAt,id）"
                        ),
                    },
                    "updated_at_from": {"type": "string", "description": "更新日時の範囲検索（開始）。ISO 8601形式（例: 2026-04-01T10:30:00）"},
                    "updated_at_to": {"type": "string", "description": "更新日時の範囲検索（終了）。ISO 8601形式"},
                },
            },
        ),
        types.Tool(
            name="create_customer",
            description=(
                "新しい取引先を1件登録する。呼び出すたびに新規レコードが作成され、重複防止（べき等性）の"
                "仕組みは Mazrica API 側にない。同じ内容で誤って複数回呼び出すと同名の取引先が重複して"
                "作成されるため、実行前に list_customers（search_word）で既存の同名取引先がないか確認する"
                "ことを推奨する。name のみ必須。industry_id・owner_role_id に指定できる値は Mazrica 管理画面の"
                "取引先設定（または API の /customer_setting）で確認できる。作成後の更新・削除エンドポイントは"
                "Mazrica API には存在するが、本コネクタには実装されていない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "取引先名（必須）"},
                    "tel_no": {"type": "string", "description": "電話番号（API 側フィールド名は telNo）"},
                    "web_url": {"type": "string", "description": "Webサイト URL（API 側フィールド名は webUrl）"},
                    "address": {"type": "string", "description": "住所"},
                    "industry_id": {"type": "integer", "description": "業種ID（Mazrica 管理画面の取引先設定で確認できる値。指定した場合レスポンスの industry.name に業種名が反映される）"},
                    "owner_role_id": {"type": "integer", "description": "所有ロールID。0 を指定するとロール未指定になる"},
                    "employee": {"type": "integer", "description": "従業員数"},
                    "capital": {"type": "integer", "description": "資本金"},
                    "establish_year": {"type": "integer", "description": "設立年（西暦）"},
                    "closing_month": {"type": "integer", "description": "決算月（1〜12）"},
                    "company_num": {"type": "string", "description": "企業番号（Target タブ表示条件用の内部識別子。画面には表示されない。法人番号とは別物）"},
                },
                "required": ["name"],
            },
        ),
        # ── 案件 ──
        types.Tool(
            name="list_deals",
            description=(
                "案件（商談）の一覧を取得する。特定の案件タイプの棚卸しや、名称・取引先名でのキーワード検索に"
                "使う。既定では更新日時の降順（新しい順）で返り、sort パラメータで並び順を変更できる。"
                "ページネーションは page/limit 方式（本ツールの既定は page=1, limit=100。Mazrica API 側の上限は"
                "limit=1000）。search_word を指定すると取引先名または案件名の部分一致で絞り込める。deal_type_id・"
                "updated_at_from/updated_at_to でも絞り込める。注意: Mazrica の GET /deals には取引先ID（customer_id）"
                "で直接絞り込むクエリパラメータが存在しない。特定取引先の案件だけを厳密に取得したい場合は、"
                "search_word にその取引先名を指定するか、取得結果の customer.id を確認して手元で絞り込む必要がある"
                "（本コネクタには複合条件検索 POST /deals/search は実装されていない）。読み取り専用。案件の更新"
                "（PATCH /deals/{id}）・削除（DELETE /deals/{id}）エンドポイントも存在するが、本コネクタには"
                "実装されていない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり）", "default": 1},
                    "limit": {"type": "integer", "description": "1ページあたりの件数（Mazrica API 上限1000、省略時100）", "default": 100},
                    "search_word": {"type": "string", "description": "取引先名または案件名で絞り込む（部分一致。API 側パラメータ名は searchWord）"},
                    "deal_type_id": {"type": "integer", "description": "案件タイプIDで絞り込む（list_deal_types で確認）"},
                    "sort": {
                        "type": "string",
                        "description": (
                            "並び順。updatedAt または createdAt を指定（既定は更新日時の降順）。"
                            "先頭に - を付けると降順（例: -updatedAt）。カンマ区切りで複数指定可"
                        ),
                    },
                    "updated_at_from": {"type": "string", "description": "更新日時の範囲検索（開始）。ISO 8601形式"},
                    "updated_at_to": {"type": "string", "description": "更新日時の範囲検索（終了）。ISO 8601形式"},
                },
            },
        ),
        types.Tool(
            name="create_deal",
            description=(
                "新しい案件（商談）を1件登録する。呼び出すたびに新規レコードが作成され、重複防止（べき等性）の"
                "仕組みは Mazrica API 側にない。同じ内容で誤って複数回呼び出すと同名の案件が重複して作成される"
                "ため注意すること。Mazrica の案件は「案件タイプ」ごとにフェーズ・商品・契約確度・チャネルの"
                "選択肢が異なるアカウント固有のマスタ設定を持ち、name・deal_type_id・customer_id・phase_id・"
                "product_id・probability_id・channel_id・user_id・expected_contract_date が必須（Mazrica API 側の"
                "必須項目に合わせている）。有効な deal_type_id は list_deal_types で調べ、その deal_type_id に"
                "対応する phase_id・product_id・probability_id・channel_id は get_deal_type で調べる。customer_id は"
                "list_customers、user_id（担当者）は list_users で調べる。amount（契約金額）は省略可。"
                "なお Mazrica API の案件オブジェクトには汎用の memo（メモ）フィールドは存在しない（アカウント固有の"
                "詳細項目 dealCustoms 経由でのみ設定可能だが、本コネクタには未実装）。作成後の更新・削除"
                "エンドポイントも Mazrica API には存在するが、本コネクタには実装されていない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "案件名（必須）"},
                    "deal_type_id": {"type": "integer", "description": "案件タイプID（必須。list_deal_types で確認）"},
                    "customer_id": {"type": "integer", "description": "取引先ID（必須。list_customers で確認）"},
                    "phase_id": {"type": "integer", "description": "フェーズID（必須。get_deal_type で、指定した案件タイプに紐づく有効な値を確認）"},
                    "product_id": {"type": "integer", "description": "商品ID（必須。get_deal_type で確認）"},
                    "probability_id": {"type": "integer", "description": "契約確度ID（必須。get_deal_type で確認）"},
                    "channel_id": {"type": "integer", "description": "チャネルID（必須。get_deal_type で確認）"},
                    "user_id": {"type": "integer", "description": "担当ユーザーID（必須。list_users で確認）"},
                    "expected_contract_date": {"type": "string", "description": "契約予定日（必須。YYYY-MM-DD形式、例: 2026-04-11）"},
                    "amount": {"type": "integer", "description": "契約金額（省略可）"},
                },
                "required": [
                    "name",
                    "deal_type_id",
                    "customer_id",
                    "phase_id",
                    "product_id",
                    "probability_id",
                    "channel_id",
                    "user_id",
                    "expected_contract_date",
                ],
            },
        ),
        # ── 案件タイプ設定（create_deal の各種ID確認用） ──
        types.Tool(
            name="list_deal_types",
            description=(
                "登録済みの案件タイプ（id・name）の一覧を取得する。create_deal に渡す deal_type_id を調べる"
                "起点として使う。案件タイプごとのフェーズ・商品・契約確度・チャネルの詳細（それぞれのID）まで"
                "見たい場合は、ここで調べた id を使って get_deal_type を呼ぶ。読み取り専用。ページネーション・"
                "絞り込みパラメータはない（全件を返す）。"
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="get_deal_type",
            description=(
                "指定した案件タイプ1件の詳細設定（フェーズ・商品・契約確度・チャネル・最終停止理由・"
                "詳細項目設定などの一覧、それぞれ id と name を含む）を取得する。create_deal を呼ぶ前に、"
                "対象の案件タイプで有効な phase_id・product_id・probability_id・channel_id を確認する目的で"
                "使う（これらのIDはアカウントごと・案件タイプごとに異なるマスタ値のため、決め打ちできない）。"
                "対象の案件タイプIDは list_deal_types で確認する。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "deal_type_id": {"type": "integer", "description": "詳細を取得する案件タイプID（list_deal_types で確認）"},
                },
                "required": ["deal_type_id"],
            },
        ),
        # ── ユーザー ──
        types.Tool(
            name="list_users",
            description=(
                "ユーザー（営業担当者）の一覧を取得する。create_deal に渡す user_id（担当ユーザー）を調べる目的で"
                "よく使う。1回のリクエストで最大100件固定（Mazrica API 側に limit パラメータはなく、100件を超える"
                "場合は page を進めて取得する）。deleted=true を指定すると削除済みユーザーも含めて返す（既定は"
                "含めない）。email を指定すると完全一致でそのユーザーのみに絞り込める。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり、1ページ100件固定）", "default": 1},
                    "deleted": {"type": "boolean", "description": "true の場合、削除済みユーザーも含めて取得する（既定は含めない）"},
                    "email": {"type": "string", "description": "このメールアドレスに完全一致するユーザーのみに絞り込む"},
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
        # ── 取引先 ──
        if name == "list_customers":
            params: dict = {
                "page": arguments.get("page", 1),
                "limit": arguments.get("limit", 100),
            }
            if arguments.get("search_word"):
                params["searchWord"] = arguments["search_word"]
            if arguments.get("sort"):
                params["sort"] = arguments["sort"]
            if arguments.get("updated_at_from"):
                params["updatedAtFrom"] = arguments["updated_at_from"]
            if arguments.get("updated_at_to"):
                params["updatedAtTo"] = arguments["updated_at_to"]
            r = client.get("/customers", params=params)

        elif name == "create_customer":
            body: dict = {"name": arguments["name"]}
            if arguments.get("tel_no"):
                body["telNo"] = arguments["tel_no"]
            if arguments.get("web_url"):
                body["webUrl"] = arguments["web_url"]
            if arguments.get("address"):
                body["address"] = arguments["address"]
            if arguments.get("industry_id") is not None:
                body["industryId"] = arguments["industry_id"]
            if arguments.get("owner_role_id") is not None:
                body["ownerRoleId"] = arguments["owner_role_id"]
            if arguments.get("employee") is not None:
                body["employee"] = arguments["employee"]
            if arguments.get("capital") is not None:
                body["capital"] = arguments["capital"]
            if arguments.get("establish_year") is not None:
                body["establishYear"] = arguments["establish_year"]
            if arguments.get("closing_month") is not None:
                body["closingMonth"] = arguments["closing_month"]
            if arguments.get("company_num"):
                body["companyNum"] = arguments["company_num"]
            r = client.post("/customers", json=body)

        # ── 案件 ──
        elif name == "list_deals":
            params = {
                "page": arguments.get("page", 1),
                "limit": arguments.get("limit", 100),
            }
            if arguments.get("search_word"):
                params["searchWord"] = arguments["search_word"]
            if arguments.get("deal_type_id") is not None:
                params["dealTypeId"] = arguments["deal_type_id"]
            if arguments.get("sort"):
                params["sort"] = arguments["sort"]
            if arguments.get("updated_at_from"):
                params["updatedAtFrom"] = arguments["updated_at_from"]
            if arguments.get("updated_at_to"):
                params["updatedAtTo"] = arguments["updated_at_to"]
            r = client.get("/deals", params=params)

        elif name == "create_deal":
            body = {
                "name": arguments["name"],
                "dealType": {"id": arguments["deal_type_id"]},
                "customer": {"id": arguments["customer_id"]},
                "phase": {"id": arguments["phase_id"]},
                "product": {"id": arguments["product_id"]},
                "probability": {"id": arguments["probability_id"]},
                "channel": {"id": arguments["channel_id"]},
                "user": {"id": arguments["user_id"]},
                "expectedContractDate": arguments["expected_contract_date"],
            }
            if arguments.get("amount") is not None:
                body["amount"] = arguments["amount"]
            r = client.post("/deals", json=body)

        # ── 案件タイプ設定 ──
        elif name == "list_deal_types":
            r = client.get("/deal_setting/deal_types")

        elif name == "get_deal_type":
            r = client.get(f"/deal_setting/deal_types/{arguments['deal_type_id']}")

        # ── ユーザー ──
        elif name == "list_users":
            params = {"page": arguments.get("page", 1)}
            if arguments.get("deleted"):
                params["deleted"] = 1
            if arguments.get("email"):
                params["email"] = arguments["email"]
            r = client.get("/users", params=params)

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
