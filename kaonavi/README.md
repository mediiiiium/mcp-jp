# kaonavi-mcp

カオナビ タレントマネジメントシステムの MCP サーバー。

## セットアップ

```bash
cd kaonavi
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `KAONAVI_CONSUMER_KEY` | カオナビ管理画面 → 公開API v2情報 → 認証情報 から取得 |
| `KAONAVI_CONSUMER_SECRET` | 同上 |

管理画面 → 設定 → 公開API v2情報 → 認証情報タブ でConsumer KeyとConsumer Secretを確認してください。

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "kaonavi": {
      "command": "kaonavi-mcp",
      "env": {
        "KAONAVI_CONSUMER_KEY": "your_consumer_key",
        "KAONAVI_CONSUMER_SECRET": "your_consumer_secret" 
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_members` | メンバー（従業員）一覧を取得 |
| `get_member` | 特定メンバーの詳細情報を取得（社員コード指定） |
| `list_departments` | 所属ツリー（部署階層）一覧を取得 |
| `list_layouts` | カスタムシートのレイアウト定義一覧を取得 |
| `get_sheet` | 特定シートのメンバーデータを取得（レイアウトID指定） |

## 使用例

```
全メンバーの一覧を見せて
```

```
営業部の部署IDを教えて
```

```
シートレイアウト一覧を確認して、スキルシートのデータを取得して
```
