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
| `list_notes` | ノート（フォルダに近い単位）一覧を取得。アーカイブ済みを含めるか指定可 |
| `search_pages` | ページを検索・一覧取得（キーワード・ノート・タグ・作成者・アーカイブ有無で絞り込み可） |
| `get_page` | ページの詳細情報（本文・タグ・コメント含む）を取得 |
| `create_page` | 新しいページを作成（格納先フォルダ指定可） |
| `update_page` | 既存ページを部分更新（別ノートへの移動・フォルダ移動も可） |

いずれもページングは `page`/`per_page` 方式（カーソル方式ではない）で、レスポンスの `total`・`next_page`・`previous_page` から次ページの有無や総件数を確認する。

## API の制限事項

- NotePM API には `note`・`page` それぞれに削除エンドポイントが存在するが、誤削除防止のため本コネクタには削除ツールを実装していない（削除は NotePM の Web UI から行う）。
- ノートの作成・更新・アーカイブ化/復元エンドポイントも存在するが、本コネクタは参照系（`list_notes`）のみに対応。
- ページ作成時に作成者・作成日時を上書きするパラメータ（`user`/`created_at`、主にデータ移行用途）が API には存在するが、なりすまし防止のため本コネクタからは指定できない。
- コメント・添付ファイル・ユーザー・グループ・サービス連携（Slack/Webhook等）用のエンドポイントも API には存在するが、本コネクタは未対応。
- `search_pages` の `created` パラメータは名前に反して日付ではなく「作成者（ユーザーコード）」で絞り込むもの。
- 検索・一覧のソート順は API ドキュメントに明記がなく、本コネクタから指定することはできない。
- API のレート制限はユーザーごとに1分間60リクエストまで（超過時は HTTP 429）。

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
