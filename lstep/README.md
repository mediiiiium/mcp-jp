# lstep MCP

Lステップ（LINE公式アカウント向けMAツール）の MCP サーバー。

Claude等のAIエージェントからLステップを操作できます。

## 利用可能なツール

- `list_tags` — タグ一覧取得
- `list_friends` — 友だち一覧取得（タグ・情報付き）
- `list_friends_by_tag` — タグで友だちを絞り込み
- `bulk_add_tag` — 複数友だちに一括タグ付与
- `bulk_remove_tag` — 複数友だちから一括タグ削除
- `get_message_history` — メッセージ履歴取得
- `set_response_mark` — 対応マーク設定

## セットアップ

```bash
cd lstep
pip install -e .
```

環境変数に Lステップ API トークンを設定：

```bash
export LSTEP_API_TOKEN=your_token_here
```

## 前提

- Lステップ プロプランまたはAPI連携オプション（月額11,000円）が必要
- API ドキュメント: https://docs.lineml.jp/
