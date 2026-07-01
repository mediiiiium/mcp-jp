# lstep MCP server — Glama introspection check 用 Dockerfile
#
# Glama のチェックは「起動して introspection (tools/list) に応答」できればよい。
# list_tools() はトークン無しで 19 ツールを返すため、LSTEP_API_TOKEN 未設定でも通る。
# 実運用でツールを呼ぶ際は LSTEP_API_TOKEN を環境変数で渡すこと。
#
# ビルド: docker build -t lstep-mcp .（このディレクトリで実行）
# 実行:   docker run -i --rm -e LSTEP_API_TOKEN=xxx lstep-mcp

FROM python:3.12-slim

WORKDIR /app

# パッケージ定義とソースをコピーして install（エントリポイント lstep-mcp を生成）
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

# root 権限での実行を避ける
RUN useradd --no-create-home --shell /usr/sbin/nologin mcp
USER mcp

# MCP は stdio 経由で通信する
ENTRYPOINT ["lstep-mcp"]
