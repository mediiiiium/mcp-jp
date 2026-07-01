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
| `list_candidacies` | 応募者（選考）一覧を取得。求人ID・選考状況(status)・選考ステップ(step)・終了理由・応募日時/ステップ更新日時の範囲で絞り込み可。1ページ100件固定のページネーション（page指定） |
| `get_candidacy` | 応募者1件の詳細情報を取得 |
| `list_requisitions` | 求人（ポジション）一覧を取得。募集状況・採用ページ掲載状況で絞り込み可。1ページ100件固定のページネーション（page指定） |
| `list_timeline_comments` | 応募者1名分のタイムラインコメント一覧を取得（ページネーションなし、全件返却） |
| `add_timeline_comment` | 応募者のタイムラインにコメントを追加（書式・メンション指定可、べき等ではない） |

## 既知の制約

HERP Hire API のページネーションは `page`（ページ番号、1ページ100件固定）方式であり、`limit`/`offset` は指定できません。

以下のエンドポイントは HERP Hire API に存在しないため、本コネクタにも対応するツールはありません（HERP Hire 管理画面から操作してください）。

- 応募者（candidacy）・求人（requisition）・タイムラインコメントいずれの削除
- 求人（requisition）自体の作成・更新
- タイムラインコメントの編集・削除

また、HERP Hire API には本コネクタで未実装の以下のエンドポイントも存在します（応募者ステップ更新・選考終了、コンタクト（面談記録）作成・一覧、評価(evaluations)の取得・提出、応募ファイルの取得、ユーザー一覧、担当者アサイン管理など）。必要になった場合は追加実装を検討してください。

## 使用例

```
エンジニア採用の応募者を全員リストアップして
```

```
田中さんの選考にコメント「一次面接通過、二次面接調整中」を追加して
```
