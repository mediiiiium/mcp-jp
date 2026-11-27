# mcp-jp-smaregi

スマレジ（POS・店舗管理）を Claude から扱うためのプラグインです。スマレジの商品・取引・会員・店舗・在庫を調べることができます。
中身は、[mcp-jp](https://github.com/mediiiiium/mcp-jp) の `smaregi` MCP サーバーの使い方をまとめたスキル（SKILL.md）です。MCP サーバー本体はプラグインに含まれていないので、下の「必要なもの」に沿って別に入れてください。

Look up Smaregi POS products, transactions, customers, stores and stock levels through the Smaregi Platform API. Useful for sales checks, stock checks and store-level summaries.

## 入れ方

Claude Code で次を実行します（2.1.275 以降）。

```
/plugin install mcp-jp-smaregi --marketplace mediiiiium/mcp-jp
```

## 必要なもの

`smaregi` の MCP サーバーを Claude Code に登録します。トークンなどの値の取り方は [スキル](./skills/smaregi/SKILL.md) の「準備」にあります。

```bash
pip install "git+https://github.com/mediiiiium/mcp-jp#subdirectory=smaregi"
claude mcp add smaregi -e SMAREGI_ACCESS_TOKEN=<値> -e SMAREGI_CONTRACT_ID=<値> -- smaregi-mcp
```

Docker で動かす場合は、イメージ `ghcr.io/mediiiiium/smaregi-mcp:0.1.0` も使えます。

## 注意

公式ドキュメントに沿って実装し、構造とエラー処理のテストは CI で通していますが、実際のアカウントでの動作確認はまだです。
mcp-jp は スマレジ の提供元とは関係のない個人の OSS です。

## ライセンス

MIT（[LICENSE](./LICENSE)）
