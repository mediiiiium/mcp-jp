# hubspot-mcp

HubSpot CRM（営業・マーケティング・CRM）の MCP サーバー。コンタクト・商談の管理を AI から操作できます。

## セットアップ

```bash
cd hubspot
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `HUBSPOT_ACCESS_TOKEN` | HubSpot プライベートアプリのアクセストークン |

### アクセストークンの取得

1. HubSpot にログイン
2. 右上のアイコン → 「アカウントとビリング」→「インテグレーション」→「プライベートアプリ」
3. 「プライベートアプリを作成する」でアプリを作成
4. スコープ: `crm.objects.contacts.read`, `crm.objects.contacts.write`, `crm.objects.deals.read`, `crm.objects.deals.write` を選択
5. 発行されたアクセストークンを環境変数に設定

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "hubspot": {
      "command": "hubspot-mcp",
      "env": {
        "HUBSPOT_ACCESS_TOKEN": "your_access_token_here"
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `search_contacts` | コンタクトを名前・メール・会社名で検索 |
| `get_contact` | コンタクトIDを指定して詳細情報を取得 |
| `create_contact` | 新しいコンタクトを作成 |
| `list_deals` | 商談（ディール）一覧を取得 |
| `create_deal` | 新しい商談を作成 |

## 使用例

```
田中さんという名前のコンタクトを検索して
```

```
株式会社〇〇のコンタクト一覧を教えて
```

```
コンタクトID 12345 の詳細を教えて
```

```
商談一覧を見せて
```

```
「株式会社ABC 基幹システム導入」という商談を100万円で作成して
```
