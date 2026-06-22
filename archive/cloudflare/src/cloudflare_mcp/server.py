import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("cloudflare-mcp")
BASE_URL = "https://api.cloudflare.com/client/v4"


def _client() -> httpx.Client:
    api_token = os.environ.get("CLOUDFLARE_API_TOKEN")
    if not api_token:
        raise ValueError("CLOUDFLARE_API_TOKEN が設定されていません")
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_zones",
            description="ゾーン（ドメイン）一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "ドメイン名でフィルタ"},
                    "per_page": {"type": "integer", "description": "1ページあたりの件数（デフォルト20）"},
                },
            },
        ),
        types.Tool(
            name="list_dns_records",
            description="DNS レコード一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "zone_id": {"type": "string", "description": "ゾーンID"},
                    "type": {"type": "string", "description": "レコードタイプ（例: A, CNAME, MX）"},
                    "name": {"type": "string", "description": "ホスト名でフィルタ"},
                },
                "required": ["zone_id"],
            },
        ),
        types.Tool(
            name="create_dns_record",
            description="DNS レコードを作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "zone_id": {"type": "string", "description": "ゾーンID"},
                    "type": {"type": "string", "description": "レコードタイプ（A, AAAA, CNAME, MX, TXT など）"},
                    "name": {"type": "string", "description": "ホスト名（例: www）"},
                    "content": {"type": "string", "description": "レコードの値（例: 1.2.3.4）"},
                    "ttl": {"type": "integer", "description": "TTL（秒、1=自動）"},
                    "proxied": {"type": "boolean", "description": "Cloudflare プロキシを有効にする（デフォルトfalse）"},
                },
                "required": ["zone_id", "type", "name", "content"],
            },
        ),
        types.Tool(
            name="purge_cache",
            description="ゾーンのキャッシュをパージする",
            inputSchema={
                "type": "object",
                "properties": {
                    "zone_id": {"type": "string", "description": "ゾーンID"},
                    "purge_everything": {"type": "boolean", "description": "全キャッシュをパージ（デフォルトtrue）"},
                    "files": {"type": "array", "items": {"type": "string"}, "description": "特定のファイルURLをパージ"},
                },
                "required": ["zone_id"],
            },
        ),
        types.Tool(
            name="get_zone_analytics",
            description="ゾーンのアクセス統計を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "zone_id": {"type": "string", "description": "ゾーンID"},
                    "since": {"type": "string", "description": "開始時刻（ISO8601形式）"},
                    "until": {"type": "string", "description": "終了時刻（ISO8601形式）"},
                },
                "required": ["zone_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "list_zones":
        params = {"per_page": arguments.get("per_page", 20)}
        if arguments.get("name"):
            params["name"] = arguments["name"]
        r = client.get("/zones", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_dns_records":
        zone_id = arguments["zone_id"]
        params = {}
        if arguments.get("type"):
            params["type"] = arguments["type"]
        if arguments.get("name"):
            params["name"] = arguments["name"]
        r = client.get(f"/zones/{zone_id}/dns_records", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "create_dns_record":
        zone_id = arguments["zone_id"]
        payload = {
            "type": arguments["type"],
            "name": arguments["name"],
            "content": arguments["content"],
            "ttl": arguments.get("ttl", 1),
            "proxied": arguments.get("proxied", False),
        }
        r = client.post(f"/zones/{zone_id}/dns_records", json=payload)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "purge_cache":
        zone_id = arguments["zone_id"]
        if arguments.get("files"):
            payload = {"files": arguments["files"]}
        else:
            payload = {"purge_everything": arguments.get("purge_everything", True)}
        r = client.post(f"/zones/{zone_id}/purge_cache", json=payload)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_zone_analytics":
        zone_id = arguments["zone_id"]
        params = {}
        if arguments.get("since"):
            params["since"] = arguments["since"]
        if arguments.get("until"):
            params["until"] = arguments["until"]
        r = client.get(f"/zones/{zone_id}/analytics/dashboard", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    else:
        raise ValueError(f"未知のツール: {name}")


def main():
    import asyncio

    async def _run():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

    asyncio.run(_run())


if __name__ == "__main__":
    main()
