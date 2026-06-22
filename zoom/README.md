# zoom-mcp

Zoom MCP サーバー。ミーティング・レコーディング・ユーザー管理ができます。

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `ZOOM_ACCOUNT_ID` | ✅ | Zoom アカウントID |
| `ZOOM_CLIENT_ID` | ✅ | Server-to-Server OAuth アプリのクライアントID |
| `ZOOM_CLIENT_SECRET` | ✅ | Server-to-Server OAuth アプリのクライアントシークレット |

## 認証情報取得方法（Server-to-Server OAuth）

1. [Zoom App Marketplace](https://marketplace.zoom.us/) にアクセス
2. **Develop** → **Build App** → **Server-to-Server OAuth** を選択
3. アプリ名を入力して **Create** をクリック
4. **App Credentials** に表示される Account ID、Client ID、Client Secret をコピー
5. **Scopes** タブで必要なスコープを追加（meeting:read、recording:read など）

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_meetings` | ミーティング一覧を取得する |
| `get_meeting` | ミーティングの詳細を取得する |
| `create_meeting` | 新しいミーティングを作成する |
| `list_recordings` | クラウドレコーディング一覧を取得する |
| `list_users` | アカウント内のユーザー一覧を取得する |

## インストール

```bash
cd zoom
pip install -e .
```

## Claude Desktop 設定例

```json
{
  "mcpServers": {
    "zoom": {
      "command": "zoom-mcp",
      "env": {
        "ZOOM_ACCOUNT_ID": "your_zoom_account_id",
        "ZOOM_CLIENT_ID": "your_zoom_client_id",
        "ZOOM_CLIENT_SECRET": "your_zoom_client_secret"  # pragma: allowlist secret
      }
    }
  }
}
```
