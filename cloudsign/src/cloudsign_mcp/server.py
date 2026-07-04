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
    # CloudSign Web API は書類の作成・更新・送信系エンドポイントを
    # application/x-www-form-urlencoded でのみ受け付ける（JSON 不可、公式 API 仕様書で確認済み）。
    # そのため Content-Type はここで固定せず、リクエストごとに data=（form-urlencoded）か
    # json=（GET 系の一部で使うことがある）を httpx に判断させる。
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "Authorization": f"Bearer {token}",
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
                "status でステータス絞り込みが可能（get_document で個別の詳細を見る前に対象の document_id を"
                "探す用途で使うことが多い）。ページネーションは page 方式（1始まり、1ページ最大100件）。"
                "CloudSign Web API 仕様書（SwaggerHub: CloudSign/cloudsign-web_api）で確認する限り、本エンドポイントに"
                "タイトルの部分一致検索パラメータは存在しない（該当する書類を絞り込みたい場合は status で範囲を"
                "絞った上で、レスポンス中の title を確認する）。既定の並び順は CloudSign API 側の仕様として"
                "明記されていない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "integer",
                        "enum": [-1, 0, 1, 2, 3, 4],
                        "description": (
                            "書類ステータスで絞り込む（-1=全ての状態 / 0=下書き / 1=先方確認中 / 2=締結済 / "
                            "3=取消または却下 / 4=テンプレート）。既定は -1（全件）。CloudSign Web API 仕様書の"
                            "documentModel.status の説明文には 13=インポート書類 という値も記載されているが、"
                            "本エンドポイントの status パラメータの enum には含まれていない（インポート書類を"
                            "個別に絞り込む方法は本エンドポイントには無いと考えられる）。"
                        ),
                        "default": -1,
                    },
                    "page": {"type": "integer", "description": "ページ番号（1始まり、1ページ最大100件）", "default": 1},
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
                "send_document で送信する必要がある。CloudSign Web API 仕様書には下書き状態限定の削除API"
                "（DELETE /documents/{documentID}）が存在するが、本コネクタには実装されていない（誤って作成した"
                "書類は管理画面から削除・無効化してください）。"
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
                "下書き状態の書類に署名者（宛先）を追加する。CloudSign Web API の宛先追加エンドポイント"
                "（POST /documents/{documentID}/participants）を参加者リストの順に1件ずつ呼び出す実装のため、"
                "呼び出すたびに新しい宛先が追加される（既存の宛先を上書きするものではない）。send_document で"
                "送信する前に必ず呼び出す必要がある（宛先未設定のまま送信することはできない）。追加した宛先の"
                "順序が署名依頼の送信順になる（1番目の相手が同意/署名した後に2番目へ通知が送られる、といった"
                "逐次送信）。同じ書類に対して本ツールを複数回呼び出すと、そのたびに宛先が追加されていく点に注意"
                "（重複して追加したくない場合は get_document で現在の宛先を確認してから呼び出す）。作成者自身が"
                "書類作成時点で宛先の1人目（送信者、order=0）として含まれている可能性がある（documentModel の"
                "仕様上の記載）。send_document 実行後は宛先の変更・並び替えはできない。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "対象の書類ID（下書き状態であること）"},
                    "participants": {
                        "type": "array",
                        "description": "追加する署名者リスト。配列の順序＝署名依頼を送る順序（1番目から順に逐次送信される）",
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
                "事前に set_participants で参加者を設定しておく必要がある。CloudSign Web API 仕様では、既に"
                "「先方確認中」状態の書類に対して本エンドポイントを呼び出すと送信ではなくリマインド通知として"
                "扱われる（エラーにはならない）。送信を取り消す（キャンセルする）APIはCloudSign 側に提供されて"
                "いないため、誤送信時は管理画面から手動で取消・却下操作を行う必要がある。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "送信する書類ID（下書き状態かつ参加者設定済みであること）"},
                },
                "required": ["document_id"],
            },
        ),
        types.Tool(
            name="get_document_alert",
            description=(
                "書類のアラート情報（契約更新・満了確認などのためにユーザーが設定したリマインド日と有効/無効"
                "フラグ、メモ）を取得する。get_document のレスポンスには含まれない付随情報のため独立したツールに"
                "している。document_id は list_documents や get_document で取得したIDを指定する。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "対象の書類ID"},
                },
                "required": ["document_id"],
            },
        ),
        types.Tool(
            name="get_document_attribute",
            description=(
                "書類の管理用属性情報（契約相手の名称、契約締結日・契約開始日・契約終了日・解約通知期限、"
                "自動更新の有無、取引金額、管理番号、ユーザー定義項目など）を取得する。get_document のレスポンス"
                "には含まれない、契約管理台帳的な情報を確認したい場合に使う。document_id は list_documents や"
                "get_document で取得したIDを指定する。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "対象の書類ID"},
                },
                "required": ["document_id"],
            },
        ),
        types.Tool(
            name="get_me",
            description=(
                "Web API を実行しているユーザー自身の情報（ID・メールアドレス・氏名・所属組織・所属チーム・"
                "保持している権限）を取得する。認証しているアカウントがどのチーム・権限で動いているかを確認する"
                "用途に使う。CloudSign 側の仕様として、複数部署管理機能を利用しているアカウントでは本APIは"
                "利用できない（エラーになる）。読み取り専用。"
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="list_team_documents",
            description=(
                "チーム内のメンバー全員がやり取りした書類の一覧を取得する。list_documents は自分が作成・関与した"
                "書類のみが対象だが、本ツールはチーム全体の書類（先方確認中・締結済・取消/却下・インポート書類の"
                "みで、下書きやテンプレートは含まれない）を横断して確認できる。CloudSign 側の仕様として、"
                "管理者権限を持たないアカウントや複数部署管理機能を利用しているアカウントは利用できない"
                "（エラーになる）。ページネーションは page 方式（1始まり、1ページ最大100件）。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり、1ページ最大100件）", "default": 1},
                },
            },
        ),
        types.Tool(
            name="list_cabinets",
            description=(
                "キャビネット（書類を整理するフォルダ）の一覧を取得する。アクセス許可があるキャビネットのみ"
                "返される。list_cabinet_documents でキャビネット内の書類を見る前に、対象の cabinet_id を調べる"
                "用途に使う。ページネーションは page 方式（1始まり、1ページ最大100件）。読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "ページ番号（1始まり、1ページ最大100件）", "default": 1},
                },
            },
        ),
        types.Tool(
            name="list_cabinet_documents",
            description=(
                "指定したキャビネットに格納されている書類の一覧を取得する。CloudSign 側の仕様として"
                "**エンタープライズプラン限定**の機能で、それ以外のプランでは利用できない（エラーになる）。"
                "cabinet_id は list_cabinets で取得したIDを指定する。取得できる書類の総数は最大10,000件"
                "（100ページ）までで、それを超える場合は from/to で最終処理日時の範囲を絞り込む必要がある。"
                "受信管理者側で非表示に設定された書類は結果から除外されるが、total（総件数）にはそれらも"
                "含まれる場合がある点に注意。ページネーションは page 方式（1始まり、1ページ最大100件）。"
                "読み取り専用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "cabinet_id": {"type": "string", "description": "対象のキャビネットID（list_cabinets で取得）"},
                    "page": {"type": "integer", "description": "ページ番号（1始まり、1ページ最大100件）", "default": 1},
                    "from_date": {"type": "string", "description": "書類の最終処理日時の範囲開始（RFC3339形式）"},
                    "to_date": {"type": "string", "description": "書類の最終処理日時の範囲終了（RFC3339形式）"},
                },
                "required": ["cabinet_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        with _client() as client:
            if name == "list_documents":
                params = {"page": arguments.get("page", 1)}
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
                # CloudSign Web API は application/x-www-form-urlencoded のみ受け付ける
                r = client.post("/documents", data=payload)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "set_participants":
                document_id = arguments["document_id"]
                results = []
                for p in arguments["participants"]:
                    payload = {"email": p["email"], "name": p["name"]}
                    # CloudSign Web API の宛先追加 API（宛先ごとに1件ずつ POST で追加する）
                    r = client.post(f"/documents/{document_id}/participants", data=payload)
                    r.raise_for_status()
                    results.append(r.json())
                return format_response(results)

            elif name == "send_document":
                # 下書き→送信、または先方確認中の書類へのリマインドは POST（ボディなし）
                r = client.post(f"/documents/{arguments['document_id']}")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_document_alert":
                r = client.get(f"/documents/{arguments['document_id']}/alert")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_document_attribute":
                r = client.get(f"/documents/{arguments['document_id']}/attribute")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "get_me":
                r = client.get("/me")
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_team_documents":
                params = {"page": arguments.get("page", 1)}
                r = client.get("/team_documents", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_cabinets":
                params = {"page": arguments.get("page", 1)}
                r = client.get("/cabinets", params=params)
                r.raise_for_status()
                return format_response(r.json())

            elif name == "list_cabinet_documents":
                params = {
                    "cabinet_id": arguments["cabinet_id"],
                    "page": arguments.get("page", 1),
                }
                if arguments.get("from_date"):
                    params["from"] = arguments["from_date"]
                if arguments.get("to_date"):
                    params["to"] = arguments["to_date"]
                r = client.get("/cabinet_documents", params=params)
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
