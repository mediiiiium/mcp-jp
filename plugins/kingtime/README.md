# mcp-jp-kingtime

KING OF TIME（勤怠管理）を Claude から扱うためのプラグインです。KING OF TIME の従業員・勤怠・打刻・休暇を調べ、打刻を登録することができます。
中身は、[mcp-jp](https://github.com/mediiiiium/mcp-jp) の `kingtime` MCP サーバーと、その使い方をまとめたスキル（SKILL.md）です。

Look up KING OF TIME employees, daily and monthly attendance, time stamps and leave, and record time stamps. Recording a stamp is not idempotent, so the skill checks existing stamps before writing.

## 入れ方

Claude Code で次を実行します（2.1.275 以降）。

```
/plugin install mcp-jp-kingtime --marketplace mediiiiium/mcp-jp
```

## 必要なもの

- Docker（MCP サーバーは `ghcr.io/mediiiiium/kingtime-mcp:0.1.0` のイメージで動きます）
- 次の環境変数。Claude Code を起動する前に設定してください。値の取り方は [スキル](./skills/kingtime/SKILL.md) の「準備」にあります。

| 環境変数 |
|---|
| `KINGTIME_ACCESS_TOKEN` |

## 注意

公式ドキュメントに沿って実装し、構造とエラー処理のテストは CI で通していますが、実際のアカウントでの動作確認はまだです。
mcp-jp は KING OF TIME の提供元とは関係のない個人の OSS です。

## ライセンス

MIT（[LICENSE](./LICENSE)）
