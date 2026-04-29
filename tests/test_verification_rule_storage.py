import database as db


LEGACY_RULE_PAYLOAD = {
    "name": "Legacy Outlook Rule",
    "scope_type": "global",
    "match_mode": "and",
    "priority": 5,
    "enabled": 1,
    "sender_pattern": "microsoft",
    "subject_pattern": "security code",
    "body_pattern": "temporary code",
    "extract_pattern": r"(\\d{6})",
    "is_regex": 1,
    "description": "legacy columns",
}


def _clear_rule_tables() -> None:
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        for table_name in (
            "verification_detection_records",
            "verification_rule_matchers",
            "verification_rule_extractors",
            "verification_rules",
        ):
            try:
                cursor.execute(f"DELETE FROM {table_name}")
            except Exception:
                continue
        conn.commit()


def setup_function():
    _clear_rule_tables()


def teardown_function():
    _clear_rule_tables()


def test_create_rule_with_matchers_and_extractors_roundtrip():
    rule = db.create_verification_rule(
        {
            "name": "Microsoft 登录验证码",
            "scope_type": "targeted",
            "match_mode": "or",
            "priority": 100,
            "enabled": True,
            "description": "subject first",
            "matchers": [
                {"source_type": "sender", "keyword": "microsoft", "sort_order": 1},
                {"source_type": "subject", "keyword": "security code", "sort_order": 2},
            ],
            "extractors": [
                {"source_type": "subject", "extract_pattern": r"(\\d{6})", "sort_order": 1},
                {"source_type": "body", "extract_pattern": r"(\\d{6})", "sort_order": 2},
            ],
        }
    )

    assert rule["matchers"][0]["source_type"] == "sender"
    assert rule["extractors"][1]["source_type"] == "body"

    listed = db.list_verification_rules()
    assert listed[0]["matchers"][0]["source_type"] == "sender"
    assert listed[0]["extractors"][1]["source_type"] == "body"


def test_legacy_rule_columns_migrate_to_matchers_and_extractors():
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO verification_rules (
                name, scope_type, match_mode, priority, enabled,
                sender_pattern, subject_pattern, body_pattern,
                extract_pattern, is_regex, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                LEGACY_RULE_PAYLOAD["name"],
                LEGACY_RULE_PAYLOAD["scope_type"],
                LEGACY_RULE_PAYLOAD["match_mode"],
                LEGACY_RULE_PAYLOAD["priority"],
                LEGACY_RULE_PAYLOAD["enabled"],
                LEGACY_RULE_PAYLOAD["sender_pattern"],
                LEGACY_RULE_PAYLOAD["subject_pattern"],
                LEGACY_RULE_PAYLOAD["body_pattern"],
                LEGACY_RULE_PAYLOAD["extract_pattern"],
                LEGACY_RULE_PAYLOAD["is_regex"],
                LEGACY_RULE_PAYLOAD["description"],
            ),
        )
        conn.commit()

    listed = db.list_verification_rules()

    assert len(listed) == 1
    assert [matcher["source_type"] for matcher in listed[0]["matchers"]] == [
        "sender",
        "subject",
        "body",
    ]
    assert [extractor["source_type"] for extractor in listed[0]["extractors"]] == [
        "subject",
        "body",
    ]
    assert all(
        extractor["extract_pattern"] == LEGACY_RULE_PAYLOAD["extract_pattern"]
        for extractor in listed[0]["extractors"]
    )

    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS c FROM verification_rule_matchers")
        matcher_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) AS c FROM verification_rule_extractors")
        extractor_count = cursor.fetchone()[0]

    assert matcher_count == 3
    assert extractor_count == 2
