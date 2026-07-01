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
| `list_posts` | esa独自の検索クエリ構文（title:/body:/category:/tag:/wip:/kind:/sharing:/starred:/@user/created:/updated:/stars:/comments:/backlinks:/!in: 等）で記事を検索・一覧取得。page/per_page方式のページネーション |
| `get_post` | 記事番号を指定して1件取得。include でコメント・スター・backlinksを同時取得可能 |
| `create_post` | 新しい記事を作成（べき等ではなく、呼ぶたびに新規記事が作られる） |
| `update_post` | 既存記事を部分更新。original_revision を渡すと3-way mergeで同時編集の衝突を検知できる |
| `list_comments` | チーム全体の最新コメントを横断的に一覧取得（記事単位のコメント取得は未実装） |

## 既知の制約

esa API 自体には以下のエンドポイントが存在しますが、本コネクタでは実装していません（誤操作防止・スコープ限定のため）。必要な場合は esa の Web UI から操作してください。

- 記事の削除（`DELETE /v1/teams/:team_name/posts/:post_number`）
- コメントの投稿・更新・削除（`POST` / `PATCH` / `DELETE /v1/teams/:team_name/comments/...`）、および記事単位のコメント取得（`GET /v1/teams/:team_name/posts/:post_number/comments`）— 本コネクタの `list_comments` はチーム全体のコメント一覧のみ取得可能
- スター・Watch の付与/解除（`POST`/`DELETE .../star`, `.../watch`）
- カテゴリの一括移動（`POST /v1/teams/:team_name/categories/batch_move`）
- メンバー・招待の管理

また、esa API にはレートリミットがあり、15分間に300リクエストまで（超過時は429エラー）。大量取得時は per_page（最大100）を活用してリクエスト数を抑えてください。

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
