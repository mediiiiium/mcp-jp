# mcp-jp-smaregi

スマレジ（POS・店舗管理）を Claude から扱うためのプラグインです。スマレジの商品・取引・会員・店舗・在庫を調べることができます。
中身は、[mcp-jp](https://github.com/mediiiiium/mcp-jp) の `smaregi` MCP サーバーと、その使い方をまとめたスキル（SKILL.md）です。

Look up Smaregi POS products, transactions, customers, stores and stock levels through the Smaregi Platform API. Useful for sales checks, stock checks and store-level summaries.

## 入れ方

Claude Code で次を実行します（2.1.275 以降）。

```
/plugin install mcp-jp-smaregi --marketplace mediiiiium/mcp-jp
```

## 必要なもの

- Docker（MCP サーバーは `ghcr.io/mediiiiium/smaregi-mcp:0.1.0` のイメージで動きます）
- 次の環境変数。Claude Code を起動する前に設定してください。値の取り方は [スキル](./skills/smaregi/SKILL.md) の「準備」にあります。

| 環境変数 |
|---|
| `SMAREGI_ACCESS_TOKEN` |
| `SMAREGI_CONTRACT_ID` |

## 注意

公式ドキュメントに沿って実装し、構造とエラー処理のテストは CI で通していますが、実際のアカウントでの動作確認はまだです。
mcp-jp は スマレジ の提供元とは関係のない個人の OSS です。

## ライセンス

MIT（[LICENSE](./LICENSE)）
