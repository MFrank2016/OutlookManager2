import asyncio
import pathlib
import sys

import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dao.account_dao import AccountDAO
from dao.batch_import_task_dao import BatchImportTaskItemDAO
from dao.email_cache_dao import EmailCacheDAO
from dao.share_token_dao import ShareTokenDAO
from routes import share_routes


def test_account_filters_use_index_friendly_order(monkeypatch: pytest.MonkeyPatch):
    dao = AccountDAO()
    captured = {}

    def fake_find_paginated(**kwargs):
        captured["order_by"] = kwargs.get("order_by")
        return [], 0

    monkeypatch.setattr(dao, "find_paginated", fake_find_paginated)
    dao.get_by_filters(page=200, page_size=50)

    assert captured["order_by"] == "created_at DESC, id DESC"


def test_account_tag_filters_use_jsonb_operator_on_postgres(monkeypatch: pytest.MonkeyPatch):
    dao = AccountDAO()
    captured = {}

    def fake_find_paginated(**kwargs):
        captured["where_clause"] = kwargs.get("where_clause")
        captured["params"] = kwargs.get("params")
        return [], 0

    monkeypatch.setattr("dao.account_dao.DB_TYPE", "postgresql")
    monkeypatch.setattr(dao, "find_paginated", fake_find_paginated)
    dao.get_by_filters(include_tags=["vip"], exclude_tags=["disabled"])

    assert "tags @>" in captured["where_clause"]
    assert "LIKE" not in captured["where_clause"]


def test_share_tokens_use_stable_index_friendly_order(monkeypatch: pytest.MonkeyPatch):
    dao = ShareTokenDAO()
    captured = {}

    def fake_find_paginated(**kwargs):
        captured["order_by"] = kwargs.get("order_by")
        return [], 0

    monkeypatch.setattr(dao, "find_paginated", fake_find_paginated)
    dao.list_tokens(page=3, page_size=50)

    assert captured["order_by"] == "created_at DESC, id DESC"


def test_account_filters_can_limit_result_set_by_allowed_emails(monkeypatch: pytest.MonkeyPatch):
    dao = AccountDAO()
    captured = {}

    def fake_find_paginated(**kwargs):
        captured["where_clause"] = kwargs.get("where_clause")
        captured["params"] = kwargs.get("params")
        return [], 0

    monkeypatch.setattr(dao, "find_paginated", fake_find_paginated)
    dao.get_by_filters(
        page=1,
        page_size=10,
        allowed_emails=["a@example.com", "b@example.com"],
    )

    assert "email IN" in captured["where_clause"]
    assert "a@example.com" in captured["params"]
    assert "b@example.com" in captured["params"]


def test_email_cache_uses_batch_upsert_instead_of_row_by_row(monkeypatch: pytest.MonkeyPatch):
    dao = EmailCacheDAO()
    call_stats = {"execute_count": 0, "executemany_count": 0}

    class FakeCursor:
        rowcount = 0

        def execute(self, *_args, **_kwargs):
            call_stats["execute_count"] += 1

        def executemany(self, *_args, **_kwargs):
            call_stats["executemany_count"] += 1

    class FakeConn:
        def __init__(self):
            self._cursor = FakeCursor()

        def cursor(self):
            return self._cursor

        def commit(self):
            return None

    class FakeConnCtx:
        def __enter__(self):
            return FakeConn()

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("dao.email_cache_dao.get_db_connection", lambda: FakeConnCtx())
    monkeypatch.setattr("dao.email_cache_dao.DB_TYPE", "sqlite")
    monkeypatch.setattr("dao.email_cache_dao.logger.info", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("dao.email_cache_dao.logger.error", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("dao.email_cache_dao.logger.warning", lambda *_args, **_kwargs: None)

    ok = dao.cache_emails(
        "perf@example.com",
        [
            {
                "message_id": "m1",
                "folder": "INBOX",
                "subject": "s1",
                "from_email": "a@example.com",
                "date": "2026-01-01T00:00:00",
                "is_read": False,
                "has_attachments": False,
                "sender_initial": "A",
                "verification_code": None,
                "body_preview": None,
            },
            {
                "message_id": "m2",
                "folder": "INBOX",
                "subject": "s2",
                "from_email": "b@example.com",
                "date": "2026-01-01T00:00:00",
                "is_read": True,
                "has_attachments": False,
                "sender_initial": "B",
                "verification_code": None,
                "body_preview": None,
            },
        ],
    )

    assert ok is True
    assert call_stats["executemany_count"] >= 1


def test_batch_import_items_use_batch_insert(monkeypatch: pytest.MonkeyPatch):
    dao = BatchImportTaskItemDAO()
    call_stats = {"execute_count": 0, "executemany_count": 0}

    class FakeCursor:
        rowcount = 0

        def execute(self, *_args, **_kwargs):
            call_stats["execute_count"] += 1

        def executemany(self, *_args, **_kwargs):
            call_stats["executemany_count"] += 1

    class FakeConn:
        def __init__(self):
            self._cursor = FakeCursor()

        def cursor(self):
            return self._cursor

        def commit(self):
            return None

    class FakeConnCtx:
        def __enter__(self):
            return FakeConn()

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("dao.batch_import_task_dao.get_db_connection", lambda: FakeConnCtx())
    monkeypatch.setattr("dao.batch_import_task_dao.logger.info", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("dao.batch_import_task_dao.logger.error", lambda *_args, **_kwargs: None)

    ok = dao.add_items(
        "task-1",
        [
            {"email": "a@example.com", "refresh_token": "r1", "client_id": "c1"},
            {"email": "b@example.com", "refresh_token": "r2", "client_id": "c2"},
        ],
    )

    assert ok is True
    assert call_stats["executemany_count"] >= 1


@pytest.mark.asyncio
async def test_share_list_tokens_runs_db_query_in_executor(monkeypatch: pytest.MonkeyPatch):
    called = {"run_in_executor": False}

    class FakeLoop:
        async def run_in_executor(self, executor, func, *args):
            called["run_in_executor"] = True
            return func(*args)

    monkeypatch.setattr(asyncio, "get_running_loop", lambda: FakeLoop())
    monkeypatch.setattr(share_routes.db, "list_share_tokens", lambda *args, **kwargs: ([], 0))
    monkeypatch.setattr(share_routes.db, "get_config", lambda key: None)

    result = await share_routes.list_tokens(
        email_account_id=None,
        account_search=None,
        token_search=None,
        page=1,
        page_size=50,
        current_user={"role": "admin"},
    )

    assert result == []
    assert called["run_in_executor"] is True


@pytest.mark.asyncio
async def test_share_list_tokens_reads_share_domain_once(monkeypatch: pytest.MonkeyPatch):
    class FakeLoop:
        async def run_in_executor(self, executor, func, *args):
            return func(*args)

    config_called = {"count": 0}

    def fake_list_share_tokens(*args, **kwargs):
        return (
            [
                {
                    "id": 1,
                    "token": "token-1",
                    "email_account_id": "a@example.com",
                    "start_time": "2026-01-01T00:00:00",
                    "created_at": "2026-01-01T00:00:00",
                    "is_active": True,
                    "max_emails": 10,
                },
                {
                    "id": 2,
                    "token": "token-2",
                    "email_account_id": "b@example.com",
                    "start_time": "2026-01-01T00:00:00",
                    "created_at": "2026-01-01T00:00:00",
                    "is_active": True,
                    "max_emails": 10,
                },
            ],
            2,
        )

    def fake_get_config(key: str):
        if key == "share_domain":
            config_called["count"] += 1
            return "https://share.example.com"
        return None

    monkeypatch.setattr(asyncio, "get_running_loop", lambda: FakeLoop())
    monkeypatch.setattr(share_routes.db, "list_share_tokens", fake_list_share_tokens)
    monkeypatch.setattr(share_routes.db, "get_config", fake_get_config)

    result = await share_routes.list_tokens(
        email_account_id=None,
        account_search=None,
        token_search=None,
        page=1,
        page_size=50,
        current_user={"role": "admin"},
    )

    assert len(result) == 2
    assert config_called["count"] == 1
