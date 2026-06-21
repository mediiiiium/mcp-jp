# jobcan-workflow-mcp

ジョブカン経費精算/ワークフローの MCP サーバー。申請書の確認・ユーザー・プロジェクト・取引先情報を AI から操作できます。

## セットアップ

```bash
cd jobcan-workflow
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `JOBCAN_API_TOKEN` | ジョブカン APIトークン（管理画面の「共通ID連携・API管理」から発行） |

### APIトークンの取得

1. ジョブカン経費精算/ワークフローにログイン
2. 管理者画面 → 「共通ID連携・API管理」タブ
3. 「認証コード発行」画面で「発行する」をクリック

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "jobcan-workflow": {
      "command": "jobcan-workflow-mcp",
      "env": {
        "JOBCAN_API_TOKEN": "your_api_token_here"
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_requests` | 申請書一覧を取得（ステータス・申請者・日付で絞り込み可） |
| `get_request` | 申請書の詳細情報を取得 |
| `list_users` | ユーザー一覧を取得 |
| `list_projects` | プロジェクト一覧を取得 |
| `list_companies` | 取引先一覧を取得 |

## 使用例

```
今月の申請書をすべて見せて
```

```
進行中の申請書一覧を表示して
```

```
申請書ID 12345 の詳細を見せて
```

```
ユーザー一覧を取得して
```

```
登録されているプロジェクト一覧を教えて
```
