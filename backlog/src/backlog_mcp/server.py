import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("backlog-mcp")


def _client() -> httpx.Client:
    api_key = os.environ.get("BACKLOG_API_KEY")
    space = os.environ.get("BACKLOG_SPACE")
    domain = os.environ.get("BACKLOG_DOMAIN", "backlog.jp")
    if not api_key:
        raise ValueError("BACKLOG_API_KEY が設定されていません")
    if not space:
        raise ValueError("BACKLOG_SPACE が設定されていません")
    return httpx.Client(
        base_url=f"https://{space}.{domain}/api/v2",
        params={"apiKey": api_key},
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_projects",
            description="プロジェクト一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "archived": {
                        "type": "boolean",
                        "description": "アーカイブ済みプロジェクトを含めるか（デフォルト: false）",
                        "default": False,
                    },
                },
            },
        ),
        types.Tool(
            name="list_issues",
            description="課題一覧を取得する（プロジェクト・担当者・優先度・ステータスで絞り込み可）",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "プロジェクトIDのリストで絞り込み",
                    },
                    "assignee_id": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "担当者IDのリストで絞り込み",
                    },
                    "status_id": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "ステータスIDのリスト（1:未対応, 2:処理中, 3:処理済み, 4:完了）",
                    },
                    "keyword": {"type": "string", "description": "キーワード検索"},
                    "count": {"type": "integer", "description": "取得件数（最大100）", "default": 20},
                    "offset": {"type": "integer", "description": "オフセット", "default": 0},
                },
            },
        ),
        types.Tool(
            name="get_issue",
            description="課題の詳細情報を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_id_or_key": {
                        "type": "string",
                        "description": "課題ID または 課題キー（例: PROJECT-123）",
                    },
                },
                "required": ["issue_id_or_key"],
            },
        ),
        types.Tool(
            name="create_issue",
            description="新しい課題を作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer", "description": "プロジェクトID"},
                    "summary": {"type": "string", "description": "課題の件名"},
                    "issue_type_id": {"type": "integer", "description": "課題種別ID"},
                    "priority_id": {
                        "type": "integer",
                        "description": "優先度ID（2:高, 3:中, 4:低）",
                        "default": 3,
                    },
                    "description": {"type": "string", "description": "詳細説明"},
                    "assignee_id": {"type": "integer", "description": "担当者ID"},
                    "due_date": {"type": "string", "description": "期限日 YYYY-MM-DD"},
                },
                "required": ["project_id", "summary", "issue_type_id"],
            },
        ),
        types.Tool(
            name="add_issue_comment",
            description="課題にコメントを追加する",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_id_or_key": {
                        "type": "string",
                        "description": "課題ID または 課題キー（例: PROJECT-123）",
                    },
                    "content": {"type": "string", "description": "コメント本文"},
                },
                "required": ["issue_id_or_key", "content"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "list_projects":
        params: dict = {}
        if arguments.get("archived") is not None:
            params["archived"] = arguments["archived"]
        r = client.get("/projects", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "list_issues":
        params = {
            "count": arguments.get("count", 20),
            "offset": arguments.get("offset", 0),
        }
        if arguments.get("project_id"):
            for pid in arguments["project_id"]:
                params.setdefault("projectId[]", []).append(pid)
        if arguments.get("assignee_id"):
            for aid in arguments["assignee_id"]:
                params.setdefault("assigneeId[]", []).append(aid)
        if arguments.get("status_id"):
            for sid in arguments["status_id"]:
                params.setdefault("statusId[]", []).append(sid)
        if arguments.get("keyword"):
            params["keyword"] = arguments["keyword"]
        r = client.get("/issues", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_issue":
        key = arguments["issue_id_or_key"]
        r = client.get(f"/issues/{key}")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "create_issue":
        data: dict = {
            "projectId": arguments["project_id"],
            "summary": arguments["summary"],
            "issueTypeId": arguments["issue_type_id"],
            "priorityId": arguments.get("priority_id", 3),
        }
        if arguments.get("description"):
            data["description"] = arguments["description"]
        if arguments.get("assignee_id"):
            data["assigneeId"] = arguments["assignee_id"]
        if arguments.get("due_date"):
            data["dueDate"] = arguments["due_date"]
        r = client.post("/issues", data=data)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "add_issue_comment":
        key = arguments["issue_id_or_key"]
        r = client.post(f"/issues/{key}/comments", data={"content": arguments["content"]})
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
