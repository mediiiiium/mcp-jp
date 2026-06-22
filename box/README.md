# box-mcp

Box MCP サーバー。フォルダ・ファイルの管理・検索ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `BOX_ACCESS_TOKEN` | ✅ | Box アクセストークン（Developer Token または OAuth2 トークン） |

## アクセストークン取得方法

**開発・テスト用（Developer Token）:**
1. [Box Developer Console](https://app.box.com/developers/console) にアクセス
2. アプリを選択（または新規作成）
3. **Configuration** タブ → **Developer Token** セクション → **Generate Developer Token** をクリック
4. 有効期限は60分（本番環境では OAuth2 フローを使用してください）

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_folder` | フォルダの内容一覧を取得する |
| `get_folder` | フォルダの詳細情報を取得する |
| `get_file_info` | ファイルの詳細情報を取得する |
| `search` | ファイル・フォルダを検索する |
| `create_folder` | 新しいフォルダを作成する |

## インストール

```bash
cd box
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "box": {
      "command": "box-mcp",
      "env": {
        "BOX_ACCESS_TOKEN": "your_box_developer_token"
      }
    }
  }
}
```
