# circleci-mcp

CircleCI MCP サーバー。CI/CD パイプライン・ワークフロー・ジョブの管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `CIRCLECI_TOKEN` | ✅ | CircleCI Personal API Token |

## API Token 取得方法

1. CircleCI にログイン
2. 右上のアバター → **User Settings** → **Personal API Tokens**
3. **Create New Token** → Token name を入力して **Add API Token** をクリック

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `get_current_user` | 現在のユーザー情報を取得する |
| `list_pipelines` | プロジェクトのパイプライン一覧を取得する |
| `list_workflows` | パイプラインのワークフロー一覧を取得する |
| `list_jobs` | ワークフローのジョブ一覧を取得する |
| `get_job_details` | ジョブの詳細を取得する |

## プロジェクトスラッグの形式

`{vcs}/{org}/{repo}` の形式で指定します。

例: `github/myorg/myrepo`、`bitbucket/myorg/myrepo`

## インストール

```bash
cd circleci
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "circleci": {
      "command": "circleci-mcp",
      "env": {
        "CIRCLECI_TOKEN": "your_circleci_token"
      }
    }
  }
}
```
