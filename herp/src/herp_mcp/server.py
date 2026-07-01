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
