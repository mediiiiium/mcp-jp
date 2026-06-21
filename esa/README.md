# esa-mcp

esa（チームナレッジ共有）の MCP サーバー。記事の検索・閲覧・投稿・更新を AI から操作できます。

## セットアップ

```bash
cd esa
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `ESA_ACCESS_TOKEN` | esa パーソナルアクセストークン（アカウント設定から発行） |
| `ESA_TEAM_NAME` | チーム名（`yourteam.esa.io` の `yourteam` 部分） |

### アクセストークンの取得

1. esa にログイン
2. 右上のアイコン → 「アカウント設定」→「アプリケーション」
3. 「個人アクセストークンを発行する」でトークンを発行

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "esa": {
      "command": "esa-mcp",
      "env": {
        "ESA_ACCESS_TOKEN": "your_access_token_here",
        "ESA_TEAM_NAME": "your-team-name"
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_posts` | 記事一覧を取得（キーワード・カテゴリ・タグ・WIPで絞り込み可） |
| `get_post` | 記事番号を指定して記事を取得 |
| `create_post` | 新しい記事を作成 |
| `update_post` | 既存の記事を更新 |
| `list_comments` | チーム全体のコメント一覧を取得 |

## 使用例

```
開発カテゴリの最新記事を見せて
```

```
APIという単語が含まれる記事を検索して
```

```
記事 #123 の内容を教えて
```

```
「今週のミーティングメモ」というタイトルで記事を作成して
```

```
記事 #456 のタイトルを「MTG議事録 2024-01」に更新して
```
