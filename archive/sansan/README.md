# sansan-mcp

Sansan（名刺管理・人脈管理）の MCP サーバー。名刺情報・人物情報・タグ情報を AI から検索・取得できます。

## セットアップ

```bash
cd sansan
pip install -e .
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `SANSAN_API_KEY` | Sansan APIキー（管理画面の「API設定」から発行） |

### APIキーの取得

1. Sansan の管理者画面にログイン
2. 「設定」→「外部サービス連携」→「API設定」
3. APIキーを発行

## Claude Desktop 設定

```json
{
  "mcpServers": {
    "sansan": {
      "command": "sansan-mcp",
      "env": {
        "SANSAN_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `list_biz_cards` | 期間を指定して名刺一覧を取得 |
| `search_biz_cards` | 会社名・氏名・メール等で名刺を検索 |
| `get_biz_card` | 名刺IDを指定して詳細情報を取得 |
| `get_person` | 人物IDを指定して人物情報を取得（複数名刺の統合情報） |
| `list_tags` | タグ一覧を取得 |

## 使用例

```
今月交換した名刺の一覧を教えて
```

```
株式会社〇〇の連絡先を検索して
```

```
田中さんという名前の名刺を検索して
```

```
名刺ID abc123 の詳細を教えて
```

```
登録されているタグの一覧を見せて
```
