# mcp-jp-smarthr

SmartHR（人事・労務）を Claude から扱うためのプラグインです。SmartHR の従業員・部署・雇用形態・役職を調べ、従業員情報を部分更新することができます。
中身は、[mcp-jp](https://github.com/mediiiiium/mcp-jp) の `smarthr` MCP サーバーの使い方をまとめたスキル（SKILL.md）です。MCP サーバー本体はプラグインに含まれていないので、下の「必要なもの」に沿って別に入れてください。

Look up SmartHR employees, departments, employment types and job titles, and update employee records (department transfers, name, email). Read-only except one partial-update tool, which asks for confirmation before writing.

## 入れ方

Claude Code で次を実行します（2.1.275 以降）。

```
/plugin install mcp-jp-smarthr --marketplace mediiiiium/mcp-jp
```

## 必要なもの

`smarthr` の MCP サーバーを Claude Code に登録します。トークンなどの値の取り方は [スキル](./skills/smarthr/SKILL.md) の「準備」にあります。

```bash
pip install "git+https://github.com/mediiiiium/mcp-jp#subdirectory=smarthr"
claude mcp add smarthr -e SMARTHR_ACCESS_TOKEN=<値> -e SMARTHR_TENANT_ID=<値> -- smarthr-mcp
```

Docker で動かす場合は、イメージ `ghcr.io/mediiiiium/smarthr-mcp:0.1.0` も使えます。

## 注意

公式ドキュメントに沿って実装し、構造とエラー処理のテストは CI で通していますが、実際のアカウントでの動作確認はまだです。
mcp-jp は SmartHR の提供元とは関係のない個人の OSS です。

## ライセンス

MIT（[LICENSE](./LICENSE)）
