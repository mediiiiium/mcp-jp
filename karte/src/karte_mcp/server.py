import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("karte-mcp")

BASE_URL = "https://api.karte.io"


def _client() -> httpx.Client:
    api_key = os.environ.get("KARTE_API_KEY")
    if not api_key:
        raise ValueError("KARTE_API_KEY が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="track_event",
            description=(
                "KARTE にユーザー行動イベントを送信し、解析対象として記録する（POST /v2/track/event/write）。"
                "ユーザーの識別には user_id（ログイン済み会員）または visitor_id（未ログイン訪問者、vis- 始まり）の"
                "どちらか一方のみを指定する（両方の指定はできない）。書き込みは非同期に処理されるため、送信直後に "
                "get_user_events で照会しても即座には反映されない場合がある。このAPI経由のイベントはポップアップ・"
                "メール・アプリプッシュ通知などの配信トリガー（対象イベント）としては利用できない点に注意（配信トリガーに"
                "したい場合や送信と同時にサーバーサイドアクションを実行したい場合は track_event_exec_action を使う）。"
                "event_name には page, req, enter_group, leave_group, view, group, message_send, date, "
                "message_open, message_click, message_clicked, message_close は予約語のため使用できない。"
                "同じ内容を繰り返し送信すると重複したイベントとして記録される（べき等ではない）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ユーザーID（ログイン済みユーザー。identify イベントで送信された user_id）。visitor_id とは併用不可"},
                    "visitor_id": {"type": "string", "description": "訪問者ID（未ログインユーザー、vis- で始まる形式）。user_id とは併用不可"},
                    "event_name": {
                        "type": "string",
                        "description": (
                            "イベント名（例: purchase, view_item, add_to_cart）。"
                            "page/req/enter_group/leave_group/view/group/message_send/date/message_open/"
                            "message_click/message_clicked/message_close は予約語のため指定不可"
                        ),
                    },
                    "event_values": {
                        "type": "object",
                        "description": (
                            "イベントに紐づける任意のKey-Valueデータ（例: {\"item_id\": \"abc\", \"price\": 1000}）。"
                            "identify イベントを送るユーザーデータ管理用途では values に user_id を含める必要がある"
                        ),
                    },
                },
                "required": ["event_name"],
            },
        ),
        types.Tool(
            name="get_user_events",
            description=(
                "指定ユーザー（user_id または visitor_id）のイベント履歴を、イベント名ごとにまとめて取得する"
                "（POST /v2beta/track/event/get）。track_event で送信した行動ログを後から確認したい場合に使う。"
                "event_names は1〜10件まで指定可能（既定は [\"view\"]）。各イベント名配下の配列は発生時刻の昇順"
                "（古い→新しい）で返る。options.limit で1イベント名あたりの取得件数を絞れる（Beta期間中は最大10件、"
                "省略時は10件）。options.from / options.to で取得期間を絞り込める（Unixタイムミリ秒、13桁）。"
                "該当ユーザーが存在しない場合はエラーにはならず空の events が返る。書き込みは行わない。"
                "強整合性（強い一貫性）は保証されない（送信直後の反映タイミングにはラグがありうる）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ユーザーID または visitor_id（vis- 始まり）"},
                    "event_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "取得するイベント名のリスト（1〜10件、例: [\"view\", \"purchase\"]）",
                        "default": ["view"],
                    },
                    "limit": {
                        "type": "integer",
                        "description": "イベント名1件あたりの取得件数（1〜10、省略時10件。Beta期間中は最大10件までの制限あり）",
                    },
                    "from_unixtime_ms": {
                        "type": "integer",
                        "description": "この時刻（Unixタイムミリ秒、13桁）以降のイベントのみ取得する",
                    },
                    "to_unixtime_ms": {
                        "type": "integer",
                        "description": "この時刻（Unixタイムミリ秒、13桁）より前のイベントのみ取得する",
                    },
                },
                "required": ["user_id"],
            },
        ),
        types.Tool(
            name="track_event_exec_action",
            description=(
                "KARTE にイベントを送信すると同時に、あらかじめ設定済みのサーバーサイドアクション"
                "（Amazon EventBridge / LINE / SendGrid / ネイティブアプリプッシュ通知 / Webhook / Webhook V2 / "
                "KARTE Craft のいずれか）を実行する（POST /v2beta/track/event/writeAndExecAction）。"
                "user_id または visitor_id のどちらか一方が必須（併用不可）で、track_event と同じ予約語の"
                "event_name は使用できない。イベント書き込み・アクション実行はいずれも非同期。単にイベントを記録する"
                "だけで配信トリガーとしての実行を伴わない場合は track_event の方がシンプル。同じ内容を繰り返し送信すると"
                "アクションも重複して実行されうる（べき等ではない）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ユーザーID（ログイン済みユーザー）。visitor_id とは併用不可"},
                    "visitor_id": {"type": "string", "description": "訪問者ID（未ログインユーザー、vis- で始まる形式）。user_id とは併用不可"},
                    "event_name": {
                        "type": "string",
                        "description": (
                            "イベント名。page/req/enter_group/leave_group/view/group/message_send/date/"
                            "message_open/message_click/message_clicked/message_close は予約語のため指定不可"
                        ),
                    },
                    "event_values": {
                        "type": "object",
                        "description": "イベントに紐づける任意のKey-Valueデータ",
                    },
                },
                "required": ["event_name"],
            },
        ),
        types.Tool(
            name="get_campaign",
            description=(
                "接客サービス（キャンペーン。ポップアップ・メール等の配信設定一式）の詳細をIDで1件取得する"
                "（POST /v2beta/action/campaign/findById）。取得できるのはタイトル・公開状態(enabled)・説明・"
                "紐づく接客アクション一覧（配信率や停止状態を含む）・対象セグメント・配信曜日時間帯・開始/終了日など。"
                "IDが分からない場合の一覧検索手段は本コネクタにはない（KARTE管理画面で確認するか、既知のIDのみ指定できる）。"
                "KARTE APIには接客サービスの新規作成(create)・更新(update)・公開/非公開切替(toggleEnabled)の"
                "エンドポイントも存在するが、本コネクタでは読み取り専用ツールのみを実装しており、これらの書き込み系は"
                "未実装（管理画面から操作する）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "campaign_id": {"type": "string", "description": "接客サービスのID"},
                },
                "required": ["campaign_id"],
            },
        ),
        types.Tool(
            name="get_campaign_stats",
            description=(
                "全接客サービス（キャンペーン）の設定と効果測定データをCSV形式で一括取得する"
                "（POST /v2beta/action/campaign/getSettingsAndStats）。個別の接客サービスの詳細を見るなら"
                "get_campaign を使う方が適切。集計期間は、効果測定期間が「セッション単位」の接客サービスに対しては "
                "start_date / end_date（両方必須、YYYY-MM-DD）、効果測定期間が「1日/7日/30日単位」の接客サービスに"
                "対しては range（latest_thirty_days / latest_a_week / latest_two_weeks / YYYY-MM 形式のいずれか）"
                "で指定する。start_date・end_date・range は3つとも必須パラメータ（対象外の集計方式のサービスに対しては"
                "無視される）。is_test を true にするとテストデータを含めて返す。renew を true にすると集計を再計算する"
                "が、通常は指定不要（レスポンスが遅くなる）。書き込みは行わない。レスポンスはJSONではなくCSVテキストで"
                "返る（内部で自動整形せずそのまま返す）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "集計開始日（YYYY-MM-DD 形式、セッション単位の接客サービス向け）",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "集計終了日（YYYY-MM-DD 形式、セッション単位の接客サービス向け）",
                    },
                    "range": {
                        "type": "string",
                        "description": "1日/7日/30日単位の接客サービス向け集計期間: latest_thirty_days / latest_a_week / latest_two_weeks / YYYY-MM",
                        "default": "latest_thirty_days",
                    },
                    "is_test": {
                        "type": "boolean",
                        "description": "true の場合、テストデータも含めて返す（既定は false）",
                    },
                    "renew": {
                        "type": "boolean",
                        "description": "true の場合、集計データを再作成してから返す（時間がかかるため通常は不要）",
                    },
                },
                "required": ["start_date", "end_date"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "track_event":
                keys: dict = {}
                if arguments.get("user_id"):
                    keys["user_id"] = arguments["user_id"]
                elif arguments.get("visitor_id"):
                    keys["visitor_id"] = arguments["visitor_id"]
                else:
                    raise ValueError("user_id または visitor_id のいずれかが必要です")
                event: dict = {"event_name": arguments["event_name"]}
                if arguments.get("event_values"):
                    event["values"] = arguments["event_values"]
                r = client.post("/v2/track/event/write", json={"keys": keys, "event": event})
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_user_events":
                payload = {
                    "user_id": arguments["user_id"],
                    "event_names": arguments.get("event_names", ["view"]),
                }
                options: dict = {}
                if arguments.get("limit") is not None:
                    options["limit"] = arguments["limit"]
                if arguments.get("from_unixtime_ms") is not None:
                    options["from"] = arguments["from_unixtime_ms"]
                if arguments.get("to_unixtime_ms") is not None:
                    options["to"] = arguments["to_unixtime_ms"]
                if options:
                    payload["options"] = options
                r = client.post("/v2beta/track/event/get", json=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "track_event_exec_action":
                keys = {}
                if arguments.get("user_id"):
                    keys["user_id"] = arguments["user_id"]
                elif arguments.get("visitor_id"):
                    keys["visitor_id"] = arguments["visitor_id"]
                else:
                    raise ValueError("user_id または visitor_id のいずれかが必要です")
                event = {"event_name": arguments["event_name"]}
                if arguments.get("event_values"):
                    event["values"] = arguments["event_values"]
                r = client.post("/v2beta/track/event/writeAndExecAction", json={"keys": keys, "event": event})
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_campaign":
                r = client.post("/v2beta/action/campaign/findById", json={"id": arguments["campaign_id"]})
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_campaign_stats":
                payload = {
                    "start_date": arguments["start_date"],
                    "end_date": arguments["end_date"],
                    "range": arguments.get("range", "latest_thirty_days"),
                }
                if "is_test" in arguments:
                    payload["is_test"] = arguments["is_test"]
                if "renew" in arguments:
                    payload["renew"] = arguments["renew"]
                r = client.post("/v2beta/action/campaign/getSettingsAndStats", json=payload)
                r.raise_for_status()
                return [types.TextContent(type="text", text=r.text)]

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
