---
name: cloudsign
description: クラウドサイン（電子契約）の書類一覧・詳細・管理用属性・アラートを調べ、下書きの作成・宛先の追加・署名依頼の送信を、mcp-jp の cloudsign MCP サーバーで行う。「未完了の契約書を一覧にして」「この契約の終了日と金額は」「業務委託契約書を作って田中さんに署名依頼を送って」のように、クラウドサインの書類を扱う依頼で使う。
---

# クラウドサイン（mcp-jp / cloudsign）

クラウドサイン Web API の書類を、MCP サーバー `cloudsign-mcp` 経由で読み書きする。
書き込みは下書きの作成（`create_document`）・宛先の追加（`set_participants`）・送信（`send_document`）の3つ。

> 動作確認の状況: 公式の API 仕様書に沿って実装し、構造とエラー処理のテストは CI で通しているが、実際のクラウドサインアカウントではまだ動かしていない（README の「動作確認」列を参照）。

## 準備

1. クラウドサインの **Corporate プラン以上**が必要
2. 管理画面 → 外部サービス連携 → Web API で、クライアントIDを取得する
3. インストールして登録する

```bash
pip install "git+https://github.com/mediiiiium/mcp-jp#subdirectory=cloudsign"
claude mcp add cloudsign -e CLOUDSIGN_CLIENT_ID=<クライアントID> -- cloudsign-mcp
```

Claude Desktop の場合は `claude_desktop_config.json` の `mcpServers` に `"command": "cloudsign-mcp"` と環境変数を書く。

| 環境変数 | 内容 |
|---|---|
| `CLOUDSIGN_CLIENT_ID` | クラウドサイン Web API のクライアントID |

## 調べるとき

- **書類を探す**: `list_documents` を `status` で絞り、`page` で送る（最大100件/ページ）。タイトルでの検索パラメータは API にない。一覧を取ってから絞り込む。
- **チーム全体の書類**: `list_team_documents`（管理者権限が必要）。フォルダ単位なら `list_cabinets` → `list_cabinet_documents`（エンタープライズプラン限定）。
- **契約の中身**: ステータス・参加者・日時は `get_document`。契約相手・締結日・開始日・終了日・解約通知期限・自動更新・金額・管理番号は `get_document_attribute`。更新・満了のリマインド設定は `get_document_alert`。
- **自分の権限の確認**: `get_me`（複数部署管理機能を使っていると使えない）。

## 契約書を送るとき

順番は **`create_document`（下書き）→ `set_participants`（`participants` に渡した宛先を順に追加）→ `send_document`（送信）**。

- `create_document` は呼ぶたびに新しい下書きができる（べき等ではない）。失敗したように見えても、呼び直す前に `list_documents` で下書きができていないか確かめる。
- `set_participants` は呼ぶたびに宛先が**追加**される。既存の宛先の上書きにはならない。二重に追加しないよう、`get_document` で現在の宛先を確かめてから呼ぶ。
- **`send_document` は取り消せない**。相手にメールが届き、送信の取り消し API はない。タイトル・宛先（氏名とメールアドレス）を利用者に見せて、送ってよいか明示的に確認を取ってから1回だけ呼ぶ。先方確認中の書類に呼ぶとリマインドが送られる。

## できないこと

下書きの削除、宛先の更新・削除、入力欄・添付・共有先の編集、ファイルや合意締結証明書のダウンロード、締結済み書類のインポート。誤って作った下書きは管理画面から削除するよう案内する。

## ツール

`list_documents` `get_document` `get_document_attribute` `get_document_alert` `create_document` `set_participants` `send_document` `get_me` `list_team_documents` `list_cabinets` `list_cabinet_documents`

詳しい引数は [cloudsign/README.md](https://github.com/mediiiiium/mcp-jp/blob/main/cloudsign/README.md) を参照。
