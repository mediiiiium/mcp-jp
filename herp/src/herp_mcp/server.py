import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("herp-mcp")
BASE_URL = "https://public-api.herp.cloud/hire/v1"


def _client() -> httpx.Client:
    token = os.environ.get("HERP_API_KEY")
    if not token:
        raise ValueError("HERP_API_KEY が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
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
            name="list_candidacies",
            description=(
                "応募者（選考＝candidacy）の一覧を取得する。応募中の候補者の棚卸しや、特定求人への応募状況の"
                "確認、選考ステップ別の絞り込みに使う。ページネーションは page 番号方式で、1ページ100件固定"
                "（offset/limit は指定できない）。応答の hasNextPage が true の場合、page を+1して再度呼び出す"
                "と続きが取得できる。既定の並び順は appliedAt（応募日時）の降順（新しい順）。status で在籍中"
                "(active)/選考終了(terminated) を絞り込め、step で選考ステップ（entry/casualInterview/"
                "resumeScreening/firstInterview/secondInterview/thirdInterview/finalInterview/offered/"
                "offerAccepted）を絞り込める。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "取得するページ番号（1始まり、1ページ100件固定）", "default": 1},
                    "requisition_id": {"type": "string", "description": "この求人IDへの応募のみに絞り込む"},
                    "status": {
                        "type": "string",
                        "enum": ["active", "terminated"],
                        "description": "選考状況で絞り込む（active=選考中 / terminated=選考終了）。省略時は全件",
                    },
                    "step": {
                        "type": "string",
                        "enum": [
                            "entry",
                            "casualInterview",
                            "resumeScreening",
                            "firstInterview",
                            "secondInterview",
                            "thirdInterview",
                            "finalInterview",
                            "offered",
                            "offerAccepted",
                        ],
                        "description": "現在の選考ステップで絞り込む",
                    },
                    "termination_reason": {
                        "type": "string",
                        "enum": ["hired", "refusedByCandidate", "rejected", "notEligible"],
                        "description": "選考終了理由で絞り込む（status=terminated の候補者にのみ意味を持つ）",
                    },
                    "applied_at_from": {"type": "string", "description": "応募日時の範囲開始（YYYY-MM-DD、日本時間）"},
                    "applied_at_to": {"type": "string", "description": "応募日時の範囲終了（YYYY-MM-DD、日本時間）"},
                    "step_updated_at_from": {"type": "string", "description": "選考ステップ更新日時の範囲開始（YYYY-MM-DD、日本時間）"},
                    "step_updated_at_to": {"type": "string", "description": "選考ステップ更新日時の範囲終了（YYYY-MM-DD、日本時間）"},
                    "sort": {
                        "type": "string",
                        "enum": ["appliedAt", "stepUpdatedAt"],
                        "description": "並び替え基準の日時（既定 appliedAt=応募日時）",
                        "default": "appliedAt",
                    },
                    "direction": {
                        "type": "string",
                        "enum": ["asc", "desc"],
                        "description": "並び順（既定 desc=新しい順）",
                        "default": "desc",
                    },
                },
            },
        ),
        types.Tool(
            name="get_candidacy",
            description=(
                "応募者（選考）1件の詳細情報を取得する。氏名・連絡先・経歴・現在の選考ステップなど、"
                "list_candidacies の一覧には含まれない詳細を確認したい場合に使う。candidacy_id は "
                "list_candidacies のレスポンスから取得する。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "candidacy_id": {"type": "string", "description": "応募ID（list_candidacies で取得）"},
                },
                "required": ["candidacy_id"],
            },
        ),
        types.Tool(
            name="list_requisitions",
            description=(
                "求人（ポジション＝requisition）の一覧を取得する。募集中/クローズ済みの求人棚卸しや、"
                "採用ページ掲載状況の確認に使う。ページネーションは page 番号方式で、1ページ100件固定"
                "（offset/limit は指定できない）。応答の hasNextPage が true の場合、page を+1して再度呼び出す"
                "と続きが取得できる。既定の並び順は createdAt（作成日時）の降順（新しい順）。求人自体の"
                "作成・更新・削除APIは提供されていないため、本コネクタにも該当ツールはない（HERP Hire管理画面"
                "から操作する）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "取得するページ番号（1始まり、1ページ100件固定）", "default": 1},
                    "status": {
                        "type": "string",
                        "enum": ["active", "archived"],
                        "description": "募集状況で絞り込む（active=募集中 / archived=クローズ済み）。省略時は全件",
                    },
                    "career_page_status": {
                        "type": "string",
                        "enum": ["published", "unlisted", "private"],
                        "description": "採用ページへの掲載状況で絞り込む（published=公開 / unlisted=限定公開 / private=非公開）",
                    },
                    "sort": {
                        "type": "string",
                        "enum": ["createdAt", "updatedAt"],
                        "description": "並び替え基準の日時（既定 createdAt=作成日時）",
                        "default": "createdAt",
                    },
                    "direction": {
                        "type": "string",
                        "enum": ["asc", "desc"],
                        "description": "並び順（既定 desc=新しい順）",
                        "default": "desc",
                    },
                },
            },
        ),
        types.Tool(
            name="list_contacts",
            description=(
                "応募者1名分のコンタクト（面談・カジュアル面談・面接などの選考記録）を一覧取得する。"
                "各コンタクトには面談種別・実施日時・担当者・付随する評価などが含まれ、選考の経緯を"
                "追う目的で使う。candidacy_id は list_candidacies のレスポンスから取得する。API ドキュメントに"
                "ページネーションの記載がなく、該当応募者の全コンタクトを一度に返す。読み取り専用。"
                "コンタクトの新規作成API（POST /candidacies/{id}/contacts）は HERP Hire API に存在するが、"
                "本コネクタは読み取り中心の設計方針のため実装していない（HERP Hire 管理画面から操作する）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "candidacy_id": {"type": "string", "description": "応募ID（list_candidacies で取得）"},
                },
                "required": ["candidacy_id"],
            },
        ),
        types.Tool(
            name="list_candidacy_files",
            description=(
                "応募者1名に添付されたファイル（履歴書・職務経歴書・その他添付）のメタ情報一覧を取得する。"
                "ファイル種別(type)・MIMEタイプ・ファイル名・サイズ・アップロード日時・非公開フラグなどが"
                "返り、どんな応募書類が登録されているかを確認する目的で使う。candidacy_id は list_candidacies の"
                "レスポンスから取得する。ページネーションの記載はなく全ファイルのメタ情報を一度に返す。"
                "読み取り専用。なお個々のファイルの実体（バイナリ）は HERP Hire API では別エンドポイント"
                "（GET /candidacies/{id}/files/{fileId}）でバイナリ取得する仕様だが、テキストベースの本"
                "コネクタでは扱えないため実装していない。ファイル追加API（POST）も未実装。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "candidacy_id": {"type": "string", "description": "応募ID（list_candidacies で取得）"},
                },
                "required": ["candidacy_id"],
            },
        ),
        types.Tool(
            name="list_assignments",
            description=(
                "応募者1名にアサインされている担当者（selecterや面接官などの社内メンバー）の一覧を取得する。"
                "各要素は userId とその役割(role)を含み、この選考を誰が担当しているかを確認する目的で使う。"
                "userId の実名・メールアドレスなどは list_users で突き合わせて解決する。candidacy_id は "
                "list_candidacies のレスポンスから取得する。読み取り専用。担当者のアサイン追加(POST)・解除"
                "(DELETE)API は HERP Hire API に存在するが、本コネクタは読み取り中心の設計方針のため実装して"
                "いない（HERP Hire 管理画面から操作する）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "candidacy_id": {"type": "string", "description": "応募ID（list_candidacies で取得）"},
                },
                "required": ["candidacy_id"],
            },
        ),
        types.Tool(
            name="get_evaluation",
            description=(
                "評価依頼1件（evaluation）の詳細を取得する。面接官に依頼された評価の設問と回答内容を確認したい"
                "場合に使う。evaluation_request_id は、コンタクト（list_contacts）や応募者詳細（get_candidacy）の"
                "レスポンスに含まれる評価依頼IDを指定する（一覧取得の専用エンドポイントは HERP Hire API に"
                "存在しないため、評価IDはこれらのレスポンス経由で入手する必要がある）。読み取り専用。評価の"
                "提出・更新API（PUT /evaluations/{id}）は HERP Hire API に存在するが、本コネクタは読み取り中心の"
                "設計方針のため実装していない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "evaluation_request_id": {
                        "type": "string",
                        "description": "評価依頼ID（get_candidacy や list_contacts のレスポンスから取得）",
                    },
                },
                "required": ["evaluation_request_id"],
            },
        ),
        types.Tool(
            name="list_requisition_groups",
            description=(
                "求人グループ（複数の求人＝requisition をまとめる区分）の一覧を取得する。求人を職種・部門"
                "などのグループ単位で棚卸ししたい場合や、get_requisition_group に渡す求人グループIDを調べる"
                "目的で使う。API ドキュメントにページネーション・クエリパラメータの記載がなく、全グループを"
                "一度に返す。読み取り専用。求人グループの作成・更新・削除APIは HERP Hire API に提供されて"
                "いないため、本コネクタにも該当ツールはない（HERP Hire 管理画面から操作する）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="get_requisition_group",
            description=(
                "求人グループ1件の詳細情報を取得する。list_requisition_groups の一覧には含まれない、"
                "グループに紐づく求人の内訳などの詳細を確認したい場合に使う。requisition_group_id は "
                "list_requisition_groups のレスポンスから取得する。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "requisition_group_id": {
                        "type": "string",
                        "description": "求人グループID（list_requisition_groups で取得）",
                    },
                },
                "required": ["requisition_group_id"],
            },
        ),
        types.Tool(
            name="list_users",
            description=(
                "HERP Hire のユーザー（社内メンバーアカウント）の一覧を取得する。選考担当者やコメントの"
                "メンション先を特定する用途、list_assignments が返す userId を実名・メールアドレスに突き合わせる"
                "用途で使う。ページネーションは page 番号方式で、1ページ100件固定（offset/limit は指定できない）。"
                "応答の hasNextPage が true の場合、page を+1して再度呼び出すと続きが取得できる。status で"
                "在籍状況（active=有効 / deactivated=無効化済み）、role で権限（admin=管理者 / recruiter=リクルーター"
                " / assistant=アシスタント / guest=ゲスト）を絞り込める。読み取り専用。ユーザーの作成・更新・削除"
                "APIは HERP Hire API に提供されていないため、本コネクタにも該当ツールはない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "取得するページ番号（1始まり、1ページ100件固定）", "default": 1},
                    "status": {
                        "type": "string",
                        "enum": ["active", "deactivated"],
                        "description": "在籍状況で絞り込む（active=有効 / deactivated=無効化済み）。省略時は全件",
                    },
                    "role": {
                        "type": "string",
                        "enum": ["admin", "recruiter", "assistant", "guest"],
                        "description": "権限（ロール）で絞り込む（admin=管理者 / recruiter=リクルーター / assistant=アシスタント / guest=ゲスト）",
                    },
                    "direction": {
                        "type": "string",
                        "enum": ["asc", "desc"],
                        "description": "並び順（既定 desc）",
                        "default": "desc",
                    },
                },
            },
        ),
        types.Tool(
            name="list_timeline_comments",
            description=(
                "応募者1名分のタイムラインコメント（選考担当者間のやり取り・メモ）を一覧取得する。"
                "コメントを追加する前に既存のやり取りを確認する目的でよく使う。API ドキュメントにページネーション"
                "の記載がなく、該当応募者の全コメントを一度に返す。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "candidacy_id": {"type": "string", "description": "応募ID（list_candidacies で取得）"},
                },
                "required": ["candidacy_id"],
            },
        ),
        types.Tool(
            name="add_timeline_comment",
            description=(
                "応募者1名のタイムラインにコメントを新規追加する（書き込み系操作。呼び出すたびに新しいコメントが"
                "作成され、べき等ではない＝同じ内容で2回呼ぶとコメントが2件になる）。本文は最大20,000文字。"
                "text_type で書式（プレーンテキスト or Markdown）を指定でき、mention_to にユーザーIDを指定すると"
                "その担当者へ通知（メンション）される。コメントの編集・削除APIは提供されていないため、本コネクタ"
                "にも該当ツールはない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "candidacy_id": {"type": "string", "description": "応募ID（list_candidacies で取得）"},
                    "body": {"type": "string", "description": "コメント本文（最大20,000文字）"},
                    "text_type": {
                        "type": "string",
                        "enum": ["text/plain", "text/markdown"],
                        "description": "本文の書式（既定 text/plain）",
                        "default": "text/plain",
                    },
                    "mention_to": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "メンションして通知するユーザーIDのリスト（省略可）",
                    },
                },
                "required": ["candidacy_id", "body"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_candidacies":
                params: dict = {"page": arguments.get("page", 1)}
                if arguments.get("requisition_id"):
                    params["requisitionId"] = arguments["requisition_id"]
                if arguments.get("status"):
                    params["status"] = arguments["status"]
                if arguments.get("step"):
                    params["step"] = arguments["step"]
                if arguments.get("termination_reason"):
                    params["terminationReason"] = arguments["termination_reason"]
                if arguments.get("applied_at_from"):
                    params["appliedAtFrom"] = arguments["applied_at_from"]
                if arguments.get("applied_at_to"):
                    params["appliedAtTo"] = arguments["applied_at_to"]
                if arguments.get("step_updated_at_from"):
                    params["stepUpdatedAtFrom"] = arguments["step_updated_at_from"]
                if arguments.get("step_updated_at_to"):
                    params["stepUpdatedAtTo"] = arguments["step_updated_at_to"]
                if arguments.get("sort"):
                    params["sort"] = arguments["sort"]
                if arguments.get("direction"):
                    params["direction"] = arguments["direction"]
                r = client.get("/candidacies", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_candidacy":
                r = client.get(f"/candidacies/{arguments['candidacy_id']}")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_requisitions":
                params = {"page": arguments.get("page", 1)}
                if arguments.get("status"):
                    params["status"] = arguments["status"]
                if arguments.get("career_page_status"):
                    params["careerPageStatus"] = arguments["career_page_status"]
                if arguments.get("sort"):
                    params["sort"] = arguments["sort"]
                if arguments.get("direction"):
                    params["direction"] = arguments["direction"]
                r = client.get("/requisitions", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_contacts":
                r = client.get(f"/candidacies/{arguments['candidacy_id']}/contacts")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_candidacy_files":
                r = client.get(f"/candidacies/{arguments['candidacy_id']}/files")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_assignments":
                r = client.get(f"/candidacies/{arguments['candidacy_id']}/assignments")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_evaluation":
                r = client.get(f"/evaluations/{arguments['evaluation_request_id']}")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_requisition_groups":
                r = client.get("/requisition-groups")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_requisition_group":
                r = client.get(f"/requisition-groups/{arguments['requisition_group_id']}")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_users":
                params = {"page": arguments.get("page", 1)}
                if arguments.get("status"):
                    params["status"] = arguments["status"]
                if arguments.get("role"):
                    params["role"] = arguments["role"]
                if arguments.get("direction"):
                    params["direction"] = arguments["direction"]
                r = client.get("/users", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_timeline_comments":
                r = client.get(f"/candidacies/{arguments['candidacy_id']}/timeline-comments")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "add_timeline_comment":
                payload: dict = {"body": arguments["body"]}
                if arguments.get("text_type"):
                    payload["textType"] = arguments["text_type"]
                if arguments.get("mention_to"):
                    payload["mentionTo"] = arguments["mention_to"]
                r = client.post(f"/candidacies/{arguments['candidacy_id']}/timeline-comments", json=payload)
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
