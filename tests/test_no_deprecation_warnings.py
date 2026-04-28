import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run_import(module_name: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-W", "error::DeprecationWarning", "-c", f"import {module_name}"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )


def test_models_import_without_deprecation_warnings() -> None:
    result = _run_import("models")
    assert result.returncode == 0, result.stderr


def test_email_routes_import_without_deprecation_warnings() -> None:
    result = _run_import("routes.email_routes")
    assert result.returncode == 0, result.stderr
