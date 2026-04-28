import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_pytest_default_collection_stays_inside_tests_directory() -> None:
    env = os.environ.copy()
    env.pop("PYTEST_ADDOPTS", None)

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
        env=env,
    )

    combined_output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, combined_output
    assert "scripts/test_tables.py" not in combined_output
