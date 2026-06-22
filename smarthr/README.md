# smarthr-mcp

SmartHR 人事・労務管理の MCP サーバー。

## セットアップ

```bash
cd smarthr
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `SMARTHR_ACCESS_TOKEN` | SmartHR 管理画面で発行したアクセストークン |
| `SMARTHR_TENANT_ID` | SmartHR のテナントID（URLの `{tenant}.smarthr.jp` 部分） |

アクセストークンは SmartHR 管理画面 → アプリ連携 → アクセストークン から取得してください。

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "smarthr": {
      "command": "smarthr-mcp",
      "env": {
        "SMARTHR_ACCESS_TOKEN": "your_token_here",  # pragma: allowlist secret
        "SMARTHR_TENANT_ID": "your_tenant_id"
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_crews` | 従業員一覧を取得（部署・雇用形態で絞り込み可） |
| `get_crew` | 特定の従業員の詳細情報を取得 |
| `list_departments` | 部署一覧を取得 |
| `list_employment_types` | 雇用形態一覧を取得（正社員・パート等） |
| `update_crew` | 従業員情報を更新（部署異動・雇用形態変更等） |

## 使用例

```
営業部の従業員を全員リストアップして
```

```
田中さんを開発部に異動させて
```

```
現在の雇用形態の種類を教えて
```
