import os
import base64
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("garoon-mcp")


def _client() -> httpx.Client:
    login_name = os.environ.get("GAROON_LOGIN_NAME")
    password = os.environ.get("GAROON_PASSWORD")
    subdomain = os.environ.get("GAROON_SUBDOMAIN")
    if not login_name:
        raise ValueError("GAROON_LOGIN_NAME が設定されていません")
    if not password:
        raise ValueError("GAROON_PASSWORD が設定されていません")
    if not subdomain:
        raise ValueError("GAROON_SUBDOMAIN が設定されていません")
    token = base64.b64encode(f"{login_name}:{password}".encode()).decode()
    return httpx.Client(
        base_url=f"https://{subdomain}.cybozu.com/g/api/v1",
        headers={"X-Cybozu-Authorization": token, "Content-Type": "application/json"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_events",
            description=(
                "Garoon スケジュールの予定一覧を、日時範囲・ユーザー/組織/施設で絞り込んで取得する。"
                "予定の棚卸しや「今週の予定を教えて」のような一覧確認に使う（1件だけを詳しく見る用途の"
                "ツールは本コネクタには実装していない）。target と target_type は指定する場合セットで"
                "必要（片方だけの指定は Garoon API 側でエラーになる）。両方省略すると、Garoon API の仕様上"
                "実行ユーザー自身（このMCPサーバーの認証に使っているアカウント）の予定のみが返る点に注意。"
                "並び順は Garoon API の既定である updatedAt の昇順（本ツールでは orderBy を指定していない）。"
                "ページネーションは offset/limit 方式：レスポンスの hasNext が true の場合、offset に"
                "現在の offset + limit を入れて再取得すると続きが得られる。Garoon API 上の上限は1回1000件・"
                "省略時100件だが、本ツールの limit 省略時デフォルトは20件。読み取り専用で副作用はない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "range_start": {
                        "type": "string",
                        "description": "取得開始日時（RFC 3339形式、例: 2024-01-01T00:00:00Z）。省略時の挙動は Garoon API のドキュメントに明記されていないため未検証。",
                    },
                    "range_end": {
                        "type": "string",
                        "description": "取得終了日時（RFC 3339形式、例: 2024-01-31T23:59:59Z）。省略時の挙動は Garoon API のドキュメントに明記されていないため未検証。",
                    },
                    "target": {
                        "type": "string",
                        "description": "絞り込み対象のユーザーID・組織ID・施設ID。指定する場合は target_type も必須（片方のみの指定不可）。両方省略時は実行ユーザー自身のIDが自動設定される。",
                    },
                    "target_type": {
                        "type": "string",
                        "description": "targetの種別（user / organization / facility）。target を指定する場合は必須。",
                        "enum": ["user", "organization", "facility"],
                    },
                    "limit": {
                        "type": "integer",
                        "description": "取得件数（Garoon API上の上限1000件）。本ツールでの省略時デフォルトは20件（Garoon API自体の素の既定値は100件だが、本ツールでは常に20を送信する）。",
                        "default": 20,
                    },
                    "offset": {
                        "type": "integer",
                        "description": "取得開始位置（デフォルト0）。前回レスポンスの hasNext が true の場合、続きを取るには offset を積み増して再取得する。",
                        "default": 0,
                    },
                },
            },
        ),
        types.Tool(
            name="create_event",
            description=(
                "Garoon スケジュールに予定を1件新規登録する。繰り返し予定・仮予定は Garoon API が"
                "対応していないため作成できない。Garoon API の仕様上、参加者（attendees）と施設"
                "（facilities）のどちらか一方は指定が必須だが、本ツールは attendee_ids のみに対応しており"
                "施設（会議室等）の指定はできない（未実装。予定に施設を紐づけたい場合は Garoon 画面側で"
                "追加する必要がある）。このAPIは冪等ではない：同じ内容で複数回呼び出すと、Garoon API側に"
                "重複防止の仕組みがないため予定が重複登録される。作成後の更新・削除ツールは本コネクタには"
                "実装していない（Garoon API自体には PATCH /schedule/events/{id} での更新、"
                "DELETE /schedule/events/{id} での削除が存在するが、本コネクタでは未実装）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "subject": {
                        "type": "string",
                        "description": "予定のタイトル",
                    },
                    "event_type": {
                        "type": "string",
                        "description": "予定の種別（REGULAR: 通常予定 / ALL_DAY: 期間予定）。繰り返し予定はGaroon APIで作成不可。",
                        "enum": ["REGULAR", "ALL_DAY"],
                        "default": "REGULAR",
                    },
                    "start_datetime": {
                        "type": "string",
                        "description": "開始日時（RFC 3339形式、例: 2024-01-15T10:00:00+09:00）",
                    },
                    "end_datetime": {
                        "type": "string",
                        "description": "終了日時（RFC 3339形式）。Garoon APIでは end は原則必須。",
                    },
                    "notes": {
                        "type": "string",
                        "description": "予定のメモ・詳細",
                    },
                    "attendee_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "参加者のユーザーIDリスト。Garoon APIの仕様上、参加者または施設のいずれかの指定が必須であり、本ツールは施設指定に対応していないため実質必須。",
                    },
                    "visibility_type": {
                        "type": "string",
                        "description": "公開設定（PUBLIC: 公開 / PRIVATE: 非公開）。Garoon APIドキュメントに既定値の明記はないが、本ツールでは省略時 PUBLIC を送信する。",
                        "enum": ["PUBLIC", "PRIVATE"],
                        "default": "PUBLIC",
                    },
                },
                "required": ["subject", "start_datetime", "end_datetime", "attendee_ids"],
            },
        ),
        types.Tool(
            name="list_users",
            description=(
                "Garoon に登録されているユーザーの一覧を、表示名・ログイン名・個人設定のローカライズ名を"
                "対象にした部分一致検索で取得する。予定作成の attendee_ids やワークフロー確認前にユーザーIDを"
                "特定する目的で使うことが多い。並び順は Garoon API の仕様で users[].id の昇順に固定されており"
                "変更できない。ページネーションは offset/limit 方式：レスポンスの hasNext が true の場合、"
                "offset を積み増して再取得する。Garoon API上の上限は1回1000件・省略時100件だが、本ツールの"
                "limit 省略時デフォルトは50件。読み取り専用で副作用はない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "ユーザー名（表示名・ログイン名・ローカライズ名のいずれか）で部分一致絞り込み",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "取得件数（Garoon API上の上限1000件）。本ツールでの省略時デフォルトは50件。",
                        "default": 50,
                    },
                    "offset": {
                        "type": "integer",
                        "description": "取得開始位置（デフォルト0）。前回レスポンスの hasNext が true の場合、続きを取るには offset を積み増して再取得する。",
                        "default": 0,
                    },
                },
            },
        ),
        types.Tool(
            name="list_workflow_requests",
            description=(
                "Garoon ワークフローの申請一覧を取得する（/workflow/admin/requests エンドポイントを使用）。"
                "このエンドポイントは Garoon API 側の仕様上、cybozu.com 共通管理者権限またはワークフロー"
                "アプリケーション管理者権限を持つアカウントでの実行が前提であり、一般ユーザーが自分自身の"
                "申請だけを取得する用途のツールではない（そのようなエンドポイントは本コネクタには未実装）。"
                "「承認待ちの申請を確認したい」「特定ステータスの申請を棚卸ししたい」といった管理者視点の"
                "確認に使う。ページネーションは offset/limit 方式：レスポンスの hasNext が true の場合、"
                "offset を積み増して再取得する。Garoon API上の上限は1回1000件・省略時100件だが、本ツールの"
                "limit 省略時デフォルトは20件。ソート可能な項目は createdAt のみ（Garoon API の素の既定は"
                "createdAt asc だが、本ツールでは省略時 createdAt desc＝新しい順を送信する）。読み取り専用で"
                "副作用はない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
                                "UNPROCESSING",
                                "IN_PROGRESS",
                                "REJECTED",
                                "WITHDRAWN",
                                "SENT_BACK",
                                "CANCELLED",
                                "APPROVED",
                                "COMPLETED",
                            ],
                        },
                        "description": (
                            "ステータスで絞り込み（複数指定可、OR条件）。指定可能な値："
                            "UNPROCESSING=申請後・処理前, IN_PROGRESS=承認後・最終承認前, "
                            "REJECTED=却下, WITHDRAWN=取戻後・申請前, SENT_BACK=申請者へ差し戻し後・申請前, "
                            "CANCELLED=差し戻し後にキャンセル, APPROVED=最終承認済み（確認経路あり）, "
                            "COMPLETED=最終承認済み（確認経路なし）。"
                        ),
                    },
                    "limit": {
                        "type": "integer",
                        "description": "取得件数（Garoon API上の上限1000件）。本ツールでの省略時デフォルトは20件。",
                        "default": 20,
                    },
                    "offset": {
                        "type": "integer",
                        "description": "取得開始位置（デフォルト0）。前回レスポンスの hasNext が true の場合、続きを取るには offset を積み増して再取得する。",
                        "default": 0,
                    },
                    "order_by": {
                        "type": "string",
                        "description": "ソート条件。Garoon APIでソート可能な項目は createdAt のみで、asc/desc を指定する（例: createdAt desc）。",
                        "default": "createdAt desc",
                    },
                },
            },
        ),
        types.Tool(
            name="get_presence",
            description=(
                "指定した1ユーザーの在席状況（レスポンスの status.code。attend=在席 / absence=不在 / "
                "管理者が追加したカスタムステータス文字列 / 空文字=未設定、のいずれか）を取得する。"
                "Garoon API はユーザーIDまたはログイン名のいずれかで個別に引く方式のみを提供しており"
                "（本ツールはユーザーID指定のエンドポイントのみ実装）、複数ユーザーをまとめて取得する"
                "一括APIは Garoon 側に存在しない。そのため複数人の在席を確認したい場合は本ツールを"
                "人数分繰り返し呼び出す必要がある。読み取り専用で副作用はない（在席状態の更新API"
                "（PATCH）はGaroon側に存在するが、本コネクタには未実装）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "在席情報を取得したい相手のGaroonユーザーID（list_users で調べられる）",
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
            if name == "list_events":
                params: dict = {
                    "limit": arguments.get("limit", 20),
                    "offset": arguments.get("offset", 0),
                }
                if arguments.get("range_start"):
                    params["rangeStart"] = arguments["range_start"]
                if arguments.get("range_end"):
                    params["rangeEnd"] = arguments["range_end"]
                if arguments.get("target"):
                    params["target"] = arguments["target"]
                if arguments.get("target_type"):
                    params["targetType"] = arguments["target_type"]
                r = client.get("/schedule/events", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "create_event":
                body: dict = {
                    "eventType": arguments.get("event_type", "REGULAR"),
                    "subject": arguments["subject"],
                    "start": {"dateTime": arguments["start_datetime"]},
                    "end": {"dateTime": arguments["end_datetime"]},
                    "visibilityType": arguments.get("visibility_type", "PUBLIC"),
                }
                if arguments.get("notes"):
                    body["notes"] = arguments["notes"]
                if arguments.get("attendee_ids"):
                    body["attendees"] = [{"type": "USER", "id": uid} for uid in arguments["attendee_ids"]]
                r = client.post("/schedule/events", content=json.dumps(body))
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_users":
                params = {
                    "limit": arguments.get("limit", 50),
                    "offset": arguments.get("offset", 0),
                }
                if arguments.get("name"):
                    params["name"] = arguments["name"]
                r = client.get("/base/users", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_workflow_requests":
                params = {
                    "limit": arguments.get("limit", 20),
                    "offset": arguments.get("offset", 0),
                    "orderBy": arguments.get("order_by", "createdAt desc"),
                }
                if arguments.get("status"):
                    params["status"] = arguments["status"]
                r = client.get("/workflow/admin/requests", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_presence":
                user_id = arguments["user_id"]
                r = client.get(f"/presence/users/{user_id}")
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
