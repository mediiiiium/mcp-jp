"""API sunset 巡回チェック（tools/check_api_sunset.py）の回帰テスト。

ネットワーク不要のオフライン点検（記録漏れ・廃止超過ゲート）が常にグリーンで
あることを CI で保証する。新規コネクタの登録漏れや、sunset_date を過ぎた
API バージョンの移行忘れがあると exit 1 になり、ここで失敗する。
"""
import subprocess
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools" / "check_api_sunset.py"


def test_offline_check_passes():
    """オフライン点検は記録漏れ・廃止超過なしで exit 0 を返す。"""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"API sunset チェックに失敗:\n{proc.stdout}\n{proc.stderr}"
    assert "稼働コネクタ" in proc.stdout
