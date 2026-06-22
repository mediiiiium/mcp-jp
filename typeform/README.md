# typeform-mcp

Typeform MCP サーバー。フォーム・アンケートの管理・回答取得ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `TYPEFORM_ACCESS_TOKEN` | ✅ | Typeform Personal Access Token |

## トークン取得方法

1. Typeform にログイン
2. 右上のアバター → **Settings** → **Personal tokens**
3. **Generate a new token** をクリック
4. Token name を入力して **Generate token** をクリック

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_forms` | フォーム一覧を取得する |
| `get_form` | フォームの詳細を取得する |
| `get_responses` | フォームの回答一覧を取得する |
| `list_workspaces` | ワークスペース一覧を取得する |
| `get_response_summary` | 回答のサマリー統計を取得する |

## インストール

```bash
cd typeform
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "typeform": {
      "command": "typeform-mcp",
      "env": {
        "TYPEFORM_ACCESS_TOKEN": "your_typeform_access_token"
      }
    }
  }
}
```
