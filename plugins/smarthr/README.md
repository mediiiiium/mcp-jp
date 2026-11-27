# mcp-jp-smarthr

SmartHR（人事・労務）を Claude から扱うためのプラグインです。SmartHR の従業員・部署・雇用形態・役職を調べ、従業員情報を部分更新することができます。
中身は、[mcp-jp](https://github.com/mediiiiium/mcp-jp) の `smarthr` MCP サーバーと、その使い方をまとめたスキル（SKILL.md）です。

Look up SmartHR employees, departments, employment types and job titles, and update employee records (department transfers, name, email). Read-only except one partial-update tool, which asks for confirmation before writing.

## 入れ方

Claude Code で次を実行します（2.1.275 以降）。

```
/plugin install mcp-jp-smarthr --marketplace mediiiiium/mcp-jp
```

## 必要なもの

- Docker（MCP サーバーは `ghcr.io/mediiiiium/smarthr-mcp:0.1.0` のイメージで動きます）
- 次の環境変数。Claude Code を起動する前に設定してください。値の取り方は [スキル](./skills/smarthr/SKILL.md) の「準備」にあります。

| 環境変数 |
|---|
| `SMARTHR_ACCESS_TOKEN` |
| `SMARTHR_TENANT_ID` |

## 注意

公式ドキュメントに沿って実装し、構造とエラー処理のテストは CI で通していますが、実際のアカウントでの動作確認はまだです。
mcp-jp は SmartHR の提供元とは関係のない個人の OSS です。

## ライセンス

MIT（[LICENSE](./LICENSE)）
