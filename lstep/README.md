# lstep MCP

Lステップ（LINE公式アカウント向けMAツール）の MCP サーバー。

Claude等のAIエージェントからLステップを操作できます。

## 利用可能なツール

### 友だち
- `list_friends` — 友だち一覧取得（タグ・情報付き）
- `add_tag_to_friend` — 特定の友だち1人にタグ追加
- `remove_tag_from_friend` — 特定の友だち1人からタグ削除
- `set_response_mark` — 対応マーク設定

### 友だち情報
- `create_friend_info_folder` — 友だち情報フォルダ作成
- `create_friend_info` — 友だち情報（カスタム属性）作成

### タグ
- `list_tag_folders` — タグフォルダ一覧取得
- `create_tag_folder` — タグフォルダ作成
- `list_tags` — タグ一覧取得
- `create_tag` — タグ新規作成
- `update_tag` — タグ更新
- `list_friends_by_tag` — タグで友だちを絞り込み
- `bulk_add_tag` — 複数友だちに一括タグ付与
- `bulk_remove_tag` — 複数友だちから一括タグ削除

### 対応マーク
- `list_taiou_marks` — 対応マーク一覧取得

### メッセージ
- `get_message_history` — メッセージ履歴取得

### 共通情報
- `list_common_info_folders` — 共通情報フォルダ一覧取得
- `list_common_infos` — 共通情報一覧取得
- `update_common_info` — 共通情報更新

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
