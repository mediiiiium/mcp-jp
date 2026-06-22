# talentio-mcp

Talentio（日本向け採用管理システム）の MCP サーバー。公式 MCP 未提供。

## セットアップ

```bash
cd talentio
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `TALENTIO_ACCESS_TOKEN` | Talentio のアクセストークン（Developer Console から取得） |  # pragma: allowlist secret

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "talentio": {
      "command": "talentio-mcp",
      "env": {
        "TALENTIO_ACCESS_TOKEN": "your_token_here"  
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_candidates` | 候補者一覧を取得（ページネーション対応） |
| `get_candidate` | 候補者の詳細情報を取得 |
| `list_jobs` | 求人（ポジション）一覧を取得 |
| `list_applications` | 応募一覧を取得（求人IDで絞り込み可） |
| `list_pipeline_stages` | 選考パイプラインのステージ一覧を取得 |

## 使用例

```
エンジニア採用の応募者を全員リストアップして
```

```
現在オープンな求人を教えて
```
