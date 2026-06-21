# mazrica-mcp

Mazrica Sales（Senses）SFA の MCP サーバー。取引先・案件・ユーザーを AI から操作できます。

## セットアップ

```bash
cd mazrica
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `MAZRICA_API_KEY` | Mazrica 管理画面 → 設定 → API設定 から発行 |

API キーの発行には growth プラン以上の契約が必要です。

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "mazrica": {
      "command": "mazrica-mcp",
      "env": {
        "MAZRICA_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_customers` | 取引先一覧を取得（名前で絞り込み可） |
| `create_customer` | 新規取引先を登録 |
| `list_deals` | 案件（商談）一覧を取得（取引先・名前で絞り込み可） |
| `create_deal` | 新規案件を登録 |
| `list_users` | 営業担当者（ユーザー）一覧を取得 |

## 使用例

```
今月クローズ予定の案件を全部リストアップして
```

```
株式会社サンプルを新規取引先として登録して
```

```
田中さんが担当している案件を見せて
```
