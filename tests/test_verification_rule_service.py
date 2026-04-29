from datetime import datetime

import database as db

from verification_rule_service import (
    create_verification_rule,
    delete_verification_rule,
    detect_verification_code_with_rules,
    list_verification_rules,
    run_verification_rule_test_for_message,
)


def _clear_rule_tables() -> None:
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        for table_name in (
            "verification_detection_records",
            "verification_rule_matchers",
            "verification_rule_extractors",
            "verification_rules",
        ):
            cursor.execute(f"DELETE FROM {table_name}")
        conn.commit()


def _rule_payload(*, name: str, priority: int, matchers: list[dict], extractors: list[dict], **extra):
    payload = {
        "name": name,
        "scope_type": extra.pop("scope_type", "global"),
        "match_mode": extra.pop("match_mode", "or"),
        "priority": priority,
        "enabled": extra.pop("enabled", True),
        "matchers": matchers,
        "extractors": extractors,
        "description": extra.pop("description", None),
    }
    payload.update(extra)
    return payload


def setup_function():
    _clear_rule_tables()


def teardown_function():
    _clear_rule_tables()


def test_targeted_rule_precedes_global_rule_and_records_success():
    targeted = create_verification_rule(
        _rule_payload(
            name="Microsoft 定向规则",
            scope_type="targeted",
            match_mode="or",
            priority=100,
            description="只匹配微软验证码",
            matchers=[
                {"source_type": "sender", "keyword": "microsoft", "sort_order": 1},
                {"source_type": "subject", "keyword": "security code", "sort_order": 2},
            ],
            extractors=[
                {"source_type": "subject", "extract_pattern": r"(\d{6})", "sort_order": 1},
                {"source_type": "body", "extract_pattern": r"(\d{6})", "sort_order": 2},
            ],
        )
    )
    create_verification_rule(
        _rule_payload(
            name="通用验证码规则",
            priority=10,
            matchers=[{"source_type": "body", "keyword": "code", "sort_order": 1}],
            extractors=[{"source_type": "body", "extract_pattern": r"(\d{4,8})", "sort_order": 1}],
        )
    )

    result = detect_verification_code_with_rules(
        email_account="user@example.com",
        message_id="msg-1",
        from_email="account-security-noreply@Microsoft.com",
        subject="Use this security code",
        body_plain="Use this Microsoft account security code. 654321",
        source="runtime",
        page_source="detail",
        persist_record=True,
    )

    assert result["code"] == "654321"
    assert result["matched_rule"]["id"] == targeted["id"]
    assert result["matched_rule"]["scope_type"] == "targeted"
    assert result["resolved_code_source"] == "body"

    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT detected_code, rule_id, source, page_source FROM verification_detection_records"
        )
        row = cursor.fetchone()
        assert row["detected_code"] == "654321"
        assert row["rule_id"] == targeted["id"]
        assert row["source"] == "runtime"
        assert row["page_source"] == "detail"


def test_any_matcher_hit_enters_extractor_pipeline():
    rule = create_verification_rule(
        _rule_payload(
            name="GitHub OTP",
            priority=10,
            matchers=[
                {"source_type": "sender", "keyword": "github", "sort_order": 1},
                {"source_type": "body", "keyword": "temporary code", "sort_order": 2},
            ],
            extractors=[
                {"source_type": "subject", "extract_pattern": r"(\d{6})", "sort_order": 1},
                {"source_type": "body", "extract_pattern": r"(\d{6})", "sort_order": 2},
            ],
        )
    )

    result = detect_verification_code_with_rules(
        email_account="demo@example.com",
        message_id="msg-2",
        from_email="noreply@github.com",
        subject="login notice",
        body_plain="Your temporary code is 112233",
        persist_record=False,
    )

    assert result["code"] == "112233"
    assert result["matched_rule"]["id"] == rule["id"]
    assert result["resolved_code_source"] == "body"
    assert [item["source_type"] for item in result["matched_matchers"]] == ["sender", "body"]
    assert [item["source_type"] for item in result["extractor_attempts"]] == ["subject", "body"]


def test_subject_extractor_precedes_body_extractor():
    rule = create_verification_rule(
        _rule_payload(
            name="主题优先规则",
            priority=20,
            matchers=[{"source_type": "sender", "keyword": "contoso", "sort_order": 1}],
            extractors=[
                {"source_type": "subject", "extract_pattern": r"(\d{6})", "sort_order": 1},
                {"source_type": "body", "extract_pattern": r"(\d{6})", "sort_order": 2},
            ],
        )
    )

    result = detect_verification_code_with_rules(
        email_account="subject@example.com",
        message_id="msg-subject",
        from_email="login@contoso.com",
        subject="Verification 246810",
        body_plain="Use code 135790 if prompted",
        persist_record=False,
    )

    assert result["code"] == "246810"
    assert result["matched_rule"]["id"] == rule["id"]
    assert result["resolved_code_source"] == "subject"
    assert result["extractor_attempts"][0]["source_type"] == "subject"


def test_matcher_hit_but_extractors_fail_then_fallback_runs():
    create_verification_rule(
        _rule_payload(
            name="Apple subject only",
            priority=30,
            matchers=[{"source_type": "sender", "keyword": "apple", "sort_order": 1}],
            extractors=[{"source_type": "subject", "extract_pattern": r"(\d{6})", "sort_order": 1}],
        )
    )

    result = detect_verification_code_with_rules(
        email_account="fallback@example.com",
        message_id="msg-fallback",
        from_email="appleid@apple.com",
        subject="Security alert",
        body_plain="Your OTP is 778899",
        persist_record=False,
    )

    assert result["code"] == "778899"
    assert result["matched_rule"] is None
    assert result["matched_via"] == "fallback"
    assert [item["source_type"] for item in result["rule_evaluations"][0]["matched_matchers"]] == ["sender"]
    assert result["rule_evaluations"][0]["extractor_attempts"][0]["source_type"] == "subject"


def test_can_test_rule_against_cached_email_detail():
    rule = create_verification_rule(
        _rule_payload(
            name="主题命中规则",
            scope_type="targeted",
            priority=50,
            matchers=[
                {"source_type": "sender", "keyword": "apple", "sort_order": 1},
                {"source_type": "subject", "keyword": "verification", "sort_order": 2},
            ],
            extractors=[
                {"source_type": "subject", "extract_pattern": r"(\d{6})", "sort_order": 1},
                {"source_type": "body", "extract_pattern": r"(\d{6})", "sort_order": 2},
            ],
        )
    )

    db.cache_email_detail(
        "apple@example.com",
        {
            "message_id": "cached-msg-1",
            "subject": "Apple verification",
            "from_email": "appleid@apple.com",
            "to_email": "apple@example.com",
            "date": datetime.now().isoformat(),
            "body_plain": "Verification code 445566",
            "body_html": None,
            "verification_code": None,
        },
    )

    result = run_verification_rule_test_for_message(
        email_account="apple@example.com",
        message_id="cached-msg-1",
        rule_id=rule["id"],
    )

    assert result["code"] == "445566"
    assert result["matched_rule"]["id"] == rule["id"]
    assert result["source"] == "test"
    assert result["page_source"] == "admin-test"
    assert result["resolved_code_source"] == "body"


def test_rule_crud_roundtrip():
    created = create_verification_rule(
        _rule_payload(
            name="CRUD 规则",
            priority=1,
            matchers=[{"source_type": "body", "keyword": "otp", "sort_order": 1}],
            extractors=[{"source_type": "body", "extract_pattern": r"(\d{6})", "sort_order": 1}],
        )
    )

    listed = list_verification_rules()
    assert any(rule["id"] == created["id"] for rule in listed)

    assert delete_verification_rule(created["id"]) is True
    assert all(rule["id"] != created["id"] for rule in list_verification_rules())
