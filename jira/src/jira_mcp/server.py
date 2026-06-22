import os
import json
import base64
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("jira-mcp")


def _client() -> httpx.Client:
    email = os.environ.get("JIRA_EMAIL")
    api_token = os.environ.get("JIRA_API_TOKEN")
    subdomain = os.environ.get("JIRA_SUBDOMAIN")
    if not email:
        raise ValueError("JIRA_EMAIL が設定されていません")
    if not api_token:
        raise ValueError("JIRA_API_TOKEN が設定されていません")
    if not subdomain:
        raise ValueError("JIRA_SUBDOMAIN が設定されていません")
    credentials = base64.b64encode(f"{email}:{api_token}".encode()).decode()
    return httpx.Client(
        base_url=f"https://{subdomain}.atlassian.net/rest/api/3",
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        timeout=30,
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_projects",
            description="Jira プロジェクト一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "maxResults": {"type": "integer", "description": "取得件数上限（デフォルト50）"},
                    "query": {"type": "string", "description": "プロジェクト名でフィルタ"},
                },
            },
        ),
        types.Tool(
            name="search_issues",
            description="JQL でイシューを検索する",
            inputSchema={
                "type": "object",
                "properties": {
                    "jql": {"type": "string", "description": "JQL クエリ（例: project=ABC AND status=Open）"},
                    "maxResults": {"type": "integer", "description": "取得件数上限（デフォルト20）"},
                    "fields": {"type": "string", "description": "取得するフィールド（カンマ区切り、省略で主要フィールド）"},
                },
                "required": ["jql"],
            },
        ),
        types.Tool(
            name="get_issue",
            description="イシューの詳細を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {"type": "string", "description": "イシューキー（例: ABC-123）"},
                },
                "required": ["issue_key"],
            },
        ),
        types.Tool(
            name="create_issue",
            description="新しいイシューを作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_key": {"type": "string", "description": "プロジェクトキー（例: ABC）"},
                    "summary": {"type": "string", "description": "イシューのタイトル"},
                    "issue_type": {"type": "string", "description": "イシュータイプ（例: Bug, Task, Story）"},
                    "description": {"type": "string", "description": "イシューの説明（プレーンテキスト）"},
                    "priority": {"type": "string", "description": "優先度（例: High, Medium, Low）"},
                    "assignee_account_id": {"type": "string", "description": "担当者のアカウントID"},
                },
                "required": ["project_key", "summary", "issue_type"],
            },
        ),
        types.Tool(
            name="update_issue",
            description="イシューを更新する",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {"type": "string", "description": "イシューキー（例: ABC-123）"},
                    "summary": {"type": "string", "description": "新しいタイトル"},
                    "description": {"type": "string", "description": "新しい説明（プレーンテキスト）"},
                    "status_name": {"type": "string", "description": "遷移先ステータス名（例: In Progress, Done）"},
                    "priority": {"type": "string", "description": "新しい優先度"},
                },
                "required": ["issue_key"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _client()

    if name == "list_projects":
        params = {"maxResults": arguments.get("maxResults", 50)}
        if arguments.get("query"):
            params["query"] = arguments["query"]
        r = client.get("/project/search", params=params)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "search_issues":
        fields = arguments.get("fields", "summary,status,assignee,priority,issuetype,created,updated,description")
        payload = {
            "jql": arguments["jql"],
            "maxResults": arguments.get("maxResults", 20),
            "fields": fields.split(",") if isinstance(fields, str) else fields,
        }
        r = client.post("/search", json=payload)
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "get_issue":
        issue_key = arguments["issue_key"]
        r = client.get(f"/issue/{issue_key}")
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "create_issue":
        fields = {
            "project": {"key": arguments["project_key"]},
            "summary": arguments["summary"],
            "issuetype": {"name": arguments["issue_type"]},
        }
        if arguments.get("description"):
            fields["description"] = {
                "type": "doc",
                "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": arguments["description"]}]}],
            }
        if arguments.get("priority"):
            fields["priority"] = {"name": arguments["priority"]}
        if arguments.get("assignee_account_id"):
            fields["assignee"] = {"accountId": arguments["assignee_account_id"]}
        r = client.post("/issue", json={"fields": fields})
        r.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps(r.json(), ensure_ascii=False, indent=2))]

    elif name == "update_issue":
        issue_key = arguments["issue_key"]
        fields = {}
        if arguments.get("summary"):
            fields["summary"] = arguments["summary"]
        if arguments.get("description"):
            fields["description"] = {
                "type": "doc",
                "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": arguments["description"]}]}],
            }
        if arguments.get("priority"):
            fields["priority"] = {"name": arguments["priority"]}
        if fields:
            r = client.put(f"/issue/{issue_key}", json={"fields": fields})
            r.raise_for_status()
        if arguments.get("status_name"):
            tr = client.get(f"/issue/{issue_key}/transitions")
            tr.raise_for_status()
            transitions = tr.json().get("transitions", [])
            transition_id = next(
                (t["id"] for t in transitions if t["name"].lower() == arguments["status_name"].lower()), None
            )
            if transition_id:
                r2 = client.post(f"/issue/{issue_key}/transitions", json={"transition": {"id": transition_id}})
                r2.raise_for_status()
        return [types.TextContent(type="text", text=json.dumps({"result": "updated", "issue_key": issue_key}, ensure_ascii=False, indent=2))]

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
