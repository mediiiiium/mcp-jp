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

# トークン発行時に要求するスコープ（スペース区切り）。
# Developer Console のアプリに同意されていないスコープを要求するとトークン発行自体が
# 失敗し、全ツールが使えなくなる。ディレクトリ系（orgunit/group）を使わない環境では
# LINEWORKS_SCOPE="bot user.read" のように絞って上書きできるようにしておく。
DEFAULT_SCOPE = "bot user.read orgunit.read group.read"


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

    scope = os.environ.get("LINEWORKS_SCOPE") or DEFAULT_SCOPE

    r = httpx.post(
        AUTH_URL,
        data={
            "assertion": assertion,
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": scope,
        },
        timeout=30,
    )
    if r.status_code >= 400:
        # 未同意スコープを要求すると発行が丸ごと失敗する。生の 400 だけ返すと
        # 「今まで動いていたのに急に全ツールが死んだ」原因に辿り着けないため、
        # 何を確認すべきかをメッセージに含める。
        raise ValueError(
            f"LINE WORKS のアクセストークン取得に失敗しました（HTTP {r.status_code}）: "
            f"{r.text[:300]}\n"
            f"要求したスコープ: {scope}\n"
            "Developer Console のアプリでこれらのスコープが同意されているか確認してください。"
            "ディレクトリ系（組織・グループ）のツールを使わない場合は、環境変数 "
            'LINEWORKS_SCOPE="bot user.read" のように絞ることで回避できます。'
        )
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
        types.Tool(
            name="search_users",
            description=(
                "テナント内のメンバーを氏名などのキーワードで検索する。list_members はページを順送りするだけで"
                "名前による絞り込みができないため、『○○さんの連絡先を教えて』のように特定の1名を氏名で探したい"
                "場合はこちらの方が少ないリクエストで済む。query には1〜100文字の検索語を指定する（GET "
                "/users/search、公式ドキュメントで実在確認済み）。並び順は既定で氏名昇順（userName asc）。"
                "ページネーションはカーソル方式で、responseMetaData.nextCursor を次回の cursor に渡す。読み取り"
                "専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "検索キーワード（氏名など、1〜100文字）。",
                    },
                    "order_by": {
                        "type": "string",
                        "description": "並び替え。'userName asc'（氏名昇順、既定）または 'userName desc'（氏名降順）。",
                        "enum": ["userName asc", "userName desc"],
                    },
                    "count": {
                        "type": "integer",
                        "description": "1回で取得する件数（1〜100、省略時は100）。",
                        "default": 100,
                    },
                    "cursor": {
                        "type": "string",
                        "description": "前回レスポンスの responseMetaData.nextCursor の値。続きのページを取得する際に指定する。",
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="list_orgunits",
            description=(
                "テナントの組織（部署・事業部など）一覧を取得する（GET /orgunits、公式ドキュメントで実在確認"
                "済み）。各組織は orgUnitId・orgUnitName・parentOrgUnitId（親組織ID、階層構造を表す）・"
                "displayLevel（階層の深さ）などを含む。『会社にどんな部署がありますか』のように組織図を把握"
                "したい場合に使う。ページネーションはカーソル方式（responseMetaData.nextCursor）。読み取り専用。"
                "組織の登録・更新・削除・移動APIもLINE WORKS側に存在するが、本コネクタは読み取り専用のため"
                "未実装。"
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
                },
            },
        ),
        types.Tool(
            name="get_orgunit",
            description=(
                "特定の組織（部署）1件の詳細情報（組織名・メールアドレス・説明・親組織ID・トーク/ノート/"
                "カレンダー等の各機能利用フラグなど）を取得する（GET /orgunits/{orgUnitId}、公式ドキュメントで"
                "実在確認済み）。org_unit_id には組織の内部ID、または externalKey:{組織外部キー} 形式を指定"
                "できる。list_orgunits で対象の orgUnitId を把握してから、その1件の詳細だけを見たい場合に使う。"
                "読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "org_unit_id": {
                        "type": "string",
                        "description": "組織の内部ID、または externalKey:{組織外部キー} 形式。",
                    },
                },
                "required": ["org_unit_id"],
            },
        ),
        types.Tool(
            name="list_orgunit_members",
            description=(
                "特定の組織（部署）に所属するメンバー一覧を取得する（GET /orgunits/{orgUnitId}/members、公式"
                "ドキュメントで実在確認済み）。org_unit_id には組織の内部ID、または externalKey:{組織外部キー} "
                "形式を指定する。flatten=true を指定すると下位組織（子組織）のメンバーも含めて取得できる（既定"
                "は false で直下のメンバーのみ）。『営業部のメンバーを教えて』のような問い合わせに使う。返る"
                "のは userId 等の簡易情報のみで、氏名や連絡先の詳細が必要な場合は get_member と組み合わせる。"
                "ページネーションはカーソル方式（responseMetaData.nextCursor）。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "org_unit_id": {
                        "type": "string",
                        "description": "組織の内部ID、または externalKey:{組織外部キー} 形式。",
                    },
                    "flatten": {
                        "type": "boolean",
                        "description": "true にすると下位組織のメンバーも含めて取得する（既定は false）。",
                        "default": False,
                    },
                    "count": {
                        "type": "integer",
                        "description": "1回で取得する件数（1〜100、省略時は100）。",
                        "default": 100,
                    },
                    "cursor": {
                        "type": "string",
                        "description": "前回レスポンスの responseMetaData.nextCursor の値。続きのページを取得する際に指定する。",
                    },
                },
                "required": ["org_unit_id"],
            },
        ),
        types.Tool(
            name="list_groups",
            description=(
                "テナントのグループ（プロジェクトチーム・委員会など、組織階層とは別に作られる横断的なグループ）"
                "一覧を取得する（GET /groups、公式ドキュメントで実在確認済み）。各グループは groupId・"
                "groupName・description・groupEmail などを含む。『社内にどんなグループがありますか』のような"
                "問い合わせに使う。ページネーションはカーソル方式（responseMetaData.nextCursor）。読み取り専用。"
                "グループの登録・更新・削除・メンバー管理APIもLINE WORKS側に存在するが、本コネクタは読み取り"
                "専用のため未実装。"
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
                },
            },
        ),
        types.Tool(
            name="get_group",
            description=(
                "特定のグループ1件の詳細情報（グループ名・説明・グループメールアドレス・管理者一覧・メンバー"
                "一覧・各機能利用フラグなど）を取得する（GET /groups/{groupId}、公式ドキュメントで実在確認"
                "済み。ただし外部グループの取得には対応していないと公式ドキュメントに明記されている）。"
                "group_id にはグループの内部ID、または externalKey:{グループ外部キー} 形式を指定できる。"
                "list_groups で対象の groupId を把握してから、その1件の詳細だけを見たい場合に使う。読み取り"
                "専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "group_id": {
                        "type": "string",
                        "description": "グループの内部ID、または externalKey:{グループ外部キー} 形式。",
                    },
                },
                "required": ["group_id"],
            },
        ),
        types.Tool(
            name="list_group_members",
            description=(
                "特定のグループに所属するメンバー一覧を取得する（GET /groups/{groupId}/members、公式ドキュメント"
                "で実在確認済み）。group_id にはグループの内部ID、または externalKey:{グループ外部キー} 形式を"
                "指定する。メンバーは USER（ユーザー）だけでなく ORGUNIT（組織）や GROUP（別グループ）が"
                "含まれる場合があり、type フィールドで区別できる。flatten=true を指定すると入れ子になった"
                "組織・グループのメンバーも展開して取得できる（既定は false）。『プロジェクトAチームのメンバー"
                "を教えて』のような問い合わせに使う。ページネーションはカーソル方式（responseMetaData."
                "nextCursor）。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "group_id": {
                        "type": "string",
                        "description": "グループの内部ID、または externalKey:{グループ外部キー} 形式。",
                    },
                    "flatten": {
                        "type": "boolean",
                        "description": "true にすると入れ子の組織・グループのメンバーも展開して取得する（既定は false）。",
                        "default": False,
                    },
                    "count": {
                        "type": "integer",
                        "description": "1回で取得する件数（1〜100、省略時は100）。",
                        "default": 100,
                    },
                    "cursor": {
                        "type": "string",
                        "description": "前回レスポンスの responseMetaData.nextCursor の値。続きのページを取得する際に指定する。",
                    },
                },
                "required": ["group_id"],
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

            elif name == "search_users":
                params: dict = {
                    "query": arguments["query"],
                    "count": arguments.get("count", 100),
                }
                if arguments.get("order_by"):
                    params["orderBy"] = arguments["order_by"]
                if arguments.get("cursor"):
                    params["cursor"] = arguments["cursor"]
                r = client.get("/users/search", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_orgunits":
                params = {"count": arguments.get("count", 100)}
                if arguments.get("cursor"):
                    params["cursor"] = arguments["cursor"]
                r = client.get("/orgunits", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_orgunit":
                r = client.get(f"/orgunits/{arguments['org_unit_id']}")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_orgunit_members":
                params = {"count": arguments.get("count", 100)}
                if arguments.get("cursor"):
                    params["cursor"] = arguments["cursor"]
                if arguments.get("flatten") is not None:
                    params["flatten"] = arguments["flatten"]
                r = client.get(f"/orgunits/{arguments['org_unit_id']}/members", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_groups":
                params = {"count": arguments.get("count", 100)}
                if arguments.get("cursor"):
                    params["cursor"] = arguments["cursor"]
                r = client.get("/groups", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_group":
                r = client.get(f"/groups/{arguments['group_id']}")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_group_members":
                params = {"count": arguments.get("count", 100)}
                if arguments.get("cursor"):
                    params["cursor"] = arguments["cursor"]
                if arguments.get("flatten") is not None:
                    params["flatten"] = arguments["flatten"]
                r = client.get(f"/groups/{arguments['group_id']}/members", params=params)
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
