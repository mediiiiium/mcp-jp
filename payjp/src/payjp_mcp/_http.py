"""mcp-jp コネクタ共通の HTTP / レスポンス整形ヘルパー。

各コネクタは独立した pip パッケージのため、このファイルは依存を増やさず
自己完結する形で各パッケージに同梱（vendoring）している。
内容はリポジトリ全体で同一。更新時は全コネクタへ反映すること。
"""
import json

import httpx
from mcp import types

# LLM のコンテキストを溢れさせないためのレスポンス上限（文字数）
MAX_CHARS = 20000


def format_response(data, *, max_chars: int = MAX_CHARS) -> list[types.TextContent]:
    """API レスポンス(JSON化可能なオブジェクト)を TextContent に整形する。

    大きすぎる場合は切り詰め、絞り込みを促すメッセージを付与する。
    """
    text = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    if len(text) > max_chars:
        text = (
            text[:max_chars]
            + f"\n\n... (出力を省略しました。全 {len(text)} 文字。"
            "limit やフィルタ条件で絞り込んでください)"
        )
    return [types.TextContent(type="text", text=text)]


def error_response(exc: Exception) -> list[types.TextContent]:
    """例外を、LLM とユーザーにとって意味のあるエラーメッセージへ変換する。

    httpx の生スタックトレースを返さず、原因と対処のヒントを示す。
    """
    if isinstance(exc, httpx.HTTPStatusError):
        code = exc.response.status_code
        hint = {
            400: "リクエストが不正です。パラメータを確認してください。",
            401: "認証に失敗しました。API キー / トークンの環境変数を確認してください。",
            403: "権限がありません。トークンのスコープ・プラン・IP 制限を確認してください。",
            404: "リソースが見つかりません。指定した ID を確認してください。",
            422: "入力値が不正です。必須項目や形式を確認してください。",
            429: "レート制限に達しました。時間をおいて再試行してください。",
        }.get(code, f"API がエラーを返しました (HTTP {code})。")
        body = (exc.response.text or "").strip()[:500]
        msg = f"{hint}\n\nHTTP {code}\n{body}" if body else f"{hint}\n\nHTTP {code}"
    elif isinstance(exc, httpx.TimeoutException):
        msg = "API への通信がタイムアウトしました。時間をおいて再試行してください。"
    elif isinstance(exc, httpx.RequestError):
        msg = f"API への通信に失敗しました: {exc}"
    elif isinstance(exc, (ValueError, KeyError)):
        # 環境変数未設定・必須引数欠落など
        msg = str(exc) or f"入力エラー: {type(exc).__name__}"
    else:
        msg = f"予期しないエラー: {type(exc).__name__}: {exc}"
    return [types.TextContent(type="text", text=f"⚠️ {msg}")]
