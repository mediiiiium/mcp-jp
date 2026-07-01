import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("typeform-mcp")
BASE_URL = "https://api.typeform.com"


def _client() -> httpx.Client:
    access_token = os.environ.get("TYPEFORM_ACCESS_TOKEN")
    if not access_token:
        raise ValueError("TYPEFORM_ACCESS_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_forms",
            description=(
                "アカウント内のフォーム（Typeform）一覧を取得する。特定フォームのIDを調べたい・"
                "ワークスペース内の全フォームを棚卸ししたい、といった起点として使う。GET /forms を呼び出し、"
                "ページネーションは page/page_size 方式（本ツールの既定は page=1, page_size=10。"
                "Typeform API側の page_size 上限は200）。レスポンスの total_items（総件数）・page_count"
                "（総ページ数）を見て次ページの要否を判断すること。search を指定するとフォームタイトルの"
                "部分一致で絞り込める。workspace_id を指定すると特定ワークスペース内のフォームのみに絞り込める"
                "（list_workspaces で取得したワークスペースIDを渡す）。sort_by（created_at または "
                "last_updated_at）と order_by（asc/desc）で並び順を指定できる。両方省略した場合の既定の"
                "並び順は公式ドキュメントに明記されておらず未確認。フォームの作成・更新・削除に対応するツールは"
                "本コネクタに存在しない（Create/Update/Delete Form APIは存在するが未実装）。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（既定1、1始まり）"},
                    "page_size": {
                        "type": "integer",
                        "description": "1ページあたりの件数（既定10、Typeform API側の上限は200）",
                    },
                    "search": {
                        "type": "string",
                        "description": "フォームタイトルの部分一致検索文字列",
                    },
                    "workspace_id": {
                        "type": "string",
                        "description": "このワークスペースIDに属するフォームのみに絞り込む（list_workspaces で取得可能）",
                    },
                    "sort_by": {
                        "type": "string",
                        "description": "並び替えの基準フィールド。created_at または last_updated_at のみ指定可能（Typeform API仕様）。",
                        "enum": ["created_at", "last_updated_at"],
                    },
                    "order_by": {
                        "type": "string",
                        "description": "並び順。asc（昇順）または desc（降順）。sort_by と併用する。",
                        "enum": ["asc", "desc"],
                    },
                },
            },
        ),
        types.Tool(
            name="get_form",
            description=(
                "1件のフォームをIDで指定して詳細（タイトル・質問（fields）構成・ロジック分岐・テーマ・"
                "settings等）を取得する。質問ごとのfield ID（get_responses の fields/query 絞り込みや"
                "回答データのフィールド突合に必要）を確認する目的でよく使う。GET /forms/{form_id} を呼び出す。"
                "1件取得のみでページネーションはない。存在しないform_idを指定すると404になる。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "form_id": {
                        "type": "string",
                        "description": "フォームID（フォームURL 例: https://xxx.typeform.com/to/u6nXL7 の末尾 u6nXL7 の部分）",
                    },
                },
                "required": ["form_id"],
            },
        ),
        types.Tool(
            name="get_responses",
            description=(
                "指定フォームの回答一覧を取得する（GET /forms/{form_id}/responses）。既定では response_type "
                "を省略した場合 completed（送信完了済み）の回答のみが対象で、未完了（started/partial）の"
                "回答は含まれない点に注意。既定の並び順は submitted_at の降順（新しい回答が先頭）。"
                "ページネーションは2方式ある: (1) page_size のみで1000件までを一括取得する簡易方式（既定25件、"
                "上限1000件）。(2) 1000件を超える場合は since/until（日時範囲での絞り込み）または "
                "before/after（各回答が持つ token 値を使ったカーソル方式）で分割取得する必要がある。"
                "before/after は sort パラメータと併用できない（本ツールはsortを公開していない）。"
                "query を指定すると回答内容の文字列部分一致で絞り込める。レスポンスの total_items で全件数を"
                "確認できる。Typeform APIはこの他にfields（回答を表示するフィールドの絞り込み）、"
                "included_response_ids/excluded_response_ids（個別ID指定）、sort（fieldIDごとのソート）も"
                "サポートするが、本ツールはその一部（page_size, since, until, before, after, query, "
                "response_type）のみを公開している。回答を削除するAPI（DELETE /forms/{form_id}/responses、"
                "included_response_idsで対象指定）はTypeformに存在するが、本コネクタには未実装（削除は"
                "非同期処理で完了確認には別途本ツールでの再取得が必要）。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "form_id": {"type": "string", "description": "フォームID"},
                    "page_size": {
                        "type": "integer",
                        "description": "1ページあたりの件数（既定25、上限1000）",
                    },
                    "since": {
                        "type": "string",
                        "description": "この日時以降（含む）の回答に絞り込む。ISO8601形式（例: 2024-01-01T00:00:00）またはUNIXタイムスタンプ秒。",
                    },
                    "until": {
                        "type": "string",
                        "description": "この日時以前（含む）の回答に絞り込む。ISO8601形式またはUNIXタイムスタンプ秒。",
                    },
                    "before": {
                        "type": "string",
                        "description": (
                            "この token より前（古い）の回答に絞り込む（exclusive）。前回レスポンスの末尾の"
                            "回答の token 値を渡すと続きのページ（さらに古い回答）を取得できる。sortパラメータとは併用不可。"
                        ),
                    },
                    "after": {
                        "type": "string",
                        "description": (
                            "この token より後（新しい）の回答に絞り込む（exclusive）。前回レスポンスの先頭の"
                            "回答の token 値を渡すと続きのページ（さらに新しい回答）を取得できる。sortパラメータとは併用不可。"
                        ),
                    },
                    "query": {
                        "type": "string",
                        "description": "回答内容（全フィールドの回答テキスト）に対する部分一致検索文字列",
                    },
                    "response_type": {
                        "type": "string",
                        "description": (
                            "取得する回答の状態。completed（既定・送信完了済みのみ）/ partial（離脱・未完了）"
                            "/ started（開始のみ）。"
                        ),
                        "enum": ["completed", "partial", "started"],
                    },
                },
                "required": ["form_id"],
            },
        ),
        types.Tool(
            name="list_workspaces",
            description=(
                "アカウント内のワークスペース一覧を取得する（GET /workspaces）。list_forms の workspace_id "
                "絞り込みに使うワークスペースIDを調べる目的でよく使う。ページネーションは page/page_size 方式"
                "（本ツールの既定は page=1, page_size=10。Typeform API側の上限は200）。search を指定すると"
                "ワークスペース名の部分一致で絞り込める。レスポンスの各要素にはそのワークスペースに属するフォーム数"
                "や共有設定（shared）が含まれる。ワークスペースの作成・更新・削除に対応するツールは本コネクタに"
                "存在しない。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（既定1、1始まり）"},
                    "page_size": {
                        "type": "integer",
                        "description": "1ページあたりの件数（既定10、Typeform API側の上限は200）",
                    },
                    "search": {
                        "type": "string",
                        "description": "ワークスペース名の部分一致検索文字列",
                    },
                },
            },
        ),
        types.Tool(
            name="get_response_summary",
            description=(
                "指定フォームの回答インサイト（サマリー統計。質問ごとの回答分布・完了率など）を取得する"
                "（GET /insights/{form_id}/summary）。個々の回答内容ではなく集計結果が欲しい場合に使う"
                "（個々の回答が必要な場合は get_responses を使うこと）。このAPIはTypeformのビジネスプラン以上"
                "でのみ利用可能で、下位プランのアカウントではエラーになる。集計対象は全期間固定で、"
                "日付範囲を指定して絞り込むクエリパラメータは存在しない（Typeform公式コミュニティで明言されており、"
                "本ツールにも期間指定パラメータはない）。1件取得のみでページネーションはない。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "form_id": {"type": "string", "description": "フォームID"},
                },
                "required": ["form_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_forms":
                params = {
                    "page": arguments.get("page", 1),
                    "page_size": arguments.get("page_size", 10),
                }
                if arguments.get("search"):
                    params["search"] = arguments["search"]
                if arguments.get("workspace_id"):
                    params["workspace_id"] = arguments["workspace_id"]
                if arguments.get("sort_by"):
                    params["sort_by"] = arguments["sort_by"]
                if arguments.get("order_by"):
                    params["order_by"] = arguments["order_by"]
                r = client.get("/forms", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_form":
                form_id = arguments["form_id"]
                r = client.get(f"/forms/{form_id}")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_responses":
                form_id = arguments["form_id"]
                params = {"page_size": arguments.get("page_size", 25)}
                if arguments.get("since"):
                    params["since"] = arguments["since"]
                if arguments.get("until"):
                    params["until"] = arguments["until"]
                if arguments.get("before"):
                    params["before"] = arguments["before"]
                if arguments.get("after"):
                    params["after"] = arguments["after"]
                if arguments.get("query"):
                    params["query"] = arguments["query"]
                if arguments.get("response_type"):
                    params["response_type"] = arguments["response_type"]
                r = client.get(f"/forms/{form_id}/responses", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_workspaces":
                params = {
                    "page": arguments.get("page", 1),
                    "page_size": arguments.get("page_size", 10),
                }
                if arguments.get("search"):
                    params["search"] = arguments["search"]
                r = client.get("/workspaces", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_response_summary":
                form_id = arguments["form_id"]
                r = client.get(f"/insights/{form_id}/summary")
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
