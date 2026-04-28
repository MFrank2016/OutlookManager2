import os
from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_DB_FILE = Path(__file__).resolve().parent / ".pytest_data.db"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 默认 pytest 基线一律使用本地 SQLite 测试库，避免依赖远程 PostgreSQL。
os.environ["DB_TYPE"] = "sqlite"
os.environ["DB_FILE"] = str(TEST_DB_FILE)


LIVE_TEST_FILES = {
    "test_admin_panel_apis.py",
    "test_new_features.py",
    "test_token_refresh.py",
}

BENCHMARK_TEST_FILES = {
    "test_cache_performance.py",
}


def pytest_sessionstart(session: pytest.Session) -> None:
    if TEST_DB_FILE.exists():
        TEST_DB_FILE.unlink()

    import database as db

    db.init_database()


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    if TEST_DB_FILE.exists():
        TEST_DB_FILE.unlink()


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    skip_live = pytest.mark.skip(
        reason="requires live server or real credentials; set RUN_LIVE_TESTS=1 to run"
    )
    skip_benchmark = pytest.mark.skip(
        reason="benchmark test skipped in default baseline; set RUN_BENCHMARK_TESTS=1 to run"
    )
    for item in items:
        if os.getenv("RUN_LIVE_TESTS") != "1" and item.fspath.basename in LIVE_TEST_FILES:
            item.add_marker(skip_live)
        if os.getenv("RUN_BENCHMARK_TESTS") != "1" and item.fspath.basename in BENCHMARK_TEST_FILES:
            item.add_marker(skip_benchmark)
