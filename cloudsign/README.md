# cloudsign-mcp

クラウドサイン（国内シェアNo.1の電子契約サービス）の MCP サーバー。公式 MCP 未提供。

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
| `list_documents` | 書類一覧を取得（タイトル・ステータスで絞り込み、offset/limit でページング、最大100件/回） |
| `get_document` | 書類1件の詳細（ステータス・参加者・日時等）を取得 |
| `create_document` | 新しい書類を下書き状態で作成（テンプレートからも可）。呼ぶたびに新規作成されるためべき等ではない |
| `set_participants` | 書類の署名者（参加者）を設定。配列順＝送信順で、送信後は変更不可 |
| `send_document` | 下書きの書類を署名依頼として送信（不可逆・べき等ではない） |

## 既知の制約

CloudSign Web API には以下のエンドポイントが提供されていないため、本コネクタにも対応するツールはありません（管理画面から手動で操作してください）。

- **書類の削除**: 削除エンドポイントは存在しない（誤って作成した書類は管理画面で削除・無効化する）
- **送信の取り消し（キャンセル）**: 送信済み書類を取り消す・却下するAPIはない
- **書類の更新**: `PUT /documents/{id}` は下書き状態のときのみ有効（タイトル・メッセージの変更）で、送信後は使えない
- **参加者の並び替え**: 署名依頼の送信順は参加者配列の順序で決まり、送信後は変更できない

また、書類ステータス（`status` パラメータ）の正確な値の一覧は CloudSign 公式ヘルプに一覧表として明記されておらず、確認できているのは 1=先方確認中, 2=締結完了, 3=取消または却下, 13=インポート書類 のみです。正確な仕様は CloudSign Web API 仕様書（SwaggerHub: `CloudSign/cloudsign-web_api`）を参照してください。

## 使用例

```
未完了の契約書を一覧で見せて
```

```
新しい業務委託契約書を作成して、田中太郎（tanaka@example.com）に署名依頼を送って
```
