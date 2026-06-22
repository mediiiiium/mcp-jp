# makeleaps-mcp

MakeLeaps（日本SMB向け請求書・見積書クラウドサービス）の MCP サーバー。公式 MCP チュートリアルはあるが公式サーバー未提供。

## セットアップ

```bash
cd makeleaps
pip install -e .
```

## 事前準備

MakeLeaps Developer Portal でアプリケーションを作成し、以下を取得：
- Client ID
- Client Secret
- Partner MID（ダッシュボードのURLまたはAPIルートから確認）

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
| `list_clients` | 取引先一覧を取得（名前で検索可） |
| `list_documents` | 書類一覧を取得（種別・検索で絞り込み可） |
| `get_document` | 書類の詳細情報を取得 |
| `create_document` | 請求書・見積書を作成 |
| `send_document` | 書類をメールで送付 |

## 使用例

```
今月の請求書一覧を見せて
```

```
株式会社ABCに「Webコンサルティング費用」で100万円の請求書を作成して
```

```
書類MID abc123 をsato@example.comに送付して
```
