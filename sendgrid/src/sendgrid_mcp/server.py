import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("sendgrid-mcp")

BASE_URL = "https://api.sendgrid.com/v3"


def _client() -> httpx.Client:
    api_key = os.environ.get("SENDGRID_API_KEY")
    if not api_key:
        raise ValueError("SENDGRID_API_KEY が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="send_email",
            description=(
                "SendGrid Mail Send API（POST /v3/mail/send）経由でメールを1通送信する。実際に相手に配信される"
                "実世界の副作用を伴う操作であり、SendGrid 側にはリクエストの重複排除・冪等性キーの仕組みは存在"
                "しない（ドキュメント上も確認できず）。そのため同じ内容で2回呼び出すと2通届く。誤って連投しない"
                "よう、送信前に宛先・本文を必ず確認すること。成功時のレスポンスは HTTP 202 でボディは空（本文が"
                "空でも失敗ではない）。from_email は SendGrid で送信者確認（Single Sender Verification）または"
                "ドメイン認証済みのアドレスである必要があり、未確認のアドレスを使うと SendGrid 側で拒否される。"
                "このツールは宛先1名（to）のみに対応しており、CC/BCC・複数宛先・添付ファイル・動的テンプレート"
                "（template_id）・送信予約（send_at）には対応していない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "to_email": {
                        "type": "string",
                        "description": "送信先メールアドレス（1名のみ。複数宛先・CC/BCCには非対応）",
                    },
                    "to_name": {
                        "type": "string",
                        "description": "送信先の名前（任意）",
                    },
                    "from_email": {
                        "type": "string",
                        "description": "送信元メールアドレス。SendGrid で送信者確認済み（Single Sender Verification）またはドメイン認証済みのアドレスでなければ送信に失敗する",
                    },
                    "from_name": {
                        "type": "string",
                        "description": "送信元の名前（任意）",
                    },
                    "subject": {
                        "type": "string",
                        "description": "件名",
                    },
                    "text_content": {
                        "type": "string",
                        "description": "テキスト形式の本文",
                    },
                    "html_content": {
                        "type": "string",
                        "description": "HTML形式の本文（任意。指定しない場合はテキストのみのメールになる）",
                    },
                },
                "required": ["to_email", "from_email", "subject", "text_content"],
            },
        ),
        types.Tool(
            name="get_stats",
            description=(
                "アカウント全体のメール送信統計（配信数・開封数・クリック数・バウンス数・配信停止数等）を"
                "GET /v3/stats で取得する。start_date は必須（YYYY-MM-DD形式）、end_date を省略すると当日までが"
                "対象になる。aggregated_by で日別/週別/月別に集計単位を切り替えられる。過去のパフォーマンス確認や"
                "配信品質のモニタリングに使う。書き込みは行わない。レスポンスは日付ごとの統計オブジェクトの配列。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "開始日（YYYY-MM-DD形式、必須）",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "終了日（YYYY-MM-DD形式、省略時は当日まで）",
                    },
                    "aggregated_by": {
                        "type": "string",
                        "description": "集計単位（day: 日別, week: 週別, month: 月別）",
                        "enum": ["day", "week", "month"],
                        "default": "day",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返す結果数の上限（省略時はAPI既定値）",
                    },
                    "offset": {
                        "type": "integer",
                        "description": "結果を取得し始める位置（省略時は0）",
                    },
                },
                "required": ["start_date"],
            },
        ),
        types.Tool(
            name="list_bounces",
            description=(
                "バウンス（宛先不明・メールボックス満杯等で配信できなかった）メールアドレスの抑制リストを "
                "GET /v3/suppression/bounces で取得する。一覧に載っているアドレスへは、抑制解除しない限り"
                "SendGrid が自動的に配信をブロックし続ける。start_time/end_time（Unixタイムスタンプ）でバウンス"
                "登録日時を絞り込み、email で特定アドレス（前方一致等のワイルドカードは `%25` を使用）を絞り込める。"
                "limit は最大500件（省略時のデフォルトはAPI側に依存）、offset と組み合わせてページングする。"
                "バウンス登録を削除する API（DELETE /v3/suppression/bounces、個別または全件削除）はSendGrid側に"
                "存在するが、本コネクタにはそれに対応するツールは実装されていない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "start_time": {
                        "type": "integer",
                        "description": "開始日時（Unixタイムスタンプ）",
                    },
                    "end_time": {
                        "type": "integer",
                        "description": "終了日時（Unixタイムスタンプ）",
                    },
                    "email": {
                        "type": "string",
                        "description": "特定のメールアドレスで絞り込む（省略可）",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "取得件数（デフォルト25、最大500）",
                        "default": 25,
                    },
                    "offset": {
                        "type": "integer",
                        "description": "取得開始位置（デフォルト0）",
                        "default": 0,
                    },
                },
            },
        ),
        types.Tool(
            name="list_unsubscribes",
            description=(
                "グローバル配信停止（Global Unsubscribes/Suppressions）リストを GET /v3/suppression/unsubscribes "
                "で取得する。ここに載っているアドレスには、配信停止グループ（ASM）の設定に関わらず、SendGrid が"
                "マーケティング系メールの配信を一律ブロックする（トランザクションメールは対象外の場合がある点に"
                "注意）。start_time/end_time（Unixタイムスタンプ）で登録日時を絞り込み、email で特定アドレス"
                "（`%25` ワイルドカード対応）を絞り込める。limit は最大500件、offset と組み合わせてページングする。"
                "アドレスを配信停止リストへ追加する API（POST /v3/suppression/unsubscribes）や個別に解除する API"
                "（DELETE /v3/suppression/unsubscribes/{email}）はSendGrid側に存在するが、本コネクタにはそれに"
                "対応するツールは実装されていない（一覧取得のみ）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "start_time": {
                        "type": "integer",
                        "description": "開始日時（Unixタイムスタンプ）",
                    },
                    "end_time": {
                        "type": "integer",
                        "description": "終了日時（Unixタイムスタンプ）",
                    },
                    "email": {
                        "type": "string",
                        "description": "特定のメールアドレスで絞り込む（省略可）",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "取得件数（デフォルト25、最大500）",
                        "default": 25,
                    },
                    "offset": {
                        "type": "integer",
                        "description": "取得開始位置（デフォルト0）",
                        "default": 0,
                    },
                },
            },
        ),
        types.Tool(
            name="list_templates",
            description=(
                "メールテンプレート一覧を GET /v3/templates で取得する（カーソル方式のページネーション）。"
                "generations で legacy（旧式テンプレート）・dynamic（Handlebars構文を使う動的テンプレート）・"
                "legacy,dynamic（両方）を切り替えられる。SendGrid API自体の既定値は legacy だが、本ツールは"
                "実務でよく使われる dynamic をデフォルトにしている（明示的に指定しない限りAPIの既定値とは異なる"
                "点に注意）。page_size は1〜200件（デフォルト10）。次ページを取得するには、前回レスポンスの "
                "_metadata.next（URL）に含まれる page_token をこのツールの page_token に渡す。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "generations": {
                        "type": "string",
                        "description": "テンプレート世代（legacy: 旧式のみ / dynamic: 動的テンプレートのみ / legacy,dynamic: 両方）",
                        "enum": ["legacy", "dynamic", "legacy,dynamic"],
                        "default": "dynamic",
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "1ページあたりの取得件数（1〜200、デフォルト10）",
                        "default": 10,
                    },
                    "page_token": {
                        "type": "string",
                        "description": "前回レスポンスの _metadata.next に含まれるページトークンを渡すとその続きから取得する",
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "send_email":
                to_addr: dict = {"email": arguments["to_email"]}
                if arguments.get("to_name"):
                    to_addr["name"] = arguments["to_name"]
                from_addr: dict = {"email": arguments["from_email"]}
                if arguments.get("from_name"):
                    from_addr["name"] = arguments["from_name"]
                content = [{"type": "text/plain", "value": arguments["text_content"]}]
                if arguments.get("html_content"):
                    content.append({"type": "text/html", "value": arguments["html_content"]})
                body = {
                    "personalizations": [{"to": [to_addr]}],
                    "from": from_addr,
                    "subject": arguments["subject"],
                    "content": content,
                }
                r = client.post("/mail/send", content=json.dumps(body))
                r.raise_for_status()
                return format_response({"status": "sent", "status_code": r.status_code})

            elif name == "get_stats":
                params: dict = {
                    "start_date": arguments["start_date"],
                    "aggregated_by": arguments.get("aggregated_by", "day"),
                }
                if arguments.get("end_date"):
                    params["end_date"] = arguments["end_date"]
                if arguments.get("limit") is not None:
                    params["limit"] = arguments["limit"]
                if arguments.get("offset") is not None:
                    params["offset"] = arguments["offset"]
                r = client.get("/stats", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_bounces":
                params = {
                    "limit": arguments.get("limit", 25),
                    "offset": arguments.get("offset", 0),
                }
                if arguments.get("start_time"):
                    params["start_time"] = arguments["start_time"]
                if arguments.get("end_time"):
                    params["end_time"] = arguments["end_time"]
                if arguments.get("email"):
                    params["email"] = arguments["email"]
                r = client.get("/suppression/bounces", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_unsubscribes":
                params = {
                    "limit": arguments.get("limit", 25),
                    "offset": arguments.get("offset", 0),
                }
                if arguments.get("start_time"):
                    params["start_time"] = arguments["start_time"]
                if arguments.get("end_time"):
                    params["end_time"] = arguments["end_time"]
                if arguments.get("email"):
                    params["email"] = arguments["email"]
                r = client.get("/suppression/unsubscribes", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_templates":
                params = {
                    "generations": arguments.get("generations", "dynamic"),
                    "page_size": arguments.get("page_size", 10),
                }
                if arguments.get("page_token"):
                    params["page_token"] = arguments["page_token"]
                r = client.get("/templates", params=params)
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
