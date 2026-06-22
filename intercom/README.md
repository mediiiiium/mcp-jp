# intercom-mcp

Intercom MCP サーバー。コンタクト・カンバセーションの管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `INTERCOM_ACCESS_TOKEN` | ✅ | Intercom アクセストークン |

## トークン取得方法

1. Intercom 管理画面にログイン
2. **Settings** → **Integrations** → **Developer Hub**
3. アプリを選択（または新規作成）
4. **Authentication** → **Access Token** をコピー

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_contacts` | コンタクト一覧を取得する |
| `search_contacts` | メール・名前でコンタクトを検索する |
| `get_contact` | コンタクトの詳細を取得する |
| `create_contact` | 新しいコンタクトを作成する |
| `list_conversations` | カンバセーション（チャット）一覧を取得する |

## インストール

```bash
cd intercom
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "intercom": {
      "command": "intercom-mcp",
      "env": {
        "INTERCOM_ACCESS_TOKEN": "your_intercom_access_token"
      }
    }
  }
}
```
