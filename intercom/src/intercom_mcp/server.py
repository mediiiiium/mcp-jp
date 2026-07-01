import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("intercom-mcp")
BASE_URL = "https://api.intercom.io"
INTERCOM_VERSION = "2.11"


def _client() -> httpx.Client:
    access_token = os.environ.get("INTERCOM_ACCESS_TOKEN")
    if not access_token:
        raise ValueError("INTERCOM_ACCESS_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Intercom-Version": INTERCOM_VERSION,
        },
        timeout=30,
    )


_STARTING_AFTER_DESC = (
    "カーソルページネーション用の位置指定文字列。前回のレスポンスに含まれる "
    "pages.next.starting_after の値をそのまま渡すと続きを取得できる。省略時は先頭ページ。"
    "レスポンスに pages.next が含まれない（null）場合はそれが最終ページ。"
)


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_contacts",
            description=(
                "ワークスペース内のコンタクト（user/leadロールの顧客・見込み客）一覧を、絞り込みなしで"
                "全件取得する。特定のメール・名前・属性で絞り込みたい場合は search_contacts を使うこと"
                "（このツールにはフィルタ機能がない）。ページネーションはカーソル方式（starting_after）。"
                "1ページあたりの件数は既定50件（Intercom側の一覧APIの既定値）。レスポンスの"
                "pages.next.starting_after を次回呼び出しの starting_after に渡すことで続きを取得する。"
                "既定の並び順はIntercom公式ドキュメントに明記されておらず未確認（作成日時順とは限らない）。"
                "POST /contacts/merge でマージ済みのコンタクトは一覧に含まれない（マージ先のみ残る）。"
                "読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "per_page": {
                        "type": "integer",
                        "description": "1ページあたりの件数（既定50、上限はIntercom側の一覧APIに準拠）。",
                    },
                    "starting_after": {
                        "type": "string",
                        "description": _STARTING_AFTER_DESC,
                    },
                },
            },
        ),
        types.Tool(
            name="search_contacts",
            description=(
                "コンタクトをメールアドレスまたは名前の部分一致（containsのOR条件）で検索する。"
                "「◯◯というメールドメインの人を探す」「名前の一部しか分からない」といった曖昧検索に使う。"
                "完全一致のIDが分かっている場合は get_contact の方が確実で速い。内部的には "
                "POST /contacts/search を、email/nameそれぞれに演算子 `~`（部分一致）でOR結合して呼び出す。"
                "Intercom検索APIはこの他にもrole/owner_id/created_at/tag_id等30以上のフィールドと"
                "=, !=, IN, NIN, >, <, ~, !~, ^, $ 等の演算子をサポートするが、本ツールはメール・名前の"
                "部分一致検索のみを公開している。ページネーションはカーソル方式（per_page既定50、"
                "starting_after）。マージ済みコンタクトは検索結果に含まれない。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "メールアドレスまたは名前の一部（部分一致で検索、大文字小文字の扱いはIntercom側の仕様に依存）",
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "1ページあたりの件数（既定50）",
                    },
                    "starting_after": {
                        "type": "string",
                        "description": _STARTING_AFTER_DESC,
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="get_contact",
            description=(
                "1件のコンタクトをIDで指定して詳細情報（メール・電話番号・役割・カスタム属性・"
                "タグ/ノート/所属会社の件数サマリ等）を取得する。IDが既知の場合はsearch_contactsより"
                "こちらを使う方が確実。指定したコンタクトが別のコンタクトにマージ済み（POST /contacts/merge "
                "の結果）の場合、元のIDでは404 Not Foundになる点に注意（マージ先の新しいIDを使う必要がある）。"
                "1件取得のみでページネーションはない。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string", "description": "コンタクトID（Intercom内部ID）"},
                },
                "required": ["contact_id"],
            },
        ),
        types.Tool(
            name="create_contact",
            description=(
                "新しいコンタクト（user または lead）を作成する。この操作はべき等ではない — 既に同じ"
                "メールアドレスのコンタクトが存在する場合、Intercom APIは409 Conflictエラーを返すことが"
                "あり、単純に再実行すると失敗する可能性がある（重複作成を避けたい場合は先にsearch_contacts"
                "で存在確認するか、external_idを指定してIntercom側の識別子解決に委ねること）。"
                "external_idは呼び出し側システムの一意なユーザーIDをIntercomに紐づけるための識別子で、"
                "Intercomはコンタクトの同一性判定をIntercom ID → external_id(user_id) → email の優先順で"
                "行うため、継続的に連携する場合は設定を推奨する。roleを省略するとuser（既存の有償顧客・"
                "ログイン済みユーザー想定）として作成され、見込み客はleadを指定する。"
                "既存コンタクトの更新（PUT /contacts/{id}）・削除以外の変更に対応するツールは本コネクタに"
                "存在しない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "メールアドレス"},
                    "name": {"type": "string", "description": "名前"},
                    "phone": {"type": "string", "description": "電話番号（例: +81901234567）"},
                    "role": {
                        "type": "string",
                        "description": "役割: user（既定） / lead",
                        "enum": ["user", "lead"],
                    },
                    "external_id": {
                        "type": "string",
                        "description": (
                            "呼び出し側システムでの一意なユーザーID。Intercomのコンタクト同一性判定で"
                            "email より優先されるため、重複作成を防ぎたい場合に指定する。"
                        ),
                    },
                },
                "required": ["email"],
            },
        ),
        types.Tool(
            name="delete_contact",
            description=(
                "コンタクトを1件削除する（DELETE /contacts/{id}）。削除は取り消せない破壊的操作であり、"
                "べき等ではない点に注意（既に削除済み/存在しないIDに対して再実行すると404エラーになる）。"
                "紐づく会話・ノート・タグ等がどう扱われるかはIntercom側の仕様に依存し、本コネクタでは"
                "確認していない。誤操作を避けるため、実行前にget_contactで対象を確認することを推奨する。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string", "description": "削除対象のコンタクトID"},
                },
                "required": ["contact_id"],
            },
        ),
        types.Tool(
            name="list_conversations",
            description=(
                "カンバセーション（サポート・チャットの会話スレッド）一覧を取得する。open=true（既定）の"
                "場合、状態が「オープン（未解決）」の会話のみを POST /conversations/search"
                "（フィールド open = true）経由で取得する。open=false を指定すると絞り込みを行わず、"
                "GET /conversations でopen/closed/snoozedすべての会話を取得する"
                "（GET /conversations 自体には状態でフィルタするクエリパラメータが存在しないため、"
                "この使い分けで実現している）。ページネーションはカーソル方式（per_page既定20、"
                "starting_after）。既定の並び順はIntercom公式ドキュメントに明記されておらず未確認。"
                "個々の会話本文・返信履歴まで見たい場合は本コネクタには get_conversation 相当のツールが"
                "存在しないため、conversation_idを控えて別途確認する必要がある。会話を削除するAPIは"
                "Intercomに存在しない（PUT /conversations/{id} による close/snooze/assign等の状態変更は"
                "可能だが、本コネクタには未実装）。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "per_page": {
                        "type": "integer",
                        "description": "1ページあたりの件数（既定20、上限150）",
                    },
                    "open": {
                        "type": "boolean",
                        "description": (
                            "true（既定）: オープン状態の会話のみに絞り込む。"
                            "false: 状態を問わず（open/closed/snoozed）全件取得する。"
                        ),
                    },
                    "starting_after": {
                        "type": "string",
                        "description": _STARTING_AFTER_DESC,
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_contacts":
                params = {"per_page": arguments.get("per_page", 50)}
                if arguments.get("starting_after"):
                    params["starting_after"] = arguments["starting_after"]
                r = client.get("/contacts", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "search_contacts":
                payload = {
                    "query": {
                        "operator": "OR",
                        "value": [
                            {"field": "email", "operator": "~", "value": arguments["query"]},
                            {"field": "name", "operator": "~", "value": arguments["query"]},
                        ],
                    },
                    "pagination": {"per_page": arguments.get("per_page", 50)},
                }
                if arguments.get("starting_after"):
                    payload["pagination"]["starting_after"] = arguments["starting_after"]
                r = client.post("/contacts/search", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_contact":
                contact_id = arguments["contact_id"]
                r = client.get(f"/contacts/{contact_id}")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "create_contact":
                payload = {
                    "email": arguments["email"],
                    "role": arguments.get("role", "user"),
                }
                if arguments.get("name"):
                    payload["name"] = arguments["name"]
                if arguments.get("phone"):
                    payload["phone"] = arguments["phone"]
                if arguments.get("external_id"):
                    payload["external_id"] = arguments["external_id"]
                r = client.post("/contacts", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "delete_contact":
                contact_id = arguments["contact_id"]
                r = client.delete(f"/contacts/{contact_id}")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_conversations":
                per_page = arguments.get("per_page", 20)
                if arguments.get("open", True):
                    payload = {
                        "query": {"field": "open", "operator": "=", "value": True},
                        "pagination": {"per_page": per_page},
                    }
                    if arguments.get("starting_after"):
                        payload["pagination"]["starting_after"] = arguments["starting_after"]
                    r = client.post("/conversations/search", json=payload)
                else:
                    params = {"per_page": per_page}
                    if arguments.get("starting_after"):
                        params["starting_after"] = arguments["starting_after"]
                    r = client.get("/conversations", params=params)
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
