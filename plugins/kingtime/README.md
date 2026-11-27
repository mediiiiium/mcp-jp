# mcp-jp-kingtime

KING OF TIME（勤怠管理）を Claude から扱うためのプラグインです。KING OF TIME の従業員・勤怠・打刻・休暇を調べ、打刻を登録することができます。
中身は、[mcp-jp](https://github.com/mediiiiium/mcp-jp) の `kingtime` MCP サーバーの使い方をまとめたスキル（SKILL.md）です。MCP サーバー本体はプラグインに含まれていないので、下の「必要なもの」に沿って別に入れてください。

Look up KING OF TIME employees, daily and monthly attendance, time stamps and leave, and record time stamps. Recording a stamp is not idempotent, so the skill checks existing stamps before writing.

## 入れ方

Claude Code で次を実行します（2.1.275 以降）。

```
/plugin install mcp-jp-kingtime --marketplace mediiiiium/mcp-jp
```

## 必要なもの

`kingtime` の MCP サーバーを Claude Code に登録します。トークンなどの値の取り方は [スキル](./skills/kingtime/SKILL.md) の「準備」にあります。

```bash
pip install "git+https://github.com/mediiiiium/mcp-jp#subdirectory=kingtime"
claude mcp add kingtime -e KINGTIME_ACCESS_TOKEN=<値> -- kingtime-mcp
```

Docker で動かす場合は、イメージ `ghcr.io/mediiiiium/kingtime-mcp:0.1.0` も使えます。

## 注意

公式ドキュメントに沿って実装し、構造とエラー処理のテストは CI で通していますが、実際のアカウントでの動作確認はまだです。
mcp-jp は KING OF TIME の提供元とは関係のない個人の OSS です。

## ライセンス

MIT（[LICENSE](./LICENSE)）
