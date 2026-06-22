# akashi-mcp

AKASHI / マネーフォワード クラウド勤怠Plus（クラウド勤怠管理システム）の MCP サーバー。公式 MCP 未提供。

## セットアップ

```bash
cd akashi
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `AKASHI_COMPANY_ID` | AKASHI 企業ID（ログイン URL から確認） |
| `AKASHI_TOKEN` | アクセストークン（管理画面 > 設定 > API設定で発行） |  # pragma: allowlist secret

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "akashi": {
      "command": "akashi-mcp",
      "env": {
        "AKASHI_COMPANY_ID": "your_company_id",
        "AKASHI_TOKEN": "your_access_token_here"  # pragma: allowlist secret
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `get_stamps` | 指定期間の打刻記録を取得する |
| `post_stamp` | 打刻を記録する（出勤・退勤・休憩など） |
| `list_staffs` | 従業員一覧を取得する |
| `get_staff` | 特定の従業員の詳細情報を取得する |
| `get_alerts` | 勤怠アラート一覧を取得する |

## 使用例

```
今月の全従業員の打刻記録を取得して
```

```
従業員ID 123 の今週の打刻を見せて
```

```
未打刻などのアラートがある従業員を教えて
```

```
出勤打刻を記録して
```
