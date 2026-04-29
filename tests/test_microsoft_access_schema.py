import asyncio
import inspect
import json
import sqlite3
from pathlib import Path

import account_service
import database as db
from dao.account_dao import AccountDAO
from models import AccountCredentials


def test_account_credentials_exposes_strategy_fields():
    credentials = AccountCredentials(
        email="user@example.com",
        refresh_token="rt",
        client_id="cid",
    )
    assert credentials.strategy_mode == "auto"
    assert credentials.lifecycle_state == "new"


def test_init_database_adds_microsoft_access_columns(tmp_path, monkeypatch):
    db_file = tmp_path / "microsoft_access_schema.db"
    monkeypatch.setattr(db, "DB_TYPE", "sqlite")
    monkeypatch.setattr(db, "DB_FILE", str(db_file))
    monkeypatch.setattr(db, "_sqlite_last_integrity_check_ts", 0.0)

    db.init_database()

    with sqlite3.connect(db_file) as conn:
        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(accounts)").fetchall()
        }

    assert "strategy_mode" in columns
    assert "lifecycle_state" in columns
    assert "capability_snapshot_json" in columns
    assert "provider_health_json" in columns


def test_postgresql_static_schema_includes_microsoft_access_columns():
    schema_sql = Path("database/postgresql_schema.sql").read_text(encoding="utf-8")

    assert "strategy_mode" in schema_sql
    assert "lifecycle_state" in schema_sql
    assert "last_provider_used" in schema_sql
    assert "capability_snapshot_json" in schema_sql
    assert "provider_health_json" in schema_sql


def test_postgresql_runtime_migration_ensures_api_method_column():
    migration_source = inspect.getsource(db._init_postgresql_database)

    assert "ADD COLUMN IF NOT EXISTS api_method TEXT DEFAULT 'imap'" in migration_source


def test_init_database_migrates_legacy_sqlite_accounts_table(tmp_path, monkeypatch):
    db_file = tmp_path / "legacy_accounts.db"
    monkeypatch.setattr(db, "DB_TYPE", "sqlite")
    monkeypatch.setattr(db, "DB_FILE", str(db_file))
    monkeypatch.setattr(db, "_sqlite_last_integrity_check_ts", 0.0)

    with sqlite3.connect(db_file) as conn:
        conn.execute(
            """
            CREATE TABLE accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                refresh_token TEXT NOT NULL,
                client_id TEXT NOT NULL,
                tags TEXT DEFAULT '[]',
                last_refresh_time TEXT,
                next_refresh_time TEXT,
                refresh_status TEXT DEFAULT 'pending',
                refresh_error TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()

    db.init_database()

    with sqlite3.connect(db_file) as conn:
        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(accounts)").fetchall()
        }

    assert "strategy_mode" in columns
    assert "lifecycle_state" in columns
    assert "last_provider_used" in columns
    assert "capability_snapshot_json" in columns
    assert "provider_health_json" in columns


def test_account_dao_round_trip_and_update_preserves_metadata(tmp_path, monkeypatch):
    db_file = tmp_path / "dao_round_trip.db"
    monkeypatch.setattr(db, "DB_TYPE", "sqlite")
    monkeypatch.setattr(db, "DB_FILE", str(db_file))
    monkeypatch.setattr(db, "_sqlite_last_integrity_check_ts", 0.0)

    db.init_database()
    dao = AccountDAO()

    dao.create(
        email="dao-roundtrip@example.com",
        refresh_token="rt",
        client_id="cid",
        tags=["team"],
        strategy_mode="manual",
        lifecycle_state="ready",
        last_provider_used="graph",
        capability_snapshot_json={"imap": True, "graph": {"enabled": True}},
        provider_health_json='{"graph":"healthy"}',
    )

    account = dao.get_by_email("dao-roundtrip@example.com")
    assert account is not None
    assert account["strategy_mode"] == "manual"
    assert account["lifecycle_state"] == "ready"
    assert account["last_provider_used"] == "graph"
    assert json.loads(account["capability_snapshot_json"]) == {
        "imap": True,
        "graph": {"enabled": True},
    }
    assert json.loads(account["provider_health_json"]) == {"graph": "healthy"}

    records, total = dao.get_by_filters(include_tags=["team"])
    assert total == 1
    assert len(records) == 1
    assert records[0]["email"] == "dao-roundtrip@example.com"
    assert records[0]["strategy_mode"] == "manual"
    assert json.loads(records[0]["capability_snapshot_json"]) == {
        "imap": True,
        "graph": {"enabled": True},
    }

    assert dao.update_account(
        "dao-roundtrip@example.com",
        capability_snapshot_json={"graph": {"enabled": False}},
        provider_health_json={"imap": "degraded"},
        last_provider_used="imap",
        lifecycle_state="cooldown",
    )

    updated = dao.get_by_email("dao-roundtrip@example.com")
    assert updated is not None
    assert updated["strategy_mode"] == "manual"
    assert updated["lifecycle_state"] == "cooldown"
    assert updated["last_provider_used"] == "imap"
    assert json.loads(updated["capability_snapshot_json"]) == {
        "graph": {"enabled": False}
    }
    assert json.loads(updated["provider_health_json"]) == {"imap": "degraded"}


def test_save_account_credentials_preserves_existing_metadata_for_legacy_calls(
    tmp_path, monkeypatch
):
    db_file = tmp_path / "service_metadata_preserve.db"
    monkeypatch.setattr(db, "DB_TYPE", "sqlite")
    monkeypatch.setattr(db, "DB_FILE", str(db_file))
    monkeypatch.setattr(db, "_sqlite_last_integrity_check_ts", 0.0)

    db.init_database()
    dao = AccountDAO()
    dao.create(
        email="service-preserve@example.com",
        refresh_token="old-rt",
        client_id="old-cid",
        strategy_mode="manual",
        lifecycle_state="ready",
        last_provider_used="graph",
        capability_snapshot_json={"graph": {"enabled": True}},
        provider_health_json={"graph": "healthy"},
    )

    credentials = AccountCredentials(
        email="service-preserve@example.com",
        refresh_token="new-rt",
        client_id="new-cid",
    )
    asyncio.run(
        account_service.save_account_credentials(
            "service-preserve@example.com",
            credentials,
        )
    )

    updated = dao.get_by_email("service-preserve@example.com")
    assert updated is not None
    assert updated["refresh_token"] == "new-rt"
    assert updated["client_id"] == "new-cid"
    assert updated["strategy_mode"] == "manual"
    assert updated["lifecycle_state"] == "ready"
    assert updated["last_provider_used"] == "graph"
    assert json.loads(updated["capability_snapshot_json"]) == {
        "graph": {"enabled": True}
    }
    assert json.loads(updated["provider_health_json"]) == {"graph": "healthy"}


def test_save_account_credentials_preserves_existing_optional_legacy_fields(
    tmp_path, monkeypatch
):
    db_file = tmp_path / "service_legacy_optional_preserve.db"
    monkeypatch.setattr(db, "DB_TYPE", "sqlite")
    monkeypatch.setattr(db, "DB_FILE", str(db_file))
    monkeypatch.setattr(db, "_sqlite_last_integrity_check_ts", 0.0)

    db.init_database()
    dao = AccountDAO()
    dao.create(
        email="service-legacy-fields@example.com",
        refresh_token="old-rt",
        client_id="old-cid",
        tags=["existing-tag"],
    )
    assert dao.update_account(
        "service-legacy-fields@example.com",
        last_refresh_time="2026-04-01T10:00:00",
        next_refresh_time="2026-04-02T10:00:00",
        refresh_status="success",
        refresh_error="transient-error",
    )

    credentials = AccountCredentials(
        email="service-legacy-fields@example.com",
        refresh_token="new-rt",
        client_id="new-cid",
    )
    asyncio.run(
        account_service.save_account_credentials(
            "service-legacy-fields@example.com",
            credentials,
        )
    )

    updated = dao.get_by_email("service-legacy-fields@example.com")
    assert updated is not None
    assert updated["refresh_token"] == "new-rt"
    assert updated["client_id"] == "new-cid"
    assert updated["tags"] == ["existing-tag"]
    assert updated["last_refresh_time"] == "2026-04-01T10:00:00"
    assert updated["next_refresh_time"] == "2026-04-02T10:00:00"
    assert updated["refresh_status"] == "success"
    assert updated["refresh_error"] == "transient-error"
