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
| `list_comments` | チーム全体の最新コメントを横断的に一覧取得 |
| `get_post_comments` | 記事番号を指定して、その記事に紐づくコメントのみを一覧取得 |
| `list_tags` | チーム内で使われているタグを一覧取得（各タグの記事数つき） |
| `list_members` | チームメンバーを一覧取得（name/screen_name/role/posts_count等） |
| `get_team_stats` | チーム全体の統計情報を取得（記事数・コメント数・アクティブユーザー数等） |

## 既知の制約

esa API 自体には以下のエンドポイントが存在しますが、本コネクタでは実装していません（誤操作防止・スコープ限定のため）。必要な場合は esa の Web UI から操作してください。

- 記事の削除（`DELETE /v1/teams/:team_name/posts/:post_number`）
- コメントの投稿・更新・削除（`POST` / `PATCH` / `DELETE /v1/teams/:team_name/comments/...`, `POST /v1/teams/:team_name/posts/:post_number/comments`）— 閲覧系の `list_comments` / `get_post_comments` のみ実装
- スター・Watch の付与/解除（`POST`/`DELETE .../star`, `.../watch`）— 一覧取得（stargazers/watchers）も含め未実装（誤操作リスクに対して需要の確証がなく見送り）
- カテゴリの一括移動（`POST /v1/teams/:team_name/categories/batch_move`）— 書き込み系かつ一括操作で影響範囲が広いため見送り
- メンバーの削除・招待の発行/一覧/削除（`DELETE /v1/teams/:team_name/members/...`, `.../invitations/...`）— アカウント管理系はスコープ外として見送り。読み取りの `list_members` のみ実装
- 絵文字管理（`GET`/`POST`/`DELETE /v1/teams/:team_name/emojis/...`）— チーム運営上の需要が確認できず見送り
- `GET /v1/teams`（自分が所属する全チーム一覧）、`GET /v1/user`（認証ユーザー情報） — 本コネクタは `ESA_TEAM_NAME` で対象チームを固定運用する設計のため、マルチチーム前提のこれらのエンドポイントは現時点でスコープ外

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
