# herp-mcp

HERP Hire（日本向け採用管理システム）の MCP サーバー。公式 MCP 未提供。

## セットアップ

```bash
cd herp
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `HERP_API_KEY` | HERP Hire の API キー（管理画面 → API設定から取得） |  # pragma: allowlist secret

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "herp": {
      "command": "herp-mcp",
      "env": {
        "HERP_API_KEY": "your_api_key_here"  # pragma: allowlist secret
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_candidacies` | 応募者（選考）一覧を取得（求人IDで絞り込み可） |
| `get_candidacy` | 応募者の詳細情報を取得 |
| `list_requisitions` | 求人（ポジション）一覧を取得 |
| `list_timeline_comments` | 応募者のタイムラインコメント一覧を取得 |
| `add_timeline_comment` | 応募者のタイムラインにコメントを追加 |

## 使用例

```
エンジニア採用の応募者を全員リストアップして
```

```
田中さんの選考にコメント「一次面接通過、二次面接調整中」を追加して
```
