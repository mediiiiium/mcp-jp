import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("smaregi-mcp")

BASE_URL = "https://api.smaregi.jp"


def _client() -> httpx.Client:
    token = os.environ.get("SMAREGI_ACCESS_TOKEN")
    contract_id = os.environ.get("SMAREGI_CONTRACT_ID")
    if not token:
        raise ValueError("SMAREGI_ACCESS_TOKEN が設定されていません")
    if not contract_id:
        raise ValueError("SMAREGI_CONTRACT_ID が設定されていません")
    return httpx.Client(
        base_url=f"{BASE_URL}/{contract_id}/pos",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_products",
            description=(
                "スマレジに登録されている商品のマスタ情報（商品名・価格・部門ID・商品コード等）の一覧を取得する。"
                "在庫数はこのAPIのレスポンスには含まれない（在庫確認には list_stock を使う）。"
                "商品棚卸しや、部門・商品コード単位での商品抽出、商品IDの調査（get_product や他ツールに渡す前段）に使う。"
                "スマレジ・プラットフォームAPIには商品名の部分一致検索パラメータが存在しないため、商品名での絞り込みは"
                "できない（呼び出し側で一覧を取得してから名前でフィルタする必要がある）。1回のリクエストで最大1000件"
                "（未指定時は100件）。ページネーションはpage方式（1始まり）で、レスポンスに総件数が含まれないため、"
                "空配列が返るまでpageを増やして取得を続ける。既定の並び順はAPI仕様上明記されていない（ドキュメントで"
                "確認できず）。読み取り専用。スマレジAPIには商品の新規作成（POST）・更新（PATCH）・削除（DELETE）に"
                "対応するエンドポイントも存在するが、本コネクタでは未実装（閲覧のみ）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（最大1000、既定100）", "default": 100},
                    "page": {"type": "integer", "description": "ページ番号（1始まり、既定1）", "default": 1},
                    "category_id": {"type": "string", "description": "部門IDで絞り込み（完全一致）"},
                    "product_code": {"type": "string", "description": "商品コードで絞り込み（完全一致）"},
                    "group_code": {"type": "string", "description": "グループコード（関連商品のグルーピング）で絞り込み"},
                    "sort": {
                        "type": "string",
                        "description": (
                            "並び順。productId, categoryId, productCode, groupCode, displaySequence, "
                            "updDateTime のいずれかを指定し、降順にしたい場合は「フィールド名:desc」の形式で指定する"
                            "（例: updDateTime:desc）。カンマ区切りで複数指定可。"
                        ),
                    },
                },
            },
        ),
        types.Tool(
            name="get_product",
            description=(
                "商品IDを指定して、その商品1件の詳細情報（商品名・価格・部門ID・商品コード等）を取得する。"
                "list_products で商品IDが分かっている場合の詳細確認に使う。在庫数はこのAPIのレスポンスには"
                "含まれない（在庫確認には list_stock を使う）。1件取得のみでページネーションはない。"
                "読み取り専用。スマレジAPIには商品の更新（PATCH）・"
                "削除（DELETE）に対応するエンドポイントも存在するが、本コネクタでは未実装。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "商品ID（list_products のレスポンスの productId）"},
                },
                "required": ["product_id"],
            },
        ),
        types.Tool(
            name="list_transactions",
            description=(
                "売上取引（レシート単位の取引ヘッダ）の一覧を取得する。「今日の売上を確認したい」「特定店舗・特定期間の"
                "取引件数を把握したい」といった集計・確認に使う。取引明細（購入商品行）はこのAPIのレスポンスには含まれない"
                "（明細が必要な場合は get_transaction_details に取引ID（transactionHeadId）を渡す）。"
                "スマレジ・プラットフォームAPIの仕様上、取引一覧取得には transaction_date_time_from/to・"
                "sum_date・upd_date_time-from/to 等の期間系パラメータのうち最低1つの指定が必須で、未指定のまま"
                "呼び出すとAPIがエラーを返す（本コネクタは transaction_date_time_from/to のみ対応）。会員での絞り込みは"
                "会員ID（customer_id）ではなく会員コード（customer_code）でのみ可能。1回のリクエストで最大1000件"
                "（未指定時は100件）。ページネーションはpage方式（1始まり）で、レスポンスに総件数は含まれない。"
                "既定の並び順はAPI仕様上明記されていない（ドキュメントで確認できず）。読み取り専用。スマレジAPIには"
                "取引の新規作成（POST）・更新（PATCH）・取消（cancel）に対応するエンドポイントも存在するが、"
                "本コネクタでは未実装（閲覧のみ）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（最大1000、既定100）", "default": 100},
                    "page": {"type": "integer", "description": "ページ番号（1始まり、既定1）", "default": 1},
                    "store_id": {"type": "string", "description": "店舗IDで絞り込み"},
                    "transaction_date_time_from": {
                        "type": "string",
                        "description": (
                            "取引日時（開始）。サーバーが取引を受信した日時。形式は YYYY-MM-DDThh:mm:ssTZD "
                            "（例: 2024-01-01T00:00:00+09:00）。この期間パラメータ、または "
                            "transaction_date_time_to のいずれかを指定しないとAPIがエラーになる。"
                        ),
                    },
                    "transaction_date_time_to": {
                        "type": "string",
                        "description": "取引日時（終了）。形式は YYYY-MM-DDThh:mm:ssTZD。最大31日間の範囲まで指定可。",
                    },
                    "customer_code": {"type": "string", "description": "会員コードで絞り込み（会員IDでの絞り込みはAPI非対応）"},
                },
            },
        ),
        types.Tool(
            name="list_customers",
            description=(
                "スマレジに登録されている会員（顧客）の一覧を取得する。会員コード・会員番号での絞り込みや、会員ID範囲"
                "指定、更新日時での絞り込みができる。会員名の部分一致検索・ランク（rank）での絞り込みはスマレジ・"
                "プラットフォームAPIに該当パラメータが存在せず対応していない（呼び出し側で一覧取得後にフィルタする"
                "必要がある）。1回のリクエストで最大1000件（未指定時は100件）。ページネーションはpage方式（1始まり）"
                "で、レスポンスに総件数は含まれない。並び順は customerId または customerCode のみ指定可能で、既定の"
                "並び順はAPI仕様上明記されていない（ドキュメントで確認できず）。読み取り専用。スマレジAPIには会員の"
                "新規作成（POST）・更新（PATCH）・削除（DELETE）に対応するエンドポイントも存在するが、本コネクタでは"
                "未実装（閲覧のみ）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（最大1000、既定100）", "default": 100},
                    "page": {"type": "integer", "description": "ページ番号（1始まり、既定1）", "default": 1},
                    "customer_code": {"type": "string", "description": "会員コードで絞り込み（完全一致）"},
                    "customer_no": {"type": "string", "description": "会員番号で絞り込み"},
                    "customer_id_from": {"type": "string", "description": "会員ID範囲（開始）"},
                    "customer_id_to": {"type": "string", "description": "会員ID範囲（終了）"},
                },
            },
        ),
        types.Tool(
            name="list_stock",
            description=(
                "商品・店舗ごとの在庫数（在庫数・取置き在庫数）の一覧を取得する。list_products / get_product の"
                "レスポンスには在庫数が含まれないため、在庫確認にはこのツールを使う。商品ID・店舗ID・更新日時で"
                "絞り込み可能。**注意**: スマレジ・プラットフォームAPIの仕様上、在庫情報は販売・入出荷等で"
                "在庫数が一度でも変動した商品・店舗の組み合わせでなければ返ってこない（登録後一度も動きが無い"
                "商品は一覧に現れない）。1回のリクエストで最大1000件（未指定時は100件）。ページネーションは"
                "page方式（1始まり）で、レスポンスに総件数は含まれない。既定の並び順はAPI仕様上明記されて"
                "いない（ドキュメントで確認できず）。読み取り専用。スマレジAPIには在庫の更新（PATCH）・相対値"
                "更新（POST .../add）・一括更新に対応するエンドポイントも存在するが、POSの実在庫を書き換える"
                "操作のため本コネクタでは未実装。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（最大1000、既定100）", "default": 100},
                    "page": {"type": "integer", "description": "ページ番号（1始まり、既定1）", "default": 1},
                    "store_id": {"type": "string", "description": "店舗IDで絞り込み"},
                    "product_id": {"type": "string", "description": "商品IDで絞り込み"},
                    "upd_date_time_from": {
                        "type": "string",
                        "description": "更新日時（開始）。形式は YYYY-MM-DDThh:mm:ssTZD（例: 2024-01-01T00:00:00+09:00）。最大31日間の範囲まで指定可。",
                    },
                    "upd_date_time_to": {
                        "type": "string",
                        "description": "更新日時（終了）。形式は YYYY-MM-DDThh:mm:ssTZD。最大31日間の範囲まで指定可。",
                    },
                    "sort": {
                        "type": "string",
                        "description": (
                            "並び順。productId, storeId のいずれかを指定し、降順にしたい場合は"
                            "「フィールド名:desc」の形式で指定する（例: updDateTime:desc）。カンマ区切りで複数指定可。"
                        ),
                    },
                },
            },
        ),
        types.Tool(
            name="get_stock_changes",
            description=(
                "商品ID・店舗IDを指定して、その組み合わせの在庫変動履歴（いつ・何が原因で・いくつ増減し、"
                "結果として在庫がいくつになったか）を取得する。list_stock が示すのは「現在の在庫数」のみで"
                "推移は分からないため、「なぜこの在庫数になったか」「いつ売れた／入荷したか」を追う場合は"
                "このツールを使う。stock_division（在庫区分。例: 修正・仕入・売上・移動など）や対象日・"
                "在庫変動履歴ID・移動元/移動先店舗IDで絞り込み可能。1回のリクエストで最大1000件"
                "（未指定時は100件）。ページネーションはpage方式（1始まり）で、レスポンスに総件数は含まれない。"
                "既定の並び順はAPI仕様上明記されていない（ドキュメントで確認できず）。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "商品ID"},
                    "store_id": {"type": "string", "description": "店舗ID"},
                    "limit": {"type": "integer", "description": "取得件数（最大1000、既定100）", "default": 100},
                    "page": {"type": "integer", "description": "ページ番号（1始まり、既定1）", "default": 1},
                    "id": {"type": "string", "description": "在庫変動履歴IDで絞り込み"},
                    "target_date": {"type": "string", "description": "対象日で絞り込み（YYYY-MM-DD）"},
                    "stock_division": {
                        "type": "string",
                        "description": "在庫区分で絞り込み（例: 01=修正 〜 18=受注在庫引当など、区分コードはスマレジ公式ドキュメント参照）",
                    },
                    "from_store_id": {"type": "string", "description": "移動元店舗IDで絞り込み（店舗間移動の履歴）"},
                    "to_store_id": {"type": "string", "description": "移動先店舗IDで絞り込み（店舗間移動の履歴）"},
                    "sort": {
                        "type": "string",
                        "description": (
                            "並び順。id, updDateTime, targetDateTime, stockAmount, stockDivision, fromStoreId, "
                            "toStoreId, price, cost のいずれかを指定し、降順にしたい場合は「フィールド名:desc」"
                            "の形式で指定する。カンマ区切りで複数指定可。"
                        ),
                    },
                },
                "required": ["product_id", "store_id"],
            },
        ),
        types.Tool(
            name="get_transaction_details",
            description=(
                "取引ID（list_transactions のレスポンスの transactionHeadId）を指定して、その取引の明細"
                "（購入商品行ごとの商品名・数量・単価・値引き・税区分等）を取得する。list_transactions は"
                "取引ヘッダのみで明細を含まないため、レシート内訳の確認にはこのツールを使う。"
                "with_discounts / with_detail_product_attributes を指定すると、値引き明細や商品属性情報も"
                "付加で取得できる。1回のリクエストで最大1000件（未指定時は100件）。ページネーションはpage方式"
                "（1始まり）で、レスポンスに総件数は含まれない。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "transaction_id": {"type": "string", "description": "取引ID（list_transactions のレスポンスの transactionHeadId）"},
                    "limit": {"type": "integer", "description": "取得件数（最大1000、既定100）", "default": 100},
                    "page": {"type": "integer", "description": "ページ番号（1始まり、既定1）", "default": 1},
                    "with_discounts": {
                        "type": "string",
                        "enum": ["all", "none"],
                        "description": "単品値引き/割引の詳細情報を含めるか（all: 含める、none: 含めない）。既定はnone。",
                    },
                    "with_detail_product_attributes": {
                        "type": "string",
                        "enum": ["all", "none"],
                        "description": "販売時の商品属性情報を含めるか（all: 含める、none: 含めない）。既定はnone。",
                    },
                    "sort": {
                        "type": "string",
                        "description": (
                            "並び順。transactionHeadId, transactionDetailId, transactionDetailDivision のいずれかを"
                            "指定し、降順にしたい場合は「フィールド名:desc」の形式で指定する。カンマ区切りで複数指定可。"
                        ),
                    },
                },
                "required": ["transaction_id"],
            },
        ),
        types.Tool(
            name="list_categories",
            description=(
                "スマレジに登録されている部門（商品カテゴリ）の一覧を取得する。部門ID・部門名・階層レベルの"
                "確認や、list_products / list_stock に渡す category_id の調査に使う。部門コード・階層レベル"
                "（1〜3）での絞り込みが可能。部門名の部分一致検索パラメータはAPIに存在しない（呼び出し側で"
                "一覧取得後にフィルタする必要がある）。1回のリクエストで最大1000件（未指定時は100件）。"
                "ページネーションはpage方式（1始まり）で、レスポンスに総件数は含まれない。既定の並び順はAPI"
                "仕様上明記されていない（ドキュメントで確認できず）。読み取り専用。スマレジAPIには部門の"
                "新規作成（POST）・更新（PATCH）・削除（DELETE）に対応するエンドポイントも存在するが、"
                "本コネクタでは未実装（閲覧のみ）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（最大1000、既定100）", "default": 100},
                    "page": {"type": "integer", "description": "ページ番号（1始まり、既定1）", "default": 1},
                    "category_code": {"type": "string", "description": "部門コードで絞り込み（完全一致）"},
                    "level": {"type": "integer", "enum": [1, 2, 3], "description": "階層レベル（1〜3）で絞り込み"},
                    "sort": {
                        "type": "string",
                        "description": (
                            "並び順。categoryId, categoryCode, level, displaySequence, updDateTime のいずれかを"
                            "指定し、降順にしたい場合は「フィールド名:desc」の形式で指定する。カンマ区切りで複数指定可。"
                        ),
                    },
                },
            },
        ),
        types.Tool(
            name="list_stores",
            description=(
                "スマレジに登録されている店舗（および倉庫）の一覧を取得する。店舗ID・店舗名の確認や、list_products /"
                "list_transactions に渡す store_id の調査に使う。店舗コードでの絞り込みが可能。1回のリクエストで"
                "最大1000件（未指定時は100件）。ページネーションはpage方式（1始まり）で、レスポンスに総件数は"
                "含まれない。並び順は storeId, storeCode, displaySequence, updDateTime のいずれかを指定可能で、既定の"
                "並び順はAPI仕様上明記されていない（ドキュメントで確認できず）。読み取り専用。スマレジAPIには店舗の"
                "新規作成（POST）・更新（PATCH）・削除（DELETE）に対応するエンドポイントも存在するが、本コネクタでは"
                "未実装（閲覧のみ）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "取得件数（最大1000、既定100）", "default": 100},
                    "page": {"type": "integer", "description": "ページ番号（1始まり、既定1）", "default": 1},
                    "store_code": {"type": "string", "description": "店舗コードで絞り込み"},
                    "sort": {
                        "type": "string",
                        "description": (
                            "並び順。storeId, storeCode, displaySequence, updDateTime のいずれかを指定し、"
                            "降順にしたい場合は「フィールド名:desc」の形式で指定する（例: displaySequence:desc）。"
                        ),
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_products":
                params: dict = {
                    "limit": arguments.get("limit", 100),
                    "page": arguments.get("page", 1),
                }
                if arguments.get("category_id"):
                    params["category_id"] = arguments["category_id"]
                if arguments.get("product_code"):
                    params["product_code"] = arguments["product_code"]
                if arguments.get("group_code"):
                    params["group_code"] = arguments["group_code"]
                if arguments.get("sort"):
                    params["sort"] = arguments["sort"]
                r = client.get("/products/", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_product":
                r = client.get(f"/products/{arguments['product_id']}")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_transactions":
                params = {
                    "limit": arguments.get("limit", 100),
                    "page": arguments.get("page", 1),
                }
                if arguments.get("store_id"):
                    params["store_id"] = arguments["store_id"]
                if arguments.get("transaction_date_time_from"):
                    params["transaction_date_time-from"] = arguments["transaction_date_time_from"]
                if arguments.get("transaction_date_time_to"):
                    params["transaction_date_time-to"] = arguments["transaction_date_time_to"]
                if arguments.get("customer_code"):
                    params["customer_code"] = arguments["customer_code"]
                r = client.get("/transactions/", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_customers":
                params = {
                    "limit": arguments.get("limit", 100),
                    "page": arguments.get("page", 1),
                }
                if arguments.get("customer_code"):
                    params["customer_code"] = arguments["customer_code"]
                if arguments.get("customer_no"):
                    params["customer_no"] = arguments["customer_no"]
                if arguments.get("customer_id_from"):
                    params["customer_id-from"] = arguments["customer_id_from"]
                if arguments.get("customer_id_to"):
                    params["customer_id-to"] = arguments["customer_id_to"]
                r = client.get("/customers/", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_stock":
                params = {
                    "limit": arguments.get("limit", 100),
                    "page": arguments.get("page", 1),
                }
                if arguments.get("store_id"):
                    params["store_id"] = arguments["store_id"]
                if arguments.get("product_id"):
                    params["product_id"] = arguments["product_id"]
                if arguments.get("upd_date_time_from"):
                    params["upd_date_time-from"] = arguments["upd_date_time_from"]
                if arguments.get("upd_date_time_to"):
                    params["upd_date_time-to"] = arguments["upd_date_time_to"]
                if arguments.get("sort"):
                    params["sort"] = arguments["sort"]
                r = client.get("/stock/", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_stock_changes":
                params = {
                    "limit": arguments.get("limit", 100),
                    "page": arguments.get("page", 1),
                }
                if arguments.get("id"):
                    params["id"] = arguments["id"]
                if arguments.get("target_date"):
                    params["target_date"] = arguments["target_date"]
                if arguments.get("stock_division"):
                    params["stock_division"] = arguments["stock_division"]
                if arguments.get("from_store_id"):
                    params["from_store_id"] = arguments["from_store_id"]
                if arguments.get("to_store_id"):
                    params["to_store_id"] = arguments["to_store_id"]
                if arguments.get("sort"):
                    params["sort"] = arguments["sort"]
                r = client.get(
                    f"/stock/changes/{arguments['product_id']}/{arguments['store_id']}",
                    params=params,
                )
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_transaction_details":
                params = {
                    "limit": arguments.get("limit", 100),
                    "page": arguments.get("page", 1),
                }
                if arguments.get("with_discounts"):
                    params["with_discounts"] = arguments["with_discounts"]
                if arguments.get("with_detail_product_attributes"):
                    params["with_detail_product_attributes"] = arguments["with_detail_product_attributes"]
                if arguments.get("sort"):
                    params["sort"] = arguments["sort"]
                r = client.get(f"/transactions/{arguments['transaction_id']}/details", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_categories":
                params = {
                    "limit": arguments.get("limit", 100),
                    "page": arguments.get("page", 1),
                }
                if arguments.get("category_code"):
                    params["category_code"] = arguments["category_code"]
                if arguments.get("level"):
                    params["level"] = arguments["level"]
                if arguments.get("sort"):
                    params["sort"] = arguments["sort"]
                r = client.get("/categories/", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_stores":
                params = {
                    "limit": arguments.get("limit", 100),
                    "page": arguments.get("page", 1),
                }
                if arguments.get("store_code"):
                    params["store_code"] = arguments["store_code"]
                if arguments.get("sort"):
                    params["sort"] = arguments["sort"]
                r = client.get("/stores/", params=params)
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
