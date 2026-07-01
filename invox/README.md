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
| `export_journal` | 出力設定に従って費用計上仕訳／支払計上仕訳のデータをテキスト形式でエクスポート |

## 既知の制約

- **書き込み系操作の invox_company_code**: invox API は GET 系エンドポイントでは `invox_company_code` をクエリパラメータとして要求するが、POST/PUT/DELETE 系エンドポイントでは JSON ボディ側に含める必要がある。本コネクタの書き込み系ツール（`approve_received_invoice`、`export_journal`）はボディに `invox_company_code` を含めて送信する。
- **`list_received_invoices` に仕入先名・承認状態でのフィルタなし**: invox API の請求書一覧エンドポイントには仕入先名や個別の承認ステータス（承認待ち・差し戻し等）で絞り込むクエリパラメータが存在しない。必要な場合は `list_suppliers` で仕入先コードを調べて突き合わせるか、取得結果をクライアント側で絞り込むこと。
- **`fixed_only` の既定値**: `list_received_invoices` は `fixed_only` を省略すると true 扱いになり、データ化中・確認待ちなど未確定の請求書は結果に含まれない。下書き段階のものも見たい場合は明示的に `fixed_only=false` を指定する。
- **`approve_received_invoice` はべき等ではない**: 呼び出すたびに1ステップ分の承認が進む操作であり、既に承認済みの請求書に再度呼び出すとエラーになる。請求書の申請（apply）・差し戻し（reject）を行う API も invox 側には存在するが、本コネクタでは未実装。
- **`export_journal` は出力済みフラグを立てない**: エクスポート操作自体は請求書を「出力済み」に変更しない。別途 `invoice/set_exported` という invox 側の API を呼ぶ必要があるが、本コネクタでは未実装のため、同じ条件で繰り返しエクスポートすると同じデータが何度でも出力される。また会計ソフトの種類は API パラメータではなく invox 管理画面側の出力設定で決まる。
- **仕入先マスタは読み取り専用**: 仕入先の登録・更新・削除を行う API（`POST /invoice_receive/supplier`、`DELETE /invoice_receive/supplier/delete` 等）も invox 側には存在するが、本コネクタは読み取り専用のため未実装。

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
