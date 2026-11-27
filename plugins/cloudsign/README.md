# mcp-jp-cloudsign

クラウドサイン（電子契約）を Claude から扱うためのプラグインです。クラウドサインの書類・契約情報を調べ、契約書を作成・送信することができます。
中身は、[mcp-jp](https://github.com/mediiiiium/mcp-jp) の `cloudsign` MCP サーバーと、その使い方をまとめたスキル（SKILL.md）です。

Look up CloudSign documents and contract attributes, and create, address and send contracts for e-signature. Sending cannot be undone, so the skill shows the title and recipients and asks for explicit confirmation first.

## 入れ方

Claude Code で次を実行します（2.1.275 以降）。

```
/plugin install mcp-jp-cloudsign --marketplace mediiiiium/mcp-jp
```

## 必要なもの

- Docker（MCP サーバーは `ghcr.io/mediiiiium/cloudsign-mcp:0.1.0` のイメージで動きます）
- 次の環境変数。Claude Code を起動する前に設定してください。値の取り方は [スキル](./skills/cloudsign/SKILL.md) の「準備」にあります。

| 環境変数 |
|---|
| `CLOUDSIGN_CLIENT_ID` |

## 注意

公式ドキュメントに沿って実装し、構造とエラー処理のテストは CI で通していますが、実際のアカウントでの動作確認はまだです。
mcp-jp は クラウドサイン の提供元とは関係のない個人の OSS です。

## ライセンス

MIT（[LICENSE](./LICENSE)）
