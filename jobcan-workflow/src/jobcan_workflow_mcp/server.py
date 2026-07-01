import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("jobcan-workflow-mcp")

BASE_URL = "https://ssl.wf.jobcan.jp/wf_api"


def _client() -> httpx.Client:
    token = os.environ.get("JOBCAN_API_TOKEN")
    if not token:
        raise ValueError("JOBCAN_API_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Token {token}", "Content-Type": "application/json"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_requests",
            description=(
                "ジョブカン経費精算/ワークフローの申請書一覧を、ステータス・申請者・グループ・"
                "プロジェクト・日付範囲などで絞り込んで取得する（GET /v2/requests/）。「今月の申請を"
                "見せて」「進行中の申請一覧」のような棚卸し・一覧確認に使う。1件の詳細（明細行や"
                "コメント履歴を含む全項目）が必要な場合は get_request を使うこと。並び順は既定で"
                "sort_by=applied_date_desc（申請日の新しい順）。ページネーションはページ番号方式で"
                "1ページ100件固定：レスポンスの next が null でなければ page を1つ増やして再取得する"
                "（next には次ページの完全なURLが入るが、本ツールは page 番号のみ受け付ける）。"
                "applied_after/applied_before/completed_after/completed_before の日付は "
                "yyyy/mm/dd または yyyy/mm/dd hh:mm:ss 形式で指定する（ハイフン区切りは受け付けられない"
                "可能性が高い）。include_canceled を true にしない限り、取り消し済みの申請は"
                "結果から除外される。読み取り専用で副作用はない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "申請書IDで絞り込み（完全一致）。複数指定する場合はカンマ区切りで指定（例: \"123,456\"）。",
                    },
                    "status": {
                        "type": "string",
                        "description": "申請状況で絞り込み（in_progress: 進行中, completed: 完了, rejected: 却下, returned: 差し戻し, canceled: 取り消し, canceled_after_completion: 完了後取消）。",
                        "enum": ["in_progress", "completed", "rejected", "returned", "canceled", "canceled_after_completion"],
                    },
                    "form_id": {
                        "type": "string",
                        "description": "フォームID（申請書の様式）で絞り込み（完全一致）。フォームIDが不明な場合は絞り込まずに一覧を取得し、結果の form 情報から確認する。",
                    },
                    "title": {
                        "type": "string",
                        "description": "申請書タイトルで絞り込み（部分一致）。",
                    },
                    "applicant_code": {
                        "type": "string",
                        "description": "申請者のスタッフコード（ユーザーコード）で絞り込み（完全一致）。list_users で取得できるユーザーコードを指定する。",
                    },
                    "group_code": {
                        "type": "string",
                        "description": "申請者が所属するグループ（部署）のコードで絞り込み（完全一致）。",
                    },
                    "project_code": {
                        "type": "string",
                        "description": "プロジェクトコードで絞り込み（完全一致）。list_projects で取得できるコードを指定する。",
                    },
                    "applied_after": {
                        "type": "string",
                        "description": "申請日時の開始（この日時以降に申請されたものを抽出）。yyyy/mm/dd または yyyy/mm/dd hh:mm:ss 形式（例: \"2024/01/01\"）。",
                    },
                    "applied_before": {
                        "type": "string",
                        "description": "申請日時の終了（この日時以前に申請されたものを抽出）。yyyy/mm/dd または yyyy/mm/dd hh:mm:ss 形式。",
                    },
                    "completed_after": {
                        "type": "string",
                        "description": "最終承認日時の開始（この日時以降に最終承認されたものを抽出）。yyyy/mm/dd または yyyy/mm/dd hh:mm:ss 形式。未承認・進行中の申請には最終承認日がないため対象外になる。",
                    },
                    "completed_before": {
                        "type": "string",
                        "description": "最終承認日時の終了（この日時以前に最終承認されたものを抽出）。yyyy/mm/dd または yyyy/mm/dd hh:mm:ss 形式。",
                    },
                    "include_canceled": {
                        "type": "boolean",
                        "description": "取り消し済みの申請も結果に含めるか（既定は false = 除外）。取り消し申請だけを見たい場合は status=canceled と併用する。",
                        "default": False,
                    },
                    "sort_by": {
                        "type": "string",
                        "description": "並び順（applied_date_asc: 申請日昇順, applied_date_desc: 申請日降順[既定], group: グループ順, form: フォーム順, user: 申請者順）。",
                        "enum": ["applied_date_asc", "applied_date_desc", "group", "form", "user"],
                    },
                    "page": {
                        "type": "integer",
                        "description": "ページ番号（デフォルト: 1）。1ページ100件固定。レスポンスの next が null でなければ次ページが存在する。",
                        "default": 1,
                    },
                },
            },
        ),
        types.Tool(
            name="get_request",
            description=(
                "申請書1件の詳細情報を取得する（GET /v2/requests/{request_id}/）。list_requests の"
                "一覧には含まれない明細行・添付ファイル情報・承認ルートの進捗などを確認したいときに使う。"
                "request_id は list_requests のレスポンスに含まれる id フィールドの値を指定する。"
                "読み取り専用で副作用はない。承認・却下・差し戻しを行うAPIエンドポイントは本APIには"
                "存在しない（承認操作はジョブカンのWeb画面上でのみ可能）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "request_id": {
                        "type": "integer",
                        "description": "申請書ID（list_requests のレスポンスの id フィールドで取得できる）。",
                    },
                },
                "required": ["request_id"],
            },
        ),
        types.Tool(
            name="list_users",
            description=(
                "ジョブカンに登録されているユーザーの一覧を取得する（GET /v3/users/）。list_requests の"
                "applicant_code に指定するスタッフコードを調べる際などに使う。v3 を使用しているのは、"
                "v1/v2 に比べて所属（グループ・役職）が構造化されたオブジェクトで返り、v3 のみメモ欄"
                "（memo）も含まれるため。ページネーションはページ番号方式：レスポンスの next が null で"
                "なければ page を1つ増やして再取得する（1ページあたりの件数・並び順はAPIドキュメントに"
                "明記されておらず未検証）。page 以外の絞り込みパラメータ（氏名・グループ等）はAPIドキュメント"
                "上に存在しない。なお本APIにはユーザー作成（POST）・更新（PUT）・無効化（DELETE）の"
                "エンドポイントが存在するが、本コネクタでは読み取り専用ツールのみを実装しており未対応。"
                "読み取り専用で副作用はない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer",
                        "description": "ページ番号（デフォルト: 1）。1ページあたりの件数はAPIドキュメントに明記なし。",
                        "default": 1,
                    },
                },
            },
        ),
        types.Tool(
            name="list_projects",
            description=(
                "ジョブカンに登録されているプロジェクト一覧を取得する（GET /v1/projects/）。"
                "list_requests の project_code に指定するコードを調べる際などに使う。ページネーションは"
                "ページ番号方式：レスポンスの next が null でなければ page を1つ増やして再取得する"
                "（1ページあたりの件数・並び順はAPIドキュメントに明記されておらず未検証）。page 以外の"
                "絞り込みパラメータ（プロジェクト名等）はAPIドキュメント上に存在しない。なお本APIには"
                "プロジェクト作成（POST）・更新（PUT）・削除（DELETE）のエンドポイントが存在するが、"
                "本コネクタでは読み取り専用ツールのみを実装しており未対応。読み取り専用で副作用はない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer",
                        "description": "ページ番号（デフォルト: 1）。1ページあたりの件数はAPIドキュメントに明記なし。",
                        "default": 1,
                    },
                },
            },
        ),
        types.Tool(
            name="list_companies",
            description=(
                "ジョブカンに登録されている取引先（会社）一覧を取得する（GET /v1/company/）。経費精算の"
                "取引先マスタを確認したいときに使う。ページネーションはページ番号方式：レスポンスの next が"
                "null でなければ page を1つ増やして再取得する（1ページあたりの件数・並び順はAPIドキュメント"
                "に明記されておらず未検証）。page 以外の絞り込みパラメータ（取引先名等）はAPIドキュメント上"
                "に存在しない。なお本APIには取引先作成（POST）・更新（PUT）・削除（DELETE）のエンドポイント"
                "が存在するが、本コネクタでは読み取り専用ツールのみを実装しており未対応。読み取り専用で"
                "副作用はない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer",
                        "description": "ページ番号（デフォルト: 1）。1ページあたりの件数はAPIドキュメントに明記なし。",
                        "default": 1,
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_requests":
                params: dict = {"page": arguments.get("page", 1)}
                if arguments.get("id"):
                    params["id"] = arguments["id"]
                if arguments.get("status"):
                    params["status"] = arguments["status"]
                if arguments.get("form_id"):
                    params["form_id"] = arguments["form_id"]
                if arguments.get("title"):
                    params["title"] = arguments["title"]
                if arguments.get("applicant_code"):
                    params["applicant_code"] = arguments["applicant_code"]
                if arguments.get("group_code"):
                    params["group_code"] = arguments["group_code"]
                if arguments.get("project_code"):
                    params["project_code"] = arguments["project_code"]
                if arguments.get("applied_after"):
                    params["applied_after"] = arguments["applied_after"]
                if arguments.get("applied_before"):
                    params["applied_before"] = arguments["applied_before"]
                if arguments.get("completed_after"):
                    params["completed_after"] = arguments["completed_after"]
                if arguments.get("completed_before"):
                    params["completed_before"] = arguments["completed_before"]
                if "include_canceled" in arguments:
                    params["include_canceled"] = arguments["include_canceled"]
                if arguments.get("sort_by"):
                    params["sort_by"] = arguments["sort_by"]
                r = client.get("/v2/requests/", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_request":
                rid = arguments["request_id"]
                r = client.get(f"/v2/requests/{rid}/")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_users":
                params = {"page": arguments.get("page", 1)}
                r = client.get("/v3/users/", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_projects":
                params = {"page": arguments.get("page", 1)}
                r = client.get("/v1/projects/", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_companies":
                params = {"page": arguments.get("page", 1)}
                r = client.get("/v1/company/", params=params)
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
