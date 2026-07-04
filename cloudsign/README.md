# cloudsign-mcp

クラウドサイン（国内シェアNo.1の電子契約サービス）の MCP サーバー。公式 MCP 未提供。

- API ドキュメント: https://app.swaggerhub.com/apis/CloudSign/cloudsign-web_api

## セットアップ

```bash
cd cloudsign
pip install -e .
```

## 前提条件

クラウドサインの **Corporateプラン以上** が必要です。  
API クライアントIDは管理画面 → 外部サービス連携 → Web API から取得してください。

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `CLOUDSIGN_CLIENT_ID` | クラウドサイン Web API のクライアントID |  # pragma: allowlist secret

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "cloudsign": {
      "command": "cloudsign-mcp",
      "env": {
        "CLOUDSIGN_CLIENT_ID": "your_client_id_here"
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_documents` | 書類一覧を取得（ステータスで絞り込み、page でページング、最大100件/ページ） |
| `get_document` | 書類1件の詳細（ステータス・参加者・日時等）を取得 |
| `create_document` | 新しい書類を下書き状態で作成（テンプレートからも可）。呼ぶたびに新規作成されるためべき等ではない |
| `set_participants` | 書類に署名者（宛先）を1件ずつ追加する。呼び出すたびに追加されるため、既存宛先の上書きにはならない |
| `send_document` | 下書きの書類を署名依頼として送信、または先方確認中の書類にリマインドを送る（不可逆・べき等ではない） |
| `get_document_alert` | 書類のアラート情報（リマインド日・有効/無効・メモ）を取得 |
| `get_document_attribute` | 書類の管理用属性情報（契約相手・契約日・金額・管理番号など）を取得 |
| `get_me` | 自分自身のユーザー情報（所属チーム・権限）を取得（複数部署管理機能利用時は不可） |
| `list_team_documents` | チーム内メンバー全員がやり取りした書類一覧を取得（管理者権限が必要） |
| `list_cabinets` | キャビネット（書類フォルダ）一覧を取得 |
| `list_cabinet_documents` | 指定キャビネット内の書類一覧を取得（エンタープライズプラン限定） |

## 既知の制約

2026-07-05 の深掘りで CloudSign Web API 仕様書（SwaggerHub: `CloudSign/cloudsign-web_api`、OpenAPI 3.0形式、公開レジストリ `api.swaggerhub.com` から取得）を精査した結果、以前のバージョンの本 README・実装には以下の誤りがあったため、あわせて修正した:

- **`list_documents` のパラメータ誤り**: 旧実装は `title`（部分一致検索）・`offset`/`limit` を送っていたが、仕様書上 `GET /documents` にこれらのパラメータは存在しない（正しくは `page` によるページング、`status` による絞り込みのみ）。`title` はサーバー側で無視されていた可能性が高い。
- **書き込み系のリクエスト形式の誤り**: `create_document`（`POST /documents`）・`set_participants`（宛先追加）は仕様書上 `application/x-www-form-urlencoded` のみを受け付けるが、旧実装は JSON（`Content-Type: application/json` かつ JSON ボディ）で送信していた。動作していなかった可能性がある。
- **`send_document` のエンドポイント誤り**: 送信は `POST /documents/{documentID}`（ボディなし）が正しい。旧実装は `PUT /documents/{documentID}` に `{"status": 1}` という、仕様書に存在しないフィールドを送っていた（`PUT` は下書き状態でのタイトル・メッセージ更新用で、`status` という更新可能フィールドは無い）。
- **`set_participants` のロジック誤り**: 旧実装は「配列インデックス（1始まり）を宛先IDとみなして `PUT /documents/{documentID}/participants/{participantID}` で上書きする」実装だったが、仕様書上 `participantID` は宛先ごとに割り当てられる文字列ID（32〜36文字）であり、連番の整数ではない。宛先を新規に追加する正しい方法は `POST /documents/{documentID}/participants` であるため、そちらに変更した。
- **書類ステータス `status` の誤り**: 旧 README は「13=インポート書類」を `GET /documents` の `status` パラメータの有効値として案内していたが、仕様書上このパラメータの `enum` は `-1, 0, 1, 2, 3, 4` のみ（`13` は含まれない）。`13` は `documentModel.status`（書類データ自体が持つ値）の説明文には登場するが、一覧取得時の絞り込み値としては使えないと考えられる。

CloudSign Web API には以下のエンドポイントも実在するが、本コネクタには実装されていない:

- **下書き書類の削除**（`DELETE /documents/{documentID}`、下書き状態限定）: 存在は仕様書で確認できるが、削除は不可逆な書き込み操作であり、本コネクタは読み取り中心の方針のため見送った。誤って作成した書類は管理画面から削除・無効化してください。
- **送信の取り消し（キャンセル）**: 送信済み書類を取り消す・却下する API は存在しない。
- **参加者の更新・削除**（`PUT`/`DELETE /documents/{documentID}/participants/{participantID}`）、**入力欄・添付ファイル・共有先（reportees）の作成/更新/削除**: いずれも書き込み系で、実データ（契約書の内容や送信対象）を変更する操作のため見送った。
- **ファイル・証明書のダウンロード**（`GET /documents/{documentID}/files/{fileID}`、`GET /documents/{documentID}/certificate`、添付ファイルのダウンロード）: バイナリデータを返すエンドポイントで、本コネクタのテキストベースのレスポンス形式に合わないため見送った。
- **インポート書類の作成**（`POST /imported_documents`）: 締結済み契約書を CloudSign にアップロードする書き込み系機能のため見送った。

正確な最新仕様は CloudSign Web API 仕様書（`https://app.swaggerhub.com/apis/CloudSign/cloudsign-web_api`）を参照してください。

## 使用例

```
未完了の契約書を一覧で見せて
```

```
新しい業務委託契約書を作成して、田中太郎（tanaka@example.com）に署名依頼を送って
```
