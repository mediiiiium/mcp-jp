# makeleaps-mcp

MakeLeaps（日本SMB向け請求書・見積書クラウドサービス）の MCP サーバー。公式 MCP チュートリアルはあるが公式サーバー未提供。

## セットアップ

```bash
cd makeleaps
pip install -e .
```

## 事前準備

MakeLeaps 管理画面の **API ユーザー画面**
（<https://app.makeleaps.com/integrations/makeleaps/api-users/>）で「Add API Key」を押し、以下を取得：
- Client ID
- Client Secret（作成後に「Show API Secret」で表示）
- Partner MID（ダッシュボードのURLまたはAPIルートから確認）

**API は無料プランでは使えない**（料金ページの機能比較「MakeLeaps Rest API」は
無料プラン × / 個人プラン ○ / 法人プラン ○ / エンタープライズ ○。2026-07-30 時点）。
発行に審査・申請は不要（公式チュートリアルに記載なし＝管理画面で完結）。
"Developer Portal" は**ドキュメントのサイト**でキーの発行場所ではない（ここを間違えていた）。

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `MAKELEAPS_CLIENT_ID` | アプリケーションの Client ID |
| `MAKELEAPS_CLIENT_SECRET` | アプリケーションの Client Secret |  # pragma: allowlist secret
| `MAKELEAPS_PARTNER_MID` | 自社のパートナー MID |

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "makeleaps": {
      "command": "makeleaps-mcp",
      "env": {
        "MAKELEAPS_CLIENT_ID": "your_client_id",
        "MAKELEAPS_CLIENT_SECRET": "your_client_secret",  # pragma: allowlist secret
        "MAKELEAPS_PARTNER_MID": "your_partner_mid"
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_clients` | 取引先一覧を取得（名前検索・アーカイブ状態・バーチャル口座有無で絞り込み可） |
| `list_documents` | 書類一覧を取得（種別・取引先・期間・タグ・送付/入金等のステータスで絞り込み可） |
| `get_document` | 書類の詳細情報を取得（expand でクライアント等のフィールドを展開可能） |
| `list_document_templates` | 書類種別ごとに使用可能な書類テンプレートコード一覧を取得 |
| `create_document` | 請求書・見積書等を作成（テンプレート・取引先担当者の指定が必須） |
| `send_document` | 書類をメール（Secure Send）で送付 |

## 制限事項・注意点

- MakeLeaps API の公式ドキュメント（`https://app.makeleaps.com/api/docs/`。機械可読版は
  `https://app.makeleaps.com/api/llms.txt`）に基づき実装しているが、ページネーションの
  パラメータ名（`page` 等）や既定の並び順は公式ドキュメントに明記されていないため未検証。
- レスポンスは `{"meta": {"status": ...}, "response": ...}` で包まれる。本コネクタは**それをそのまま返す**
  （パースしないので envelope の変更に影響されない）。取り出しはモデル側の仕事になる点に注意。
- レート上限は **120リクエスト/分・5000リクエスト/日**（公式記載）。リトライ実装は無いので、
  429 が返ったらそのままエラーになる。
- OAuth のトークンは **`scope: "read write"` 固定**で、読み取り専用のスコープは存在しない。
  「読み取りしかしない」はコネクタが GET だけを叩くという意味で、権限としての保証ではない
  （書き込み系ツール `create_document` / `send_document` は本コネクタに実装されているので、なおさら明示が必要）。
- `create_document` は `document_template` と `client_contact_mid`（取引先担当者のMID）が必須。有効なテンプレートコードは
  `list_document_templates` で事前に確認する。
- `send_document` は Secure Send（メール送付）のみ対応。Client Inbox 送付・郵送・Peppol送付、複数宛先指定には対応していない。
  送付オーダーはサーバー側で非同期バリデーションされるため、作成直後は送付がエラーになる場合がある。
- 取引先・書類の更新（PUT/PATCH）・削除（DELETE）エンドポイントは MakeLeaps API 自体には存在するが、本コネクタには
  実装されていない。必要な場合は MakeLeaps 管理画面や API を直接使用する。

## 使用例

```
今月の請求書一覧を見せて
```

```
invoice用のテンプレート一覧を見せて
```

```
株式会社ABCの担当者contact_mid xyz789 宛に「Webコンサルティング費用」で100万円の請求書を作成して
```

```
書類MID abc123 をsato@example.comに送付して
```
