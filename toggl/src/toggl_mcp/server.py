import os
import base64
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("toggl-mcp")
BASE_URL = "https://api.track.toggl.com/api/v9"


def _client() -> httpx.Client:
    api_token = os.environ.get("TOGGL_API_TOKEN")
    if not api_token:
        raise ValueError("TOGGL_API_TOKEN が設定されていません")
    credentials = base64.b64encode(f"{api_token}:api_token".encode()).decode()
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Basic {credentials}", "Content-Type": "application/json"},
        timeout=30,
    )


_WORKSPACE_ID_DESC = "対象ワークスペースID（list_workspaces で確認）"
_TIME_ENTRY_ID_DESC = "対象の時間計測エントリーID（list_time_entries で確認）"


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_profile",
            description=(
                "現在のユーザー（このAPIトークンの所有者）のプロファイルを取得する。デフォルトワークスペースID・"
                "メールアドレス・タイムゾーンなど基本情報の確認に使う。with_related_data を true にすると、"
                "紐づくクライアント・プロジェクト・タスク・タグ・ワークスペース・直近の時間計測エントリー等を"
                "まとめて1回のリクエストで取得できる（個別に list_* を呼ぶより効率的だが応答が大きくなる）。"
                "読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "with_related_data": {
                        "type": "boolean",
                        "description": "true にするとクライアント・プロジェクト・タスク・タグ・ワークスペース・時間計測エントリー等の関連データもまとめて取得する（既定false）",
                    },
                },
            },
        ),
        types.Tool(
            name="list_workspaces",
            description=(
                "このユーザーが所属するワークスペース（Toggl Trackの契約・請求単位となる組織）の一覧を取得する。"
                "プロジェクト・時間計測エントリー等ほぼ全てのツールで workspace_id の指定が必要になるため、"
                "他のツールを呼ぶ前に最初に確認することが多い。ページネーションなし（全件を一度に返す）。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="list_projects",
            description=(
                "指定ワークスペース内のプロジェクト一覧を取得する。時間計測エントリー作成時に指定するproject_idを"
                "確認したい場合や、稼働中プロジェクトの棚卸しに使う。ページネーションはページ番号方式"
                "（page / per_page、per_page既定151・上限200）。既定ではactive=trueを送信しアクティブなプロジェクト"
                "のみを返す（Toggl API自体のactive省略時デフォルトは公式ドキュメントに明記されていないため、本ツール"
                "側で明示的にtrueを指定している）。全件（アーカイブ済み含む）を取得したい場合は active に 'both' を"
                "指定する。client_ids・billable・since（UNIXタイムスタンプ、これ以降に作成/更新/削除されたものに"
                "絞り込み、差分取得に使える）でも絞り込み可能。読み取り専用。プロジェクトの作成・更新・削除・"
                "クライアント一覧取得のAPIはToggl Track側に存在するが、誤操作で稼働中プロジェクトや請求データに"
                "影響が出るのを避けるため本コネクタでは提供していない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "integer", "description": _WORKSPACE_ID_DESC},
                    "active": {
                        "type": ["boolean", "string"],
                        "description": "true=アクティブのみ（既定）、false=アーカイブ済みのみ、'both'=両方",
                    },
                    "client_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "このクライアントIDのいずれかに紐づくプロジェクトのみに絞り込む",
                    },
                    "billable": {"type": "boolean", "description": "true=請求対象のみ、false=非請求対象のみに絞り込む（プレミアム機能）"},
                    "since": {"type": "integer", "description": "このUNIXタイムスタンプ以降に作成・更新・削除されたプロジェクトのみに絞り込む（差分取得用）"},
                    "page": {"type": "integer", "description": "取得するページ番号（1始まり、既定1）"},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（既定151、上限200）"},
                },
                "required": ["workspace_id"],
            },
        ),
        types.Tool(
            name="list_clients",
            description=(
                "指定ワークスペース内のクライアント（請求先企業）一覧を取得する。プロジェクトのclient_idが"
                "どの企業を指すか確認したい場合に使う。既定ではstatusを指定しないためアクティブなクライアントのみ"
                "が返る（アーカイブ済みを含めるには status='archived' または 'both' を指定）。name で部分一致・"
                "大文字小文字を区別しない絞り込みができる。ページネーションなし（全件を一度に返す）。読み取り専用。"
                "クライアントの作成・更新・削除・アーカイブ用のAPIはToggl Track側に存在するが、請求データへの"
                "影響を避けるため本コネクタでは参照のみ提供している。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "integer", "description": _WORKSPACE_ID_DESC},
                    "status": {
                        "type": "string",
                        "enum": ["active", "archived", "both"],
                        "description": "ステータスで絞り込む（active=有効のみ・既定 / archived=アーカイブ済みのみ / both=両方）",
                    },
                    "name": {"type": "string", "description": "クライアント名の部分一致（大文字小文字区別なし）で絞り込む"},
                },
                "required": ["workspace_id"],
            },
        ),
        types.Tool(
            name="list_time_entries",
            description=(
                "認証ユーザー自身の時間計測エントリー一覧を取得する。既定では開始日時(start)の新しい順で返る。"
                "start_date・end_date を省略した場合、Toggl側の仕様（公式ドキュメントには明記がないためサポート"
                "情報に基づく）で直近9日分・最大1000件までしか返らない可能性があるため、それより古い/多いデータが"
                "必要な場合は start_date/end_date またはページング代わりとなる before（この日時より前のエントリー"
                "に絞り込む）で範囲を絞って複数回呼び出すこと。専用のカーソル/ページ番号方式のページネーションは"
                "存在しない。since（UNIXタイムスタンプ）を使うとその時刻以降に作成・更新・削除されたエントリーを"
                "取得でき、削除されたエントリーも含まれるため差分同期に使える。meta=true で関連するプロジェクト名・"
                "クライアント名等のメタ情報を含める。include_sharing=true で共有先ユーザー情報を含める。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "開始時刻の範囲開始（YYYY-MM-DD または RFC3339形式）。end_dateとあわせて指定する"},
                    "end_date": {"type": "string", "description": "開始時刻の範囲終了（YYYY-MM-DD または RFC3339形式）。start_dateとあわせて指定する"},
                    "before": {"type": "string", "description": "この日時（YYYY-MM-DD または RFC3339形式）より前に開始したエントリーのみに絞り込む"},
                    "since": {"type": "integer", "description": "このUNIXタイムスタンプ以降に作成・更新・削除されたエントリーのみに絞り込む（削除済みも含む、差分取得用）"},
                    "meta": {"type": "boolean", "description": "true にすると関連するプロジェクト名・クライアント名等のメタ情報を含める（既定false）"},
                    "include_sharing": {"type": "boolean", "description": "true にすると共有先ユーザー情報を含める（既定false）"},
                },
            },
        ),
        types.Tool(
            name="create_time_entry",
            description=(
                "新しい時間計測エントリーを1件作成する。呼び出すたびに新規エントリーが作成されるため冪等ではない"
                "（同じ内容で2回呼ぶと重複して2件作成される）。duration に -1 など負の値を渡すと「実行中のタイマー」"
                "として作成される（stopは省略）。実行中のタイマーを止めるには stop_time_entry を使う。作成後の"
                "内容変更は update_time_entry、削除は delete_time_entry を使う。project_id・task_id は事前に"
                "list_projects 等で有効なIDを確認しておくこと。tags（タグ名。存在しない名前は自動作成される）と"
                "tag_ids（既存タグID）はどちらか一方で足りる場合が多い。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "integer", "description": _WORKSPACE_ID_DESC},
                    "description": {"type": "string", "description": "作業内容の説明"},
                    "project_id": {"type": "integer", "description": "紐づけるプロジェクトID"},
                    "task_id": {"type": "integer", "description": "紐づけるタスクID（プロジェクトに割り当て済みである必要がある）"},
                    "start": {"type": "string", "description": "開始時刻（ISO8601形式、例: 2024-04-01T10:00:00+09:00）"},
                    "stop": {"type": "string", "description": "終了時刻（ISO8601形式）。指定する場合、start + duration と整合している必要がある（省略可、実行中タイマーの場合は省略する）"},
                    "duration": {"type": "integer", "description": "作業時間（秒）。実行中タイマーとして作成する場合は -1 などの負の値を指定する"},
                    "billable": {"type": "boolean", "description": "請求対象として記録するか（既定false、プレミアム機能）"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "付与するタグ名の一覧（存在しない名前は自動作成される）"},
                    "tag_ids": {"type": "array", "items": {"type": "integer"}, "description": "付与する既存タグIDの一覧"},
                },
                "required": ["workspace_id", "start", "duration"],
            },
        ),
        types.Tool(
            name="update_time_entry",
            description=(
                "既存の時間計測エントリー1件を更新する（PUT）。同一内容で複数回呼び出しても結果は変わらないため"
                "実質的に冪等。Toggl公式ドキュメントには、リクエストに含めなかった項目が更新後どう扱われるか"
                "（変更されないのか、既定値にリセットされるのか）が明記されていないため、意図せぬ値のクリアを"
                "避けたい場合は変更しない項目も含めて明示的に指定することを推奨する。タイマーを停止したいだけの"
                "場合は本ツールより stop_time_entry の方が確実。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "integer", "description": _WORKSPACE_ID_DESC},
                    "time_entry_id": {"type": "integer", "description": _TIME_ENTRY_ID_DESC},
                    "description": {"type": "string", "description": "変更後の作業内容の説明"},
                    "project_id": {"type": "integer", "description": "変更後のプロジェクトID"},
                    "task_id": {"type": "integer", "description": "変更後のタスクID"},
                    "start": {"type": "string", "description": "変更後の開始時刻（ISO8601形式）"},
                    "stop": {"type": "string", "description": "変更後の終了時刻（ISO8601形式）。start + duration と整合している必要がある"},
                    "duration": {"type": "integer", "description": "変更後の作業時間（秒）。実行中にする場合は -1 などの負の値"},
                    "billable": {"type": "boolean", "description": "請求対象として記録するか"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "設定するタグ名の一覧（tag_actionと組み合わせて使う）"},
                    "tag_ids": {"type": "array", "items": {"type": "integer"}, "description": "設定する既存タグIDの一覧（tag_actionと組み合わせて使う）"},
                    "tag_action": {
                        "type": "string",
                        "enum": ["add", "delete"],
                        "description": "tags/tag_idsで指定したタグを追加(add)するか削除(delete)するか",
                    },
                },
                "required": ["workspace_id", "time_entry_id"],
            },
        ),
        types.Tool(
            name="stop_time_entry",
            description=(
                "実行中（duration が負の値）の時間計測エントリーを停止し、現在時刻を終了時刻として確定する。"
                "既に停止済みのエントリーに対して呼び出すとAPIエラーになるため冪等ではない。停止対象のIDが"
                "分からない場合は list_time_entries で duration が負の値のエントリーを探す。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "integer", "description": _WORKSPACE_ID_DESC},
                    "time_entry_id": {"type": "integer", "description": _TIME_ENTRY_ID_DESC},
                },
                "required": ["workspace_id", "time_entry_id"],
            },
        ),
        types.Tool(
            name="delete_time_entry",
            description=(
                "時間計測エントリー1件を削除する。削除は取り消せない。一度削除したIDに対して再度削除を呼ぶと"
                "エラーになるため冪等ではない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "integer", "description": _WORKSPACE_ID_DESC},
                    "time_entry_id": {"type": "integer", "description": _TIME_ENTRY_ID_DESC},
                },
                "required": ["workspace_id", "time_entry_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "get_profile":
                params = {}
                if arguments.get("with_related_data") is not None:
                    params["with_related_data"] = arguments["with_related_data"]
                r = client.get("/me", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_workspaces":
                r = client.get("/me/workspaces")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_projects":
                workspace_id = arguments["workspace_id"]
                params = {}
                active = arguments.get("active", True)
                params["active"] = active if active == "both" else str(bool(active)).lower()
                if arguments.get("client_ids"):
                    params["client_ids"] = arguments["client_ids"]
                if arguments.get("billable") is not None:
                    params["billable"] = arguments["billable"]
                if arguments.get("since"):
                    params["since"] = arguments["since"]
                if arguments.get("page"):
                    params["page"] = arguments["page"]
                if arguments.get("per_page"):
                    params["per_page"] = arguments["per_page"]
                r = client.get(f"/workspaces/{workspace_id}/projects", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_clients":
                workspace_id = arguments["workspace_id"]
                params = {}
                if arguments.get("status"):
                    params["status"] = arguments["status"]
                if arguments.get("name"):
                    params["name"] = arguments["name"]
                r = client.get(f"/workspaces/{workspace_id}/clients", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_time_entries":
                params = {}
                if arguments.get("start_date"):
                    params["start_date"] = arguments["start_date"]
                if arguments.get("end_date"):
                    params["end_date"] = arguments["end_date"]
                if arguments.get("before"):
                    params["before"] = arguments["before"]
                if arguments.get("since"):
                    params["since"] = arguments["since"]
                if arguments.get("meta") is not None:
                    params["meta"] = arguments["meta"]
                if arguments.get("include_sharing") is not None:
                    params["include_sharing"] = arguments["include_sharing"]
                r = client.get("/me/time_entries", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "create_time_entry":
                workspace_id = arguments["workspace_id"]
                payload = {
                    "start": arguments["start"],
                    "duration": arguments["duration"],
                    "created_with": "toggl-mcp",
                    "workspace_id": workspace_id,
                }
                if arguments.get("description"):
                    payload["description"] = arguments["description"]
                if arguments.get("project_id"):
                    payload["project_id"] = arguments["project_id"]
                if arguments.get("task_id"):
                    payload["task_id"] = arguments["task_id"]
                if arguments.get("stop"):
                    payload["stop"] = arguments["stop"]
                if arguments.get("billable") is not None:
                    payload["billable"] = arguments["billable"]
                if arguments.get("tags"):
                    payload["tags"] = arguments["tags"]
                if arguments.get("tag_ids"):
                    payload["tag_ids"] = arguments["tag_ids"]
                r = client.post(f"/workspaces/{workspace_id}/time_entries", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "update_time_entry":
                workspace_id = arguments["workspace_id"]
                time_entry_id = arguments["time_entry_id"]
                payload = {}
                if arguments.get("description") is not None:
                    payload["description"] = arguments["description"]
                if arguments.get("project_id") is not None:
                    payload["project_id"] = arguments["project_id"]
                if arguments.get("task_id") is not None:
                    payload["task_id"] = arguments["task_id"]
                if arguments.get("start"):
                    payload["start"] = arguments["start"]
                if arguments.get("stop"):
                    payload["stop"] = arguments["stop"]
                if arguments.get("duration") is not None:
                    payload["duration"] = arguments["duration"]
                if arguments.get("billable") is not None:
                    payload["billable"] = arguments["billable"]
                if arguments.get("tags"):
                    payload["tags"] = arguments["tags"]
                if arguments.get("tag_ids"):
                    payload["tag_ids"] = arguments["tag_ids"]
                if arguments.get("tag_action"):
                    payload["tag_action"] = arguments["tag_action"]
                r = client.put(f"/workspaces/{workspace_id}/time_entries/{time_entry_id}", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "stop_time_entry":
                workspace_id = arguments["workspace_id"]
                time_entry_id = arguments["time_entry_id"]
                r = client.patch(f"/workspaces/{workspace_id}/time_entries/{time_entry_id}/stop")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "delete_time_entry":
                workspace_id = arguments["workspace_id"]
                time_entry_id = arguments["time_entry_id"]
                r = client.delete(f"/workspaces/{workspace_id}/time_entries/{time_entry_id}")
                r.raise_for_status()
                return format_response({"deleted": True, "time_entry_id": time_entry_id})

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
