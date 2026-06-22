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
| `list_documents` | 書類一覧を取得（タイトル・ステータスで絞り込み可） |
| `get_document` | 書類の詳細情報を取得 |
| `create_document` | 新しい書類を作成（テンプレートからも可） |
| `set_participants` | 書類の署名者（参加者）情報を設定 |
| `send_document` | 書類を署名依頼として送信 |

## 使用例

```
未完了の契約書を一覧で見せて
```

```
新しい業務委託契約書を作成して、田中太郎（tanaka@example.com）に署名依頼を送って
```
