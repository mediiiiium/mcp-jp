# notepm-mcp

NotePM（日本SMB向け社内wiki・ナレッジ共有・マニュアル作成ツール）の MCP サーバー。公式 MCP 未提供。

## セットアップ

```bash
cd notepm
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `NOTEPM_TEAM_DOMAIN` | NotePM のチームドメイン（例: `mycompany` → `mycompany.notepm.jp` の場合） |
| `NOTEPM_ACCESS_TOKEN` | 設定 → API連携 で発行したアクセストークン |  # pragma: allowlist secret

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "notepm": {
      "command": "notepm-mcp",
      "env": {
        "NOTEPM_TEAM_DOMAIN": "your_team_domain",
        "NOTEPM_ACCESS_TOKEN": "your_access_token_here"  # pragma: allowlist secret
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_notes` | ノート（スペース）一覧を取得 |
| `search_pages` | キーワードでページを検索（タグ・ノート絞り込み可） |
| `get_page` | ページの詳細情報（本文）を取得 |
| `create_page` | 新しいページを作成 |
| `update_page` | 既存ページを更新 |

## 使用例

```
「オンボーディング」に関するページを検索して
```

```
営業マニュアルのノートに「商談クロージングチェックリスト」というページを作成して
```

```
page_code NP001 のページ内容を見せて
```
