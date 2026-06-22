# hrmos-kintai-mcp

HRMOS勤怠（旧IEYASU、日本SMB向けクラウド勤怠管理システム）の MCP サーバー。公式 MCP 未提供。

## セットアップ

```bash
cd hrmos-kintai
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `HRMOS_COMPANY_URL` | ログインURLに含まれる会社識別子（例: `mycompany` → `https://ieyasu.co/mycompany/` のとき） |
| `HRMOS_API_KEY` | 管理画面 → API設定 で発行したシークレットキー |  # pragma: allowlist secret

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "hrmos-kintai": {
      "command": "hrmos-kintai-mcp",
      "env": {
        "HRMOS_COMPANY_URL": "your_company_url",
        "HRMOS_API_KEY": "your_api_key_here"  # pragma: allowlist secret
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `get_monthly_attendance` | 指定月の月次勤怠データを取得（全社員） |
| `get_daily_attendance` | 指定日の日次勤怠データを取得（全社員） |
| `list_users` | 社員一覧を取得 |
| `list_departments` | 部署一覧を取得 |
| `get_user_stamps` | 指定社員の打刻履歴を取得 |

## 使用例

```
今月（2026年6月）の勤怠データを見せて
```

```
社員一覧を表示して
```

```
田中さん（user_id: 123）の先月の打刻履歴を確認して
```
