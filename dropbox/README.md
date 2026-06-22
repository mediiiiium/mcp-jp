# dropbox-mcp

Dropbox MCP サーバー。フォルダ・ファイルの管理・検索ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `DROPBOX_ACCESS_TOKEN` | ✅ | Dropbox アクセストークン |

## アクセストークン取得方法

1. [Dropbox App Console](https://www.dropbox.com/developers/apps) にアクセス
2. **Create app** → **Scoped access** → **Full Dropbox** を選択
3. アプリ名を入力して **Create app** をクリック
4. **Permissions** タブで必要な権限にチェック（files.content.read など）
5. **Settings** タブ → **OAuth 2** → **Generated access token** をクリック

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_folder` | フォルダの内容一覧を取得する |
| `get_metadata` | ファイル/フォルダのメタデータを取得する |
| `search` | ファイル・フォルダを検索する |
| `create_folder` | 新しいフォルダを作成する |
| `get_temporary_link` | ファイルの一時ダウンロードリンクを取得する |

## インストール

```bash
cd dropbox
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "dropbox": {
      "command": "dropbox-mcp",
      "env": {
        "DROPBOX_ACCESS_TOKEN": "your_dropbox_access_token"
      }
    }
  }
}
```
