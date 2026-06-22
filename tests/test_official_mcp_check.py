"""公式MCP巡回チェック（tools/check_official_mcp.py）の回帰テスト。

ネットワーク不要のオフライン点検（鮮度・重複ゲート）が常にグリーンであることを
CI で保証する。稼働コネクタが公式MCP提供済みサービスと重複すると exit 1 になり、
ここで失敗する＝archive/ への退避漏れに気づける。
"""
import subprocess
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools" / "check_official_mcp.py"


def test_offline_check_passes():
    """オフライン点検（--check-urls なし）は重複なしで exit 0 を返す。"""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"重複検出ゲートに失敗:\n{proc.stdout}\n{proc.stderr}"
    assert "稼働コネクタ" in proc.stdout
