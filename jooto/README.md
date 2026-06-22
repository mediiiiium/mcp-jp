# jooto-mcp

Jooto（日本SMB向けタスク・プロジェクト管理ツール）の MCP サーバー。公式 MCP 未提供。

## セットアップ

```bash
cd jooto
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `JOOTO_API_KEY` | Jooto 管理画面で発行した API キー |  # pragma: allowlist secret

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "jooto": {
      "command": "jooto-mcp",
      "env": {
        "JOOTO_API_KEY": "your_api_key_here"  # pragma: allowlist secret
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_organizations` | 所属するオーガニゼーション一覧を取得 |
| `list_boards` | オーガニゼーション内のボード（プロジェクト）一覧を取得 |
| `list_tasks` | ボード内のタスク一覧を取得（担当者で絞り込み可） |
| `create_task` | 新しいタスクを作成 |
| `get_task` | タスクの詳細情報を取得 |

## 使用例

```
営業チームのボードにあるタスク一覧を見せて
```

```
「ランディングページ修正」というタスクを「Webサイト改善」ボードに作成して、期限は2026-07-31
```

```
未完了タスクの一覧を表示して
```
