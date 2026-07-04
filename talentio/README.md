# talentio-mcp

Talentio（日本向け採用管理システム）の MCP サーバー。公式 MCP 未提供。

- API ドキュメント: https://developers.talentio.com/

## セットアップ

```bash
cd talentio
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `TALENTIO_ACCESS_TOKEN` | Talentio のアクセストークン（Business プラン以上、管理者権限で発行可能。Talentio Help Center「APIの利用」参照） |  # pragma: allowlist secret

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
| `list_candidates` | 候補者（＝応募者）一覧を取得（求人ID・選考ステータス・日付範囲での絞り込み対応、ページネーション対応） |
| `get_candidate` | 候補者の詳細情報を取得（選考ステージごとの評価を含む） |
| `list_jobs` | 求人（Talentio API 上は requisition）一覧を取得（募集状況での絞り込み対応） |
| `get_job` | 求人の詳細情報を取得 |
| `list_job_titles` | 職種一覧を取得（紐づく求人一覧を含む） |
| `list_candidate_channels` | 候補者の応募経路（チャネル）一覧を取得 |
| `list_form_templates` | 評価フォームテンプレート一覧を取得 |
| `list_employees` | Talentio 利用メンバー一覧を取得（担当求人・所属グループ・権限を含む） |
| `list_employee_groups` | メンバーの所属グループ一覧を取得 |
| `list_workspaces` | ワークスペース（テナント）一覧を取得 |
| `list_deleted_candidates` | 削除済み候補者一覧を取得（候補者ID・削除日時のみ） |
| `list_candidate_comments` | 指定候補者への社内コメント一覧を取得 |
| `list_candidate_attachments` | 指定候補者の添付ファイル一覧を取得（ファイル名のみ、ダウンロードURLは含まれない） |

## API の制限・注意事項

- Talentio API には「応募(Application)」という独立したリソースは存在しない。候補者(candidate)が応募先の求人(requisition)を保持する形でデータが管理されているため、特定求人への応募者を見たい場合は `list_candidates` を `requisition_ids` で絞り込んで使う。
- 選考パイプラインのステージ定義を一覧取得する専用APIも存在しない。選考の進捗は `list_candidates` の `stage_statuses` で絞り込むか、`get_candidate` のレスポンスに含まれるステージ／評価情報を参照する。
- ページネーションは `page` 番号方式で1ページ100件固定（`limit`/`offset` は指定不可）。レスポンス本文は候補者・求人オブジェクトの配列のみで、総件数は本来 API レスポンスヘッダー `X-Total` に含まれるが、本コネクタは本文のみを返すため件数は分からない。返却件数が100件のときは次ページが存在する可能性が高い。
- レート制限は1時間あたり5,000リクエスト（ヘッダー `X-Remaining` / `X-Reset` で残数・リセットまでの秒数を確認可能）。
- すべてのツールは読み取り専用（GET）で、書き込み・副作用は発生しない。
- Talentio API には公式ドキュメント（`https://developers.talentio.com/`、OpenAPI形式）で以下の書き込み系エンドポイントの実在が確認できるが、実データを書き換える操作であり、かつ本コネクタは読み取り中心の方針のため未実装（見送り）とした:
  - `POST /candidates`（候補者追加）、`PATCH /candidates/{candidateId}`（候補者情報更新）
  - `POST /candidates/tags`（候補者タグ設定）
  - `POST /candidates/{candidateId}/stages`（候補者に選考追加）
  - `POST /candidates/{candidateId}/comments`（コメント追加。一覧取得の `list_candidate_comments` のみ実装）
  - `POST /candidates/{candidateId}/attachments`、`DELETE /candidates/{candidateId}/attachments/{id}`（添付ファイルの追加・削除。一覧取得の `list_candidate_attachments` のみ実装）
  - `PUT /candidates/{candidateId}/stages/{stageId}/evaluations/{evaluationId}`（評価の追加・更新）
  - `POST /requisitions`（求人追加）
- 求人の更新・削除に対応するAPIはTalentio自体に存在しない。

## 使用例

```
エンジニア採用の応募者を全員リストアップして
```

```
現在オープンな求人を教えて
```
