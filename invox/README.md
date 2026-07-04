# invox-mcp

invox（受取請求書・発行請求書・経費精算）の MCP サーバー。受取請求書の一覧取得・承認・仕訳エクスポートを AI から操作できます。

## セットアップ

```bash
cd invox
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `INVOX_ACCESS_TOKEN` | OAuth2 フローで取得したアクセストークン（有効期限10時間） |
| `INVOX_COMPANY_CODE` | invox 会社コード（管理画面 URL に含まれる識別子） |

### アクセストークンの取得

invox は OAuth2 認証（認可コードフロー）を採用しています。Professional プランでクライアント ID とクライアントシークレットを取得後、以下の手順でアクセストークンを発行してください。

1. `https://api.invox.jp/oauth2/authorize/` にブラウザでアクセス
2. 認可コードを取得
3. `https://api.invox.jp/oauth2/token/` に POST してアクセストークンを取得

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "invox": {
      "command": "invox-mcp",
      "env": {
        "INVOX_ACCESS_TOKEN": "your_access_token_here",
        "INVOX_COMPANY_CODE": "your_company_code"
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_received_invoices` | 受取請求書の一覧を取得（請求日・計上日・部門・確定状態などで絞り込み可。仕入先名や承認状態での絞り込みは API 側に存在しない） |
| `get_received_invoice` | 受取請求書1件の詳細情報を取得（include_journal_info=true で仕訳情報も取得可） |
| `approve_received_invoice` | ワークフロー申請済みの受取請求書を1件承認する（承認タスク名 approve_task_name が必須） |
| `list_suppliers` | 仕入先一覧を取得（コード・名称・登録番号・登録日で絞り込み、並び順指定可） |
| `get_supplier` | 仕入先コードを指定して仕入先1件の詳細（支払方法・課税区分・登録番号・拡張項目など）を取得 |
| `list_supplier_trade_conditions` | 仕入先コードに紐づく取引設定（部門・プロジェクトごとの支払方法設定）の一覧を取得 |
| `list_upload_settings` | invox 管理画面のアップロード設定（データ化方法・区切り方・アップロード用メール等）の一覧を取得 |
| `get_invoice_download_url` | 受取請求書1件の画像・PDFファイルのダウンロード用一時URL（有効期限1分）を取得 |
| `get_invoices_zip_download_url` | 複数の受取請求書ファイルをまとめた zip のダウンロード用URLを取得（最大100件） |
| `confirm_invoice_message` | 受取請求書のワークフローメッセージを1件、確認済みにする |
| `export_journal` | 出力設定に従って費用計上仕訳／支払計上仕訳のデータをテキスト形式でエクスポート |

## 既知の制約

- **書き込み系操作の invox_company_code**: invox API は GET 系エンドポイントでは `invox_company_code` をクエリパラメータとして要求するが、POST/PUT/DELETE 系エンドポイントでは JSON ボディ側に含める必要がある。本コネクタの書き込み系ツール（`approve_received_invoice`、`confirm_invoice_message`、`export_journal`）はボディに `invox_company_code` を含めて送信する。
- **`list_received_invoices` に仕入先名・承認状態でのフィルタなし**: invox API の請求書一覧エンドポイントには仕入先名や個別の承認ステータス（承認待ち・差し戻し等）で絞り込むクエリパラメータが存在しない。必要な場合は `list_suppliers` で仕入先コードを調べて突き合わせるか、取得結果をクライアント側で絞り込むこと。
- **`fixed_only` の既定値**: `list_received_invoices` は `fixed_only` を省略すると true 扱いになり、データ化中・確認待ちなど未確定の請求書は結果に含まれない。下書き段階のものも見たい場合は明示的に `fixed_only=false` を指定する。
- **`approve_received_invoice` はべき等ではない**: 呼び出すたびに1ステップ分の承認が進む操作であり、既に承認済みの請求書に再度呼び出すとエラーになる。請求書の申請（`invoice/apply`）・差し戻し（`invoice/reject`）、確定（`invoice/fix`）・確定取消（`invoice/unfix`）を行う API も invox 側には存在するが、いずれもワークフローの承認ルートや会計確定状態を変更する影響範囲の大きい操作であり、本コネクタでは慎重を期して未実装（読み取り中心の方針、需要が明確になれば個別に再検討）。
- **`confirm_invoice_message` は取り消せない**: メッセージを確認済みにする操作自体は請求書データを変更しないが、確認済みフラグを未確認に戻す API は存在しないため元に戻せない。対象のメッセージ・請求書は `get_received_invoice` のレスポンス（`messages[].message_id`、`confirmed`）で確認できる。
- **`export_journal` は出力済みフラグを立てない**: エクスポート操作自体は請求書を「出力済み」に変更しない。別途 `invoice/set_exported` という invox 側の API を呼ぶ必要があるが、出力済みへの変更は「出力待ち」ステータスの請求書にのみ有効かつ支払計上仕訳の生成有無にも影響する不可逆操作のため、本コネクタでは未実装（同じ条件で繰り返しエクスポートすると同じデータが何度でも出力される点に注意）。また会計ソフトの種類は API パラメータではなく invox 管理画面側の出力設定で決まる。
- **仕入先マスタは読み取り専用**: 仕入先の登録・更新（`POST /invoice_receive/supplier`）、削除（`DELETE /invoice_receive/supplier/delete`）、支払設定・取引設定の登録・更新・削除を行う API も invox 側には存在するが、本コネクタは読み取り専用のため未実装。
- **ファイルの直接ダウンロードは未実装**: 請求書ファイル本体・添付ファイルを直接取得する API（`GET /invoice_receive/invoice/download`、`GET /invoice_receive/invoice/attached_file/download`）はバイナリ（application/octet-stream）を返すため、テキストベースのレスポンス設計の本コネクタとは相性が悪く未実装。代わりに一時ダウンロードURLを返す `get_invoice_download_url` / `get_invoices_zip_download_url` を実装している（取得したURLへのアクセスは本コネクタの外部で行う）。
- **発行請求書（invoice_issue）・経費精算（expense）・電子帳簿保存（e_storage）は未対応**: invox API にはこれら3ドメインについて請求書登録・PDFアップロード・添付ファイル登録・書類登録・スタッフ/部門/プロジェクトマスタの追加・更新・削除エンドポイントが存在するが、いずれも書き込み系が中心で、発行請求書自体の一覧・詳細取得（GET）APIも存在しない（唯一のGETは登録済み請求書のファイルURL取得 `GET /invoice_issue/issue_invoice/download_url/get` のみで、一覧を辿る手段が無いため単独では実用的なツールにならない）。読み取り専用方針の本コネクタでは対象外とした。
- **マスタ管理系（部門・プロジェクト・勘定科目・補助勘定科目・汎用マスタ・スタッフ）は未対応**: `invoice_receive/department`・`project`・`account`・`sub_account`・`master`・`staff` 等の追加・更新・削除APIも存在するが、いずれも書き込み系のみでGET一覧APIが提供されていないため未実装。

## 使用例

```
今月受け取った請求書を一覧表示して（下書き段階のものも含めて）
```

```
請求書ID xxx の詳細を仕訳情報も含めて見せて
```

```
請求書ID xxx を「経理承認」タスクとして承認して
```

```
今月分の費用計上仕訳をエクスポートして
```
