import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("yappli-crm-mcp")

_token_cache: str | None = None

# create_user / update_user で共通利用する会員フィールド
# （Yappli CRM Open API は name/email/birthday/gender のような固定の個人情報項目を
# 持たず、login_id・rank・カスタムフィールド column01〜column50 で表現する）
_USER_FIELDS = ("unique_id", "login_id", "password", "rank", "secret_question", "secret_answer")


def _build_user_body(arguments: dict) -> dict:
    body: dict = {}
    for key in _USER_FIELDS:
        if arguments.get(key) is not None:
            body[key] = arguments[key]
    if arguments.get("logined") is not None:
        body["logined"] = arguments["logined"]
    if arguments.get("logined_at") is not None:
        body["logined_at"] = arguments["logined_at"]
    if arguments.get("enabled") is not None:
        body["enabled"] = arguments["enabled"]
    if arguments.get("columns"):
        # columns は {"column01": "値", ...} または管理画面で設定したキー名を想定
        body.update(arguments["columns"])
    if arguments.get("external_ids"):
        body["external_ids"] = arguments["external_ids"]
    return body


def _base_url() -> str:
    url = os.environ.get("YAPPLI_CRM_APP_URL")
    if not url:
        raise ValueError("YAPPLI_CRM_APP_URL が設定されていません")
    return url.rstrip("/")


def _get_token() -> str:
    global _token_cache
    if _token_cache:
        return _token_cache
    client_id = os.environ.get("YAPPLI_CRM_CLIENT_ID")
    client_secret = os.environ.get("YAPPLI_CRM_CLIENT_SECRET")
    if not client_id:
        raise ValueError("YAPPLI_CRM_CLIENT_ID が設定されていません")
    if not client_secret:
        raise ValueError("YAPPLI_CRM_CLIENT_SECRET が設定されていません")
    r = httpx.post(
        f"{_base_url()}/api/ext/token",
        json={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={"Content-Type": "application/json", "User-Agent": "yappli-crm-mcp/0.1.0"},
        timeout=30,
    )
    r.raise_for_status()
    _token_cache = r.json()["access_token"]
    return _token_cache


def _client() -> httpx.Client:
    return httpx.Client(
        base_url=f"{_base_url()}/api/ext",
        headers={
            "Authorization": f"Bearer {_get_token()}",
            "Content-Type": "application/json",
            "User-Agent": "yappli-crm-mcp/0.1.0",
        },
        timeout=30,
    )


_USER_WRITE_PROPERTIES = {
    "unique_id": {
        "type": "string",
        "description": "お客様側システムで一意な会員識別子（省略可。指定する場合は1文字以上）。会員の名寄せや外部システムとの突き合わせに使う。",
    },
    "login_id": {
        "type": "string",
        "description": "エンドユーザーのログインID（メールアドレス等）。省略または空文字のままだと、後から有効な値に更新するまでアプリ側からログインできない。",
    },
    "password": {
        "type": "string",
        "description": "ログインパスワード（指定する場合は4文字以上）。省略すると、後から有効な値に更新するまでログインできない。",
    },
    "rank": {
        "type": "string",
        "description": "会員ランク（1文字以上）。管理画面でランク機能が無効化されている場合のみ任意の値を設定できる。",
    },
    "secret_question": {"type": "string", "description": "秘密の質問"},
    "secret_answer": {"type": "string", "description": "秘密の質問の答え"},
    "logined": {
        "type": "integer",
        "description": "ログイン状態（0:未ログイン, 1:ログイン済）。1に設定する場合は logined_at も併せて必須。",
    },
    "logined_at": {
        "type": "string",
        "description": "最終ログイン日時（フォーマット: 'YYYY-MM-DD HH:MM:SS'）。logined=1 に設定する場合は必須。",
    },
    "enabled": {"type": "integer", "description": "利用可否（0:利用不可, 1:利用可）"},
    "columns": {
        "type": "object",
        "description": (
            "カスタムフィールドの値。キーは 'column01'〜'column50'、または管理画面でカスタムフィールドに"
            "設定したキー名（例: 'name', 'birthday'）。氏名・メール・生年月日・性別など固定の個人情報項目は"
            "Yappli CRM API に存在せず、すべてこのカスタムフィールド経由で表現される点に注意。"
        ),
    },
    "external_ids": {
        "type": "object",
        "description": (
            "外部連携キーと外部連携ID（例: POSシステムやECサイトのユーザーID）の組。値には英数字と `*-_.` の"
            "4記号のみ使用可。外部連携キーは事前にYappli側で設定した値のみ使用できる。"
        ),
    },
}


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_users",
            description=(
                "Yappli CRMに登録されている会員（顧客）の一覧を取得する。全会員の棚卸しや件数確認など、"
                "全体像の把握に使う。ページネーションはオフセット方式（page/per_page）で、"
                "1回のリクエストで最大1000件（既定50件）取得できる。レスポンスには total（総数）・"
                "current_page・last_page が含まれるため、これらを見て次ページの有無を判断する。"
                "並び順はAPIドキュメントに明記されていないため、特定の順序を前提にしないこと。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "取得開始ページ番号（既定1）", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの取得件数（最大1000、既定50）", "default": 50},
                },
            },
        ),
        types.Tool(
            name="get_user",
            description=(
                "YappliCRMの会員ID（内部ID）を指定して、会員1件の詳細情報（ランク・保有ポイント・"
                "カスタムフィールド・ログイン状態など）を取得する。お客様システム側のIDで検索したい場合は "
                "get_user_by_unique_id、外部連携IDで検索したい場合は get_user_by_external_id を使う。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "YappliCRMの会員ID"},
                    "with_column_key": {
                        "type": "boolean",
                        "description": "true にすると column01〜column50 を管理画面で設定したキー名で返す（既定false）",
                        "default": False,
                    },
                },
                "required": ["user_id"],
            },
        ),
        types.Tool(
            name="get_user_by_unique_id",
            description=(
                "会員登録時に指定した unique_id（お客様側システムでの一意な識別子）で会員1件の詳細情報を検索する。"
                "自社システムの顧客IDからYappliCRM側の会員情報を引きたい場合に使う。該当する会員がいない場合は"
                "404エラーになる。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "unique_id": {"type": "string", "description": "お客様側システムでの一意な会員識別子（create_user/update_userで設定した値）"},
                    "with_column_key": {
                        "type": "boolean",
                        "description": "true にすると column01〜column50 を管理画面で設定したキー名で返す（既定false）",
                        "default": False,
                    },
                },
                "required": ["unique_id"],
            },
        ),
        types.Tool(
            name="get_user_by_external_id",
            description=(
                "外部連携ID（POSシステムやECサイトなど、連携している外部サービス側のID。create_user/update_userの "
                "external_ids で保存した値）で会員1件の詳細情報を検索する。外部連携キーは事前にYappli側で"
                "設定されたものだけが使用できる。該当する会員がいない場合は404エラーになる。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "external_key": {"type": "string", "description": "お客様のシステムごとに設定されている外部連携キー"},
                    "external_id": {"type": "string", "description": "外部連携ID"},
                },
                "required": ["external_key", "external_id"],
            },
        ),
        types.Tool(
            name="create_user",
            description=(
                "新規会員を登録する。氏名・メールアドレス・生年月日・性別のような固定の個人情報項目は"
                "APIに存在せず、columns（column01〜column50、または管理画面設定済みのキー名）で表現する点に注意。"
                "unique_id・login_id・password はいずれも省略可能だが、login_id または password を省略したままだと"
                "後で update_user により有効な値へ更新するまでエンドユーザーはアプリにログインできない。"
                "unique_id の重複チェックの挙動はドキュメントに明記されていないため、同じunique_idで複数回呼ぶと"
                "重複登録される可能性がある想定で運用すること（べき等性は保証されていない）。会員の削除APIは"
                "提供されていない。"
            ),
            inputSchema={
                "type": "object",
                "properties": dict(_USER_WRITE_PROPERTIES),
            },
        ),
        types.Tool(
            name="update_user",
            description=(
                "既存会員（YappliCRMの会員ID指定）の情報を更新する。login_id・password・rank・columns・"
                "external_ids など、create_user と同じ項目を指定できる。省略した項目が更新時に維持されるか"
                "クリアされるかはAPIドキュメントに明記されていないため、初回利用時はレスポンスで実際の挙動を"
                "確認すること。会員そのものを削除するAPIは提供されていない（削除できるのは外部連携IDのみ。"
                "delete_external_id を参照）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "更新対象のYappliCRM会員ID"},
                    **_USER_WRITE_PROPERTIES,
                },
                "required": ["user_id"],
            },
        ),
        types.Tool(
            name="delete_external_id",
            description=(
                "会員に紐づく外部連携ID（POSシステムやECサイトなどのID）を1件削除し、連携を解除する。"
                "成功時は204でレスポンスボディは空。存在しない外部連携キーを指定すると400エラー（"
                "'External ID not found'）になるため、べき等ではない（2回目の削除は失敗する）。"
                "会員そのものやログインID・パスワードの削除はできない（会員の削除APIは提供されていない）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "対象のYappliCRM会員ID"},
                    "key": {"type": "string", "description": "削除する外部連携キー"},
                },
                "required": ["user_id", "key"],
            },
        ),
        types.Tool(
            name="get_user_points",
            description=(
                "会員に対して行われたポイント付与・減算の履歴を取得する。登録日の新しい順で返る。"
                "現在の保有ポイント総数は get_user のレスポンス（point / total_point フィールド）で確認できる。"
                "ページネーションはオフセット方式（page/per_page）で、1回のリクエストで最大1000件（既定50件）"
                "取得できる。ポイントの有効期限別の集計を見たい場合は get_points_expired_list を使う。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "対象のYappliCRM会員ID"},
                    "page": {"type": "integer", "description": "取得開始ページ番号（既定1）", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの取得件数（最大1000、既定50）", "default": 50},
                },
                "required": ["user_id"],
            },
        ),
        types.Tool(
            name="get_points_expired_list",
            description=(
                "会員が保有するポイントのうち、有効期限が近い順に有効期限日ごとの失効予定ポイント数を"
                "集計して取得する（個々の付与履歴ではなく、期限日単位のサマリ）。「まもなく失効するポイントが"
                "あるか」を確認する用途に使う。付与履歴そのものを見たい場合は get_user_points を使う。"
                "ページネーションはオフセット方式（page/per_page、最大1000件・既定50件）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "対象のYappliCRM会員ID"},
                    "page": {"type": "integer", "description": "取得開始ページ番号（既定1）", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの取得件数（最大1000、既定50）", "default": 50},
                },
                "required": ["user_id"],
            },
        ),
        types.Tool(
            name="add_user_points",
            description=(
                "会員にポイントを付与（正の値）または減算（負の値）する。呼び出すたびに新しい付与・減算"
                "レコードが追加される加算処理であり、べき等ではない（同じ内容で2回呼ぶとポイントが二重に"
                "動く）。加算時に expired_at を省略すると、管理画面のポイント種別・デフォルト有効期限設定に"
                "従って自動的に有効期限が設定される。減算時は expired_at を指定しても無視される。"
                "ランク別のポイント付与率で自動計算したい場合は calculate_points を使う。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "対象のYappliCRM会員ID"},
                    "point": {"type": "integer", "description": "付与ポイント数（負の値を指定すると減算になる）"},
                    "title": {"type": "string", "description": "付与・減算理由（エンドユーザーのアプリ画面に表示される可能性がある項目）"},
                    "expired_at": {
                        "type": "string",
                        "description": "ポイント有効期限（'YYYY-MM-DD'形式、時刻は23:59:59固定）。減算時は指定しても無視される。",
                    },
                    "remarks": {"type": "string", "description": "備考欄（システム内部のメモ用途、エンドユーザーには非表示）"},
                },
                "required": ["user_id", "point"],
            },
        ),
        types.Tool(
            name="calculate_points",
            description=(
                "Yappli CRMの環境設定で定義されたランク別のポイント付与率を使い、指定した計算対象額（amount）から"
                "自動算出したポイント数を会員に付与する。add_user_points と異なりamountは負の値にできない"
                "（このAPIでは減算はできない）。expired_atを省略した場合の有効期限設定ルールは add_user_points と"
                "同様（ポイント種別・デフォルト期限に従う）。呼び出すたびに新しい付与レコードが追加されるため"
                "べき等ではない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "対象のYappliCRM会員ID"},
                    "amount": {"type": "integer", "description": "ポイント計算対象の金額・数量（負の値は不可。減算不可）"},
                    "title": {"type": "string", "description": "付与理由（エンドユーザーのアプリ画面に表示される可能性がある項目）"},
                    "expired_at": {"type": "string", "description": "ポイント有効期限（'YYYY-MM-DD'形式、時刻は23:59:59固定）"},
                    "remarks": {"type": "string", "description": "備考欄（システム内部のメモ用途、エンドユーザーには非表示）"},
                },
                "required": ["user_id", "amount"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        return _dispatch(name, arguments)
    except Exception as exc:  # noqa: BLE001
        return error_response(exc)


def _dispatch(name: str, arguments: dict) -> list[types.TextContent]:
    with _client() as client:
        if name == "list_users":
            params: dict = {}
            if arguments.get("page"):
                params["page"] = arguments["page"]
            if arguments.get("per_page"):
                params["per_page"] = arguments["per_page"]
            r = client.get("/users", params=params)

        elif name == "get_user":
            params = {}
            if arguments.get("with_column_key") is not None:
                params["with_column_key"] = arguments["with_column_key"]
            r = client.get(f"/users/{arguments['user_id']}", params=params)

        elif name == "get_user_by_unique_id":
            params = {}
            if arguments.get("with_column_key") is not None:
                params["with_column_key"] = arguments["with_column_key"]
            r = client.get(f"/users/unique_id/{arguments['unique_id']}", params=params)

        elif name == "get_user_by_external_id":
            external_key = arguments["external_key"]
            external_id = arguments["external_id"]
            r = client.get(f"/users/external_id/{external_key}/{external_id}")

        elif name == "create_user":
            r = client.post("/users", json=_build_user_body(arguments))

        elif name == "update_user":
            r = client.put(f"/users/{arguments['user_id']}", json=_build_user_body(arguments))

        elif name == "delete_external_id":
            r = client.request(
                "DELETE", f"/users/{arguments['user_id']}/external_ids/{arguments['key']}"
            )
            r.raise_for_status()
            return format_response({"status": "deleted", "user_id": arguments["user_id"], "key": arguments["key"]})

        elif name == "get_user_points":
            params = {}
            if arguments.get("page"):
                params["page"] = arguments["page"]
            if arguments.get("per_page"):
                params["per_page"] = arguments["per_page"]
            r = client.get(f"/users/{arguments['user_id']}/points", params=params)

        elif name == "get_points_expired_list":
            params = {}
            if arguments.get("page"):
                params["page"] = arguments["page"]
            if arguments.get("per_page"):
                params["per_page"] = arguments["per_page"]
            r = client.get(f"/users/{arguments['user_id']}/points/expired_list", params=params)

        elif name == "add_user_points":
            body: dict = {"point": arguments["point"]}
            if arguments.get("title"):
                body["title"] = arguments["title"]
            if arguments.get("expired_at"):
                body["expired_at"] = arguments["expired_at"]
            if arguments.get("remarks"):
                body["remarks"] = arguments["remarks"]
            r = client.post(f"/users/{arguments['user_id']}/points", json=body)

        elif name == "calculate_points":
            body = {"amount": arguments["amount"]}
            if arguments.get("title"):
                body["title"] = arguments["title"]
            if arguments.get("expired_at"):
                body["expired_at"] = arguments["expired_at"]
            if arguments.get("remarks"):
                body["remarks"] = arguments["remarks"]
            r = client.post(f"/users/{arguments['user_id']}/points/calculation", json=body)

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
