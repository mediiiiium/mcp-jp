# talentio MCP server — Glama introspection check 用 Dockerfile
#
# Glama のチェックは「起動して introspection (tools/list) に応答」できればよい。
# list_tools() は TALENTIO_ACCESS_TOKEN 未設定でも 5 ツールを返すため、環境変数無しでも通る。
# 実運用でツールを呼ぶ際は TALENTIO_ACCESS_TOKEN を環境変数で渡すこと。
#
# ビルド: docker build -t talentio-mcp .（このディレクトリで実行）
# 実行:   docker run -i --rm -e TALENTIO_ACCESS_TOKEN=xxx talentio-mcp

FROM python:3.12-slim

WORKDIR /app

# パッケージ定義とソースをコピーして install（エントリポイント talentio-mcp を生成）
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

# root 権限での実行を避ける
RUN useradd --no-create-home --shell /usr/sbin/nologin mcp
USER mcp

# MCP は stdio 経由で通信する
ENTRYPOINT ["talentio-mcp"]
