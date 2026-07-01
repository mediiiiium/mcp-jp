import os
import time
import httpx
import jwt
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("lineworks-mcp")
BASE_URL = "https://www.worksapis.com/v1.0"
AUTH_URL = "https://auth.worksmobile.com/oauth2/v2.0/token"


def _get_access_token() -> str:
    client_id = os.environ.get("LINEWORKS_CLIENT_ID")
    client_secret = os.environ.get("LINEWORKS_CLIENT_SECRET")
    service_account_id = os.environ.get("LINEWORKS_SERVICE_ACCOUNT_ID")
    private_key = os.environ.get("LINEWORKS_PRIVATE_KEY", "").replace("\\n", "\n")

    if not all([client_id, client_secret, service_account_id, private_key]):
        raise ValueError(
            "LINEWORKS_CLIENT_ID, LINEWORKS_CLIENT_SECRET, "
            "LINEWORKS_SERVICE_ACCOUNT_ID, LINEWORKS_PRIVATE_KEY が必要です"
        )

    now = int(time.time())
    payload = {
        "iss": client_id,
        "sub": service_account_id,
        "iat": now,
        "exp": now + 3600,
    }
    assertion = jwt.encode(payload, private_key, algorithm="RS256")

    r = httpx.post(
        AUTH_URL,
        data={
            "assertion": assertion,
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "bot user.read",
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def _client() -> httpx.Client:
    token = _get_access_token()
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )


def _bot_id() -> str:
    bot_id = os.environ.get("LINEWORKS_BOT_ID")
    if not bot_id:
        raise ValueError("LINEWORKS_BOT_ID が設定されていません")
    return bot_id


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_channel",
            description=(
                "Bot が参加している特定のトークルーム（チャンネル）1件の情報（タイトル・チャンネル種別"
                "SINGLE_USER/MULTI_USERS/ORGUNIT/GROUP など）を取得する。channel_id は事前に把握している"
                "必要があり、通常は Bot への着信コールバック（webhook）イベントのペイロードに含まれる"
                "channelId から得る。LINE WORKS Bot API には『Bot が参加している全トークルーム一覧を取得する』"
                "エンドポイントは存在しない（公式ドキュメント・コミュニティフォーラムで確認済みで、以前の実装は"
                "存在しない一覧取得エンドポイントを叩いており動作しなかったため本ツール名を list_channels から"
                "get_channel に変更し、1件取得のみに対応する形へ修正した）。なお Bot が新規にトークルームを"
                "作成する登録API（POST /bots/{botId}/channels、メンバー1〜100名を指定）も LINE WORKS 側には"
                "存在するが、本コネクタでは未実装。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": (
                            "取得するトークルームのチャンネルID（UUID形式）。Bot への着信メッセージの"
                            "webhookペイロードに含まれる channelId などから取得する。"
                        ),
                    },
                },
                "required": ["channel_id"],
            },
        ),
        types.Tool(
            name="send_channel_message",
            description=(
                "指定したトークルーム（チャンネル）にテキストメッセージを Bot から送信する。channel_id は "
                "get_channel で確認できる値、または Bot への着信イベントに含まれる channelId を指定する。"
                "呼び出すたびに新規メッセージが1件送信される操作であり、同じ内容で複数回呼んでも1件にまとまる"
                "ことはない（べき等ではない）ため、二重送信に注意すること。本文はLINE WORKS API仕様上最大"
                "2000文字までで、超えるとAPIがエラーを返す。ボタン・リスト・カルーセル・画像カルーセルなど"
                "他のメッセージタイプもAPIには存在するが、本コネクタはテキスト送信のみ実装。送信済み"
                "メッセージを取り消す・編集するAPIはLINE WORKS Bot APIに存在しないため、誤送信した内容を"
                "この経路で訂正することはできない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "送信先トークルームのチャンネルID（UUID形式）。get_channel や着信イベントから取得する。",
                    },
                    "text": {
                        "type": "string",
                        "description": "送信するメッセージ本文（最大2000文字。超えるとAPIがエラーを返す）。",
                    },
                },
                "required": ["channel_id", "text"],
            },
        ),
        types.Tool(
            name="send_user_message",
            description=(
                "Bot から特定のユーザー1名にダイレクトメッセージ（テキスト）を送信する。user_id にはユーザーID、"
                "ログインID（メールアドレス）のいずれかを指定できる。呼び出すたびに新規メッセージが1件送信"
                "される操作であり、同じ内容で複数回呼んでも1件にまとまることはない（べき等ではない）ため、"
                "二重送信に注意すること。本文は最大2000文字まで。ボタン・リスト・カルーセルなど他のメッセージ"
                "タイプもAPIには存在するが、本コネクタはテキスト送信のみ実装。送信済みメッセージを取り消す・"
                "編集するAPIはLINE WORKS Bot APIに存在しないため、誤送信した内容をこの経路で訂正することは"
                "できない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "送信先ユーザーのユーザーID、またはログインID（メールアドレス）。",
                    },
                    "text": {
                        "type": "string",
                        "description": "送信するメッセージ本文（最大2000文字。超えるとAPIがエラーを返す）。",
                    },
                },
                "required": ["user_id", "text"],
            },
        ),
        types.Tool(
            name="list_members",
            description=(
                "テナント（ドメイン）に所属するメンバー（ユーザー）一覧を取得する。ページネーションはカーソル"
                "方式で、レスポンスの responseMetaData.nextCursor を次回呼び出しの cursor にそのまま渡すと"
                "続きを取得できる（nextCursor が返らなければ最終ページ）。count は1〜100件で指定でき、省略時"
                "は100件（API既定）。既定の並び順は作成日時の昇順（order_by=CREATED_TIME, sort_order="
                "ASCENDING）で、氏名順（NAME）や降順（DESCENDING）への変更も可能。search_filter_type に "
                "'VIP' を指定すると、よく使う連絡先のみに絞り込める（それ以外の絞り込みパラメータはAPIに"
                "存在しない）。特定の1名だけが必要な場合は get_member の方が少ないリクエストで済む。読み取り"
                "専用。ユーザーの新規作成・更新・削除APIもLINE WORKS側に存在するが、本コネクタは読み取り専用"
                "のため未実装。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "count": {
                        "type": "integer",
                        "description": "1回で取得する件数（1〜100、省略時は100）。",
                        "default": 100,
                    },
                    "cursor": {
                        "type": "string",
                        "description": "前回レスポンスの responseMetaData.nextCursor の値。続きのページを取得する際に指定する。",
                    },
                    "order_by": {
                        "type": "string",
                        "description": "並び替え対象フィールド。NAME（氏名順）または CREATED_TIME（作成日時順、既定）。",
                        "enum": ["NAME", "CREATED_TIME"],
                    },
                    "sort_order": {
                        "type": "string",
                        "description": "並び順。ASCENDING（昇順、既定）または DESCENDING（降順）。",
                        "enum": ["ASCENDING", "DESCENDING"],
                    },
                    "search_filter_type": {
                        "type": "string",
                        "description": "絞り込み種別。'VIP' を指定するとよく使う連絡先のみに絞り込む。",
                        "enum": ["VIP"],
                    },
                },
            },
        ),
        types.Tool(
            name="get_member",
            description=(
                "特定メンバー1名の詳細情報（氏名、所属組織・部署・役職、電話番号、雇用状態などのフラグ）を"
                "取得する。user_id にはユーザーID、ログインID（メールアドレス）、または "
                "externalKey:{ユーザー外部キー} 形式のいずれかを指定できる。一覧から探すのではなく特定の1名"
                "の情報だけが欲しい場合、list_members より少ないリクエストで済む。書き込みは行わない。ユーザー"
                "の更新・削除APIもLINE WORKS側に存在するが、本コネクタは読み取り専用のため未実装。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "ユーザーID、ログインID（メールアドレス）、または externalKey:{ユーザー外部キー} 形式のいずれか。",
                    },
                },
                "required": ["user_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            bot_id = _bot_id()

            if name == "get_channel":
                r = client.get(f"/bots/{bot_id}/channels/{arguments['channel_id']}")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "send_channel_message":
                payload = {
                    "content": {
                        "type": "text",
                        "text": arguments["text"],
                    }
                }
                r = client.post(f"/bots/{bot_id}/channels/{arguments['channel_id']}/messages", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "send_user_message":
                payload = {
                    "content": {
                        "type": "text",
                        "text": arguments["text"],
                    }
                }
                r = client.post(f"/bots/{bot_id}/users/{arguments['user_id']}/messages", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_members":
                params: dict = {"count": arguments.get("count", 100)}
                if arguments.get("cursor"):
                    params["cursor"] = arguments["cursor"]
                if arguments.get("order_by"):
                    params["orderBy"] = arguments["order_by"]
                if arguments.get("sort_order"):
                    params["sortOrder"] = arguments["sort_order"]
                if arguments.get("search_filter_type"):
                    params["searchFilterType"] = arguments["search_filter_type"]
                r = client.get("/users", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_member":
                r = client.get(f"/users/{arguments['user_id']}")
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
