# board-mcp

board（日本向けクラウド業務・経営管理システム）の MCP サーバー。公式 MCP 未提供。

見積書・発注書・納品書・請求書・プロジェクト管理・顧客管理をカバー。

## セットアップ

```bash
cd board
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `BOARD_API_KEY` | board 管理画面で発行した API キー（x-api-key ヘッダー） |  # pragma: allowlist secret
| `BOARD_API_TOKEN` | board 管理画面で発行した API トークン（Bearer トークン） |  # pragma: allowlist secret

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "board": {
      "command": "board-mcp",
      "env": {
        "BOARD_API_KEY": "your_api_key_here",  # pragma: allowlist secret
        "BOARD_API_TOKEN": "your_api_token_here"  # pragma: allowlist secret
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_clients` | 顧客一覧を取得（名前で絞り込み可） |
| `list_projects` | プロジェクト一覧を取得（顧客・ステータスで絞り込み可） |
| `get_project` | プロジェクトの詳細情報を取得 |
| `list_invoices` | 請求書一覧を取得（顧客・プロジェクトで絞り込み可） |
| `create_project` | 新しいプロジェクトを作成 |

## 使用例

```
今月の請求書一覧を見せて
```

```
株式会社ABCのプロジェクト一覧を表示して
```

```
新しいプロジェクト「ウェブサイトリニューアル」を株式会社XYZ向けに作成して、予算は500万円
```
