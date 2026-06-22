# activecampaign-mcp

ActiveCampaign MCP サーバー。コンタクト管理・メーリングリスト・キャンペーン管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `ACTIVECAMPAIGN_API_KEY` | ✅ | ActiveCampaign API キー |
| `ACTIVECAMPAIGN_BASE_URL` | ✅ | アカウント固有のベース URL（例: `https://myaccount.api-us1.com`） |

## API キー取得方法

1. ActiveCampaign にログイン
2. **Settings** → **Developer**
3. **API Access** セクションに URL と API Key が表示される

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_contacts` | コンタクト一覧を取得する |
| `get_contact` | コンタクトの詳細を取得する |
| `create_contact` | 新しいコンタクトを作成する |
| `list_lists` | メーリングリスト一覧を取得する |
| `list_campaigns` | キャンペーン一覧を取得する |

## インストール

```bash
cd activecampaign
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "activecampaign": {
      "command": "activecampaign-mcp",
      "env": {
        "ACTIVECAMPAIGN_API_KEY": "your_activecampaign_api_key",  # pragma: allowlist secret
        "ACTIVECAMPAIGN_BASE_URL": "https://myaccount.api-us1.com"
      }
    }
  }
}
```
