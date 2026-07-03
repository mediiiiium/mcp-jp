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
- `get_message_history` — メッセージ履歴取得（friend_id・期間・既読状態などで絞り込み可能）

### 共通情報
共通情報＝特定の友だちに紐づかず、アカウント全体で共有される固定値（例: 営業時間・定休日）。友だちごとに値が異なる「友だち情報」とは別物。

- `list_common_info_folders` — 共通情報フォルダ一覧取得
- `list_common_infos` — 共通情報一覧取得
- `update_common_info` — 共通情報更新

### テンプレート
- `list_templates` — 配信テンプレート一覧取得（folder_id で絞り込み可能）

### メディア
- `upload_media` — 画像ファイルを登録メディア一覧にアップロード（image のみ、jpg/png/gif・最大10MB）

## 既知の制約

Lステップ API は以下の削除エンドポイントを提供していないため、本コネクタにも削除ツールはありません（管理画面から手動で削除してください）。

- タグ・タグフォルダの削除
- 友だち情報・友だち情報フォルダの削除
- 共通情報・共通情報フォルダの削除・新規作成（値の更新のみ可能）
- テンプレートの作成・更新・削除（一覧取得のみ）
- メディアの一覧取得・削除（アップロードのみ）

また、以下は公式APIリファレンス（https://docs.lineml.jp/）を精査した結果、**実在が確認できなかった／リスクが高いため未実装**とした機能です。

- **友だち単体の詳細取得**（`GET /friends/{id}` 等）: ドキュメント上に該当エンドポイントは存在せず、`GET /friends` にも単体IDで絞り込むパラメータはない（friend_id 系の絞り込みは `friend_info_id`/`friend_info_value` など属性ベースのみ）。一覧取得の `list_friends` で代替する。
- **メッセージ送信・配信（シナリオ配信含む）**: `docs.lineml.jp` のトーク情報セクションは `GET /messages`（履歴取得）のみで、送信系エンドポイントは存在しない。Lステップ公式ブログでは「外部システムからの命令でメッセージ送信・シナリオ配信を起動できる」旨の記載があるが、これは管理画面側で個別設定する「連携アクション」の話であり、固定のメソッド／パス／パラメータを持つ汎用APIとしては確認できなかった。加えて、仮に存在しても本コネクタの方針（読み取り中心＋明示的な確認）に照らし、AIエージェントが実際の顧客へLINEメッセージを自動送信できてしまうリスクが大きいため、実体が確認できない現状ではツール化を見送る。

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
