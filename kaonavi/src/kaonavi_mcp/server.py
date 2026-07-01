import os
import time
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from ._http import format_response, error_response

app = Server("kaonavi-mcp")

BASE_URL = "https://api.kaonavi.jp/api/v2.0"

# Simple in-process token cache
_token_cache: dict = {}


def _get_token() -> str:
    now = time.time()
    if _token_cache.get("token") and _token_cache.get("expires_at", 0) > now + 60:
        return _token_cache["token"]

    consumer_key = os.environ.get("KAONAVI_CONSUMER_KEY")
    consumer_secret = os.environ.get("KAONAVI_CONSUMER_SECRET")
    if not consumer_key or not consumer_secret:
        raise ValueError("KAONAVI_CONSUMER_KEY と KAONAVI_CONSUMER_SECRET が設定されていません")

    r = httpx.post(
        f"{BASE_URL}/token",
        auth=(consumer_key, consumer_secret),
        headers={"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
        data={"grant_type": "client_credentials"},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    _token_cache["token"] = data["access_token"]
    # カオナビトークンの有効期限は expires_in 秒（通常3600）
    _token_cache["expires_at"] = now + data.get("expires_in", 3600)
    return _token_cache["token"]


def _client() -> httpx.Client:
    token = _get_token()
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "Kaonavi-Token": token,
            "Content-Type": "application/json",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_members",
            description=(
                "全メンバー（従業員）の基本情報・所属（主務）・兼務情報を取得する。カオナビ公開API v2の"
                "「メンバー情報 一括取得」(GET /members) はページネーションに対応しておらず、1回の呼び出しで"
                "全メンバー分がまとめて返る（レスポンスは {updated_at, member_data:[...]} 形式で、"
                "member_data の各要素に code・name・department・sub_departments・custom_fields 等が含まれる）。"
                "全件が不要な場合は updated_since で更新日以降のメンバーのみに絞り込める。特定1名だけで良い場合は "
                "get_member の方が読みやすいが、内部的には同じ一括取得APIを叩いてから絞り込んでいるため、"
                "複数名を調べる場合は本ツールを1回呼んでこちらで絞り込む方が効率的。書き込みは行わない"
                "（登録・更新・削除の各APIはカオナビ側に存在するが本コネクタは読み取り専用のため未実装）。"
                "1社につき毎時3,000回のリクエスト制限がある点に注意。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "updated_since": {
                        "type": "string",
                        "description": "この日付（YYYY-MM-DD形式）以降に更新されたメンバーのみに絞り込む（省略時は全メンバー）",
                    },
                },
            },
        ),
        types.Tool(
            name="get_member",
            description=(
                "社員コードを指定して特定1名のメンバー詳細（基本情報・所属・兼務・カスタム項目）を取得する。"
                "カオナビ公開API v2には社員コード指定で1名だけを取得するエンドポイントが存在しないため、本ツールは"
                "内部的に list_members と同じ一括取得API (GET /members) を呼び出し、結果から該当する code の"
                "メンバーをこちら側で絞り込んで返す実装になっている。そのため複数名を調べたい場合は、都度本ツールを"
                "繰り返し呼ぶよりも list_members を1回呼んで自分で絞り込む方がリクエスト数を節約できる。"
                "該当する社員コードが存在しない場合はその旨のメッセージを返す。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "社員コード（member_dataのcodeフィールド）"},
                },
                "required": ["code"],
            },
        ),
        types.Tool(
            name="list_departments",
            description=(
                "所属ツリー（部署階層）の全件を取得する。返るのはフラットなリスト（department_data配列）で、"
                "各要素が code・name・parent_code（親所属のcode、最上位はnull）・leader_member_code（責任者の"
                "社員コード、未設定はnull）・order（同一階層内の表示順）・memo を持つ。階層構造は parent_code を"
                "辿ることで自分で組み立てる必要がある（APIがネストしたツリーを直接返すわけではない）。絞り込み"
                "パラメータやページネーションはAPI側に存在せず、常に全所属が返る。所属ツリーの一括更新API "
                "(PUT /departments、Request Bodyに含まれない所属は削除される全置換方式) はカオナビ側に存在するが、"
                "本コネクタは読み取り専用のため未実装。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="list_layouts",
            description=(
                "シートレイアウト（カスタムシートの項目定義。get_sheet で取得するシートの構造）の一覧を取得する。"
                "sheet_id を指定するとそのシート1件のレイアウトのみ (GET /sheet_layouts/{sheet_id}) を取得し、"
                "省略すると利用可能な全シートのレイアウト (GET /sheet_layouts) をまとめて返す。get_sheet を呼ぶ前に"
                "対象の sheet_id や custom_fields のID・型を確認する目的で使うことが多い。メンバー基本情報側の"
                "項目定義（氏名・入社日などのレイアウト、GET /member_layouts 相当）は別リソースであり、本ツールの"
                "対象外（本コネクタでは未実装）。レイアウト定義の更新APIはカオナビ側に存在せず、レイアウトの変更は"
                "管理画面から行う必要がある。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "sheet_id": {
                        "type": "integer",
                        "description": "このシートIDのレイアウトのみ取得する（省略時は全シートのレイアウトを取得）",
                    },
                },
            },
        ),
        types.Tool(
            name="get_sheet",
            description=(
                "特定シート（カスタムシート、list_layoutsのidで指定）の全メンバー分のデータを取得する。"
                "レスポンスは {updated_at, member_data:[{code, records:[{custom_fields:[...]}], updated_at}, ...]} "
                "形式で、複数レコードシート（record_type=1、例: 家族情報や資格情報など1人が複数件持てるシート）の"
                "場合は records に複数要素が入る。ページネーションはAPI側に存在せず、常に全メンバー分が1回の"
                "レスポンスで返る。updated_since を指定するとその日付以降に更新されたメンバー分のみに絞り込める。"
                "シート情報の一括更新 (PUT)・部分更新 (PATCH) APIはカオナビ側に存在するが、本コネクタは読み取り"
                "専用のため未実装。書き込みは行わない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "sheet_id": {"type": "integer", "description": "シートID（list_layoutsのidで確認）"},
                    "updated_since": {
                        "type": "string",
                        "description": "この日付（YYYY-MM-DD形式）以降に更新されたメンバー分のみに絞り込む（省略時は全メンバー分）",
                    },
                },
                "required": ["sheet_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_members":
                params = {}
                if updated_since := arguments.get("updated_since"):
                    params["updated_since"] = updated_since
                r = client.get("/members", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_member":
                # カオナビ API v2 には社員コード指定の単体取得エンドポイントが存在しないため、
                # 一括取得APIを呼んでこちら側でフィルタする。
                code = arguments["code"]
                r = client.get("/members")
                r.raise_for_status()
                data = r.json()
                member = next(
                    (m for m in data.get("member_data", []) if m.get("code") == code),
                    None,
                )
                if member is None:
                    return format_response({"message": f"社員コード '{code}' のメンバーは見つかりませんでした。"})
                return format_response(member)

            elif name == "list_departments":
                r = client.get("/departments")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_layouts":
                if sheet_id := arguments.get("sheet_id"):
                    r = client.get(f"/sheet_layouts/{sheet_id}")
                else:
                    r = client.get("/sheet_layouts")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_sheet":
                sheet_id = arguments["sheet_id"]
                params = {}
                if updated_since := arguments.get("updated_since"):
                    params["updated_since"] = updated_since
                r = client.get(f"/sheets/{sheet_id}", params=params)
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
