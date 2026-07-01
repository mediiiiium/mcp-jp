import os
from datetime import datetime, timedelta, timezone

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("relation-mcp")

JST = timezone(timedelta(hours=9))


def _client() -> httpx.Client:
    subdomain = os.environ.get("RELATION_SUBDOMAIN")
    access_token = os.environ.get("RELATION_ACCESS_TOKEN")
    if not subdomain:
        raise ValueError("RELATION_SUBDOMAIN が設定されていません")
    if not access_token:
        raise ValueError("RELATION_ACCESS_TOKEN が設定されていません")
    return httpx.Client(
        base_url=f"https://{subdomain}.relationapp.jp/api/v2",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_message_boxes",
            description=(
                "受信箱（メールボックス）の一覧を取得する。各受信箱の message_box_id・名前・色（color）・"
                "紐づくアドレス帳ID（customer_group_id）・更新日時を返す。search_tickets や get_ticket、"
                "create_reply_memo を呼ぶ際に必要な message_box_id を事前に確認する目的で使うことが多い。"
                "ページネーションなし（全受信箱を一度に返す）。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="search_tickets",
            description=(
                "指定した受信箱内のチケット（問い合わせ）を条件検索する。RE:lation APIはキーワード（件名・本文の"
                "全文）検索に対応していないため、絞り込みはステータス・ラベル・色・担当者・添付有無・期間のみで行う"
                "（keywordパラメータは存在しない）。既定では新しい順に最大50件（1ページあたり最大50件・既定50件）を"
                "返す。ページングは page 番号方式（1始まり）で、続きを取るには page を+1して再度呼び出す。"
                "since/until はメッセージの送信日時（ISO 8601形式）で絞り込む。1件の詳細（本文・添付・コメントなど）"
                "を見たい場合は get_ticket を使う。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "message_box_id": {"type": "integer", "description": "受信箱ID（list_message_boxesで確認）"},
                    "status_cds": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["open", "ongoing", "closed", "unwanted", "trash", "spam"],
                        },
                        "description": (
                            "ステータスで絞り込む（複数指定可、OR条件）。open=未対応, ongoing=保留, "
                            "closed=対応完了, unwanted=対応不要, trash=ゴミ箱, spam=迷惑メール"
                        ),
                    },
                    "label_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "ラベルIDで絞り込む（複数指定可、OR条件）。[-1] を指定するとラベルなしのチケットのみに絞り込める",
                    },
                    "color_cds": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["red", "orange", "yellow", "blue", "pink"]},
                        "description": "チケットに設定された色ラベルで絞り込む（複数指定可、OR条件）",
                    },
                    "assignee": {
                        "type": "string",
                        "description": "担当者のメンション名で絞り込む（IDではなく文字列）。空文字 \"\" を指定すると未割当のチケットのみに絞り込める",
                    },
                    "has_attachments": {"type": "boolean", "description": "true の場合、添付ファイルがあるチケットのみに絞り込む"},
                    "since": {"type": "string", "description": "メッセージ送信日時の範囲開始（ISO 8601形式、例: 2026-06-01T00:00:00+09:00）"},
                    "until": {"type": "string", "description": "メッセージ送信日時の範囲終了（ISO 8601形式）"},
                    "page": {"type": "integer", "description": "ページ番号（1始まり、既定1）。続きは page を+1して呼び出す", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（最大50、既定50）", "default": 50},
                },
                "required": ["message_box_id"],
            },
        ),
        types.Tool(
            name="get_ticket",
            description=(
                "チケット1件の詳細情報を取得する。ステータス・担当者・色・ラベル・保留理由に加え、そのチケットに"
                "紐づく全メッセージ（messages配列: 本文・送受信者・チャネル種別・添付ファイル・コメント）をまとめて"
                "返す。メッセージ件数が多いチケットでもこのAPI自体にページネーションは無く、まとめて1回で返る"
                "（メッセージ数が非常に多い場合はレスポンスが大きくなる点に注意）。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "message_box_id": {"type": "integer", "description": "受信箱ID"},
                    "ticket_id": {"type": "integer", "description": "チケットID（search_ticketsで取得したticket_id）"},
                },
                "required": ["message_box_id", "ticket_id"],
            },
        ),
        types.Tool(
            name="create_reply_memo",
            description=(
                "既存チケットに対応履歴（応対メモ、社内向けの対応記録）を1件追加する（POST、呼び出すたびに新規の"
                "メモが作成され、重複防止の仕組みはRE:lation側に存在しないためべき等ではない）。これは顧客への"
                "返信メール送信ではなく、あくまで内部記録用のメモである点に注意（メール返信APIは本コネクタでは"
                "未実装）。重要な副作用: status_cd を省略した場合、RE:lation側の既定値により対象チケットが"
                "「対応完了」状態に変わる。対応中のまま記録だけ残したい場合は status_cd に \"open\"（未対応）や "
                "\"ongoing\"（保留）を明示的に指定すること。operated_at は過去日時のみ指定可能（未来日時は不可）で、"
                "省略した場合は呼び出し時点の現在時刻が使われる。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "message_box_id": {"type": "integer", "description": "受信箱ID"},
                    "ticket_id": {"type": "integer", "description": "メモを追加する対象チケットID"},
                    "subject": {"type": "string", "description": "メモの件名（必須）"},
                    "body": {"type": "string", "description": "メモの本文（必須）"},
                    "duration": {"type": "integer", "description": "対応にかかった時間（分、0〜1440、既定0）", "default": 0},
                    "operated_at": {
                        "type": "string",
                        "description": "対応日時（ISO 8601形式、過去日時のみ有効）。省略時は呼び出し時点の現在時刻（JST）を使用する",
                    },
                    "status_cd": {
                        "type": "string",
                        "enum": ["open", "ongoing", "closed", "unwanted", "trash", "spam"],
                        "description": (
                            "メモ追加後のチケットステータス。省略時はRE:lation側の既定値 \"closed\"（対応完了）になる"
                            "点に注意。open=未対応, ongoing=保留, closed=対応完了, unwanted=対応不要, trash=ゴミ箱, spam=迷惑メール"
                        ),
                    },
                    "operator": {"type": "string", "description": "対応した担当者のメンション名（省略可）"},
                    "icon_cd": {
                        "type": "string",
                        "enum": ["received_phone", "called_phone", "meeting", "sales", "postal", "note"],
                        "description": (
                            "対応種別アイコン。received_phone=受電, called_phone=架電, meeting=会議, sales=営業, "
                            "postal=郵便物, note=その他（既定 received_phone）"
                        ),
                    },
                },
                "required": ["message_box_id", "ticket_id", "subject", "body"],
            },
        ),
        types.Tool(
            name="list_users",
            description=(
                "RE:lationのユーザー（オペレーター）一覧を取得する。メンション名・氏名・部署名・社員番号・"
                "メールアドレス・テナント管理者フラグなどを返す。search_tickets の assignee や create_reply_memo の "
                "operator に指定するメンション名を確認する目的で使うことが多い。ページングは page 番号方式"
                "（1始まり）で、1ページあたり最大100件（既定30件）。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり、既定1）", "default": 1},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（最大100、既定30）", "default": 30},
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_message_boxes":
                r = client.get("/message_boxes")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "search_tickets":
                mb_id = arguments["message_box_id"]
                payload: dict = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 50),
                }
                if arguments.get("status_cds"):
                    payload["status_cds"] = arguments["status_cds"]
                if arguments.get("label_ids"):
                    payload["label_ids"] = arguments["label_ids"]
                if arguments.get("color_cds"):
                    payload["color_cds"] = arguments["color_cds"]
                if "assignee" in arguments:
                    payload["assignee"] = arguments["assignee"]
                if "has_attachments" in arguments:
                    payload["has_attachments"] = arguments["has_attachments"]
                if arguments.get("since"):
                    payload["since"] = arguments["since"]
                if arguments.get("until"):
                    payload["until"] = arguments["until"]
                r = client.post(f"/{mb_id}/tickets/search", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_ticket":
                mb_id = arguments["message_box_id"]
                ticket_id = arguments["ticket_id"]
                r = client.get(f"/{mb_id}/tickets/{ticket_id}")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "create_reply_memo":
                mb_id = arguments["message_box_id"]
                operated_at = arguments.get("operated_at") or datetime.now(JST).isoformat(timespec="seconds")
                payload = {
                    "ticket_id": arguments["ticket_id"],
                    "subject": arguments["subject"],
                    "body": arguments["body"],
                    "operated_at": operated_at,
                    "duration": arguments.get("duration", 0),
                }
                if arguments.get("status_cd"):
                    payload["status_cd"] = arguments["status_cd"]
                if arguments.get("operator"):
                    payload["operator"] = arguments["operator"]
                if arguments.get("icon_cd"):
                    payload["icon_cd"] = arguments["icon_cd"]
                r = client.post(f"/{mb_id}/records", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_users":
                params = {
                    "page": arguments.get("page", 1),
                    "per_page": arguments.get("per_page", 30),
                }
                r = client.get("/users", params=params)
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
