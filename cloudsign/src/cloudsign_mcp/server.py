import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("cloudsign-mcp")
BASE_URL = "https://api.cloudsign.jp"


def _get_token() -> str:
    client_id = os.environ.get("CLOUDSIGN_CLIENT_ID")
    if not client_id:
        raise ValueError("CLOUDSIGN_CLIENT_ID が設定されていません")
    r = httpx.post(
        f"{BASE_URL}/token",
        data={"client_id": client_id},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def _client() -> httpx.Client:
    token = _get_token()
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
            name="list_documents",
            description=(
                "書類（契約書）の一覧を取得する。案件の棚卸しや「未完了の契約を確認したい」といった全体把握に使う。"
                "title で部分一致絞り込み、status でステータス絞り込みが可能（get_document で個別の詳細を見る前に"
                "対象の document_id を探す用途で使うことが多い）。ページネーションは offset/limit 方式で、1回の"
                "リクエストで最大100件（既定20件）。続きを取得するには前回の offset に limit を足した値を次の "
                "offset に指定する。既定の並び順は CloudSign API 側の仕様として明記されておらず、本ツールでは"
                "ソート順を指定できない（新しい順・古い順を保証するものではない点に注意）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "書類タイトルの部分一致で絞り込む"},
                    "status": {
                        "type": "integer",
                        "description": (
                            "書類ステータス（整数）で絞り込む。CloudSign 側で確認できている値の例: "
                            "1=先方確認中（送信済み・署名待ち）, 2=締結完了, 3=取消または却下, 13=インポート書類。"
                            "0（下書き）は本コネクタの create_document で作成した直後の書類が該当すると推測されるが、"
                            "公式ヘルプに明記された一覧ではないため未確認。正確な値の一覧は CloudSign Web API 仕様書"
                            "（SwaggerHub: CloudSign/cloudsign-web_api）で確認することを推奨する。"
                        ),
                    },
                    "offset": {"type": "integer", "description": "取得開始位置（0始まり）。次ページは前回の offset+limit を指定する", "default": 0},
                    "limit": {"type": "integer", "description": "取得件数（最大100、既定20）", "default": 20},
                },
            },
        ),
        types.Tool(
            name="get_document",
            description=(
                "書類1件の詳細情報（タイトル・ステータス・参加者・送信/最終処理日時など）を取得する。"
                "list_documents で対象の document_id を特定した後、内容を確認する目的で使う。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "対象の書類ID（list_documents や create_document のレスポンスに含まれる）"},
                },
                "required": ["document_id"],
            },
        ),
        types.Tool(
            name="create_document",
            description=(
                "新しい書類（契約書）を下書き状態で作成する。template_id を指定するとそのテンプレートの内容"
                "（ファイル・入力項目のレイアウト等）を引き継いだ状態で作成され、省略すると空の書類になる。"
                "呼び出すたびに新しい書類が作成される（べき等ではない。同じ内容で誤って2回呼ぶと重複した書類が"
                "2件できる）。作成直後は下書き状態で参加者未設定のため、続けて set_participants で署名者を設定し、"
                "send_document で送信する必要がある。書類の削除エンドポイントは CloudSign API に存在しないため、"
                "誤って作成した書類は管理画面から削除・無効化する必要がある。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "書類タイトル"},
                    "template_id": {"type": "string", "description": "作成元にするテンプレートID（省略時は空の書類として作成）"},
                    "message": {"type": "string", "description": "署名依頼メッセージ（送信時に相手に表示される案内文）"},
                },
                "required": ["title"],
            },
        ),
        types.Tool(
            name="set_participants",
            description=(
                "下書き状態の書類に署名者（参加者）を設定する。send_document で送信する前に必ず呼び出す必要がある"
                "（参加者未設定のまま送信することはできない）。participants 配列の順序がそのまま署名依頼の送信順"
                "になる（1番目の相手が同意/署名した後に2番目へ通知が送られる、といった逐次送信）。この順序は書類を"
                "まだ送信していない間は再度呼び出すことで変更できるが、send_document 実行後は変更できなくなる。"
                "内部的には配列のインデックス（1始まり）ごとに参加者情報を上書きする実装のため、以前より少ない人数を"
                "指定しても、それより後ろの枠に残っていた古い参加者情報が消えずに残る場合がある点に注意（参加者を"
                "減らしたい場合は管理画面での確認を推奨）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "対象の書類ID（下書き状態であること）"},
                    "participants": {
                        "type": "array",
                        "description": "署名者リスト。配列の順序＝署名依頼を送る順序（1番目から順に逐次送信される）",
                        "items": {
                            "type": "object",
                            "properties": {
                                "email": {"type": "string", "description": "署名者のメールアドレス（署名依頼の送付先）"},
                                "name": {"type": "string", "description": "署名者の表示名（相手に通知される氏名）"},
                            },
                            "required": ["email", "name"],
                        },
                    },
                },
                "required": ["document_id", "participants"],
            },
        ),
        types.Tool(
            name="send_document",
            description=(
                "下書き状態の書類を署名依頼として送信する（ステータスを「先方確認中」に変更する不可逆な操作）。"
                "事前に set_participants で参加者を設定しておく必要がある。べき等ではない: 既に送信済み・完了済みの"
                "書類に対して呼び出すとエラーになる可能性が高い。送信を取り消す（キャンセルする）APIは"
                "CloudSign 側に提供されていないため、誤送信時は管理画面から手動で取消・却下操作を行う必要がある。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "送信する書類ID（下書き状態かつ参加者設定済みであること）"},
                },
                "required": ["document_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_documents":
                params = {
                    "offset": arguments.get("offset", 0),
                    "limit": arguments.get("limit", 20),
                }
                if arguments.get("title"):
                    params["title"] = arguments["title"]
                if arguments.get("status") is not None:
                    params["status"] = arguments["status"]
                r = client.get("/documents", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_document":
                r = client.get(f"/documents/{arguments['document_id']}")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "create_document":
                payload: dict = {"title": arguments["title"]}
                if arguments.get("template_id"):
                    payload["template_id"] = arguments["template_id"]
                if arguments.get("message"):
                    payload["message"] = arguments["message"]
                r = client.post("/documents", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "set_participants":
                document_id = arguments["document_id"]
                results = []
                for i, p in enumerate(arguments["participants"]):
                    payload = {"email": p["email"], "name": p["name"]}
                    r = client.put(f"/documents/{document_id}/participants/{i + 1}", json=payload)
                    r.raise_for_status()
                    results.append(r.json())
                return format_response(results)

            elif name == "send_document":
                r = client.put(
                    f"/documents/{arguments['document_id']}",
                    json={"status": 1},
                )
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
