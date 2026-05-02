import pathlib
import subprocess
import sys
import textwrap

import pytest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_token_bucket_cleanup_path_does_not_deadlock():
    script = textwrap.dedent(
        """
        import pathlib
        import sys

        project_root = pathlib.Path.cwd()
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        from rate_limiter import TokenBucket

        bucket = TokenBucket(max_tokens=1, refill_rate=1.0, cleanup_interval=0)
        assert bucket.acquire("share-token") is True
        print("ok")
        """
    )

    try:
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=1,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        pytest.fail(f"TokenBucket.acquire 在 cleanup 路径发生死锁: {exc}")

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip().endswith("ok")
