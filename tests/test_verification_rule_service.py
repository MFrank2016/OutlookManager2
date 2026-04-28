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
        cursor.execute("DELETE FROM verification_detection_records")
        cursor.execute("DELETE FROM verification_rules")
        conn.commit()


def setup_function():
    _clear_rule_tables()


def teardown_function():
    _clear_rule_tables()


def test_targeted_rule_precedes_global_rule_and_records_success():
    targeted = create_verification_rule(
        {
            "name": "Microsoft 定向规则",
            "scope_type": "targeted",
            "match_mode": "and",
            "priority": 100,
            "enabled": True,
            "sender_pattern": "microsoft",
            "subject_pattern": "security code",
            "body_pattern": "security code",
            "extract_pattern": r"security code\.\s*(\d{6})",
            "is_regex": True,
            "description": "只匹配微软验证码",
        }
    )
    create_verification_rule(
        {
            "name": "通用验证码规则",
            "scope_type": "global",
            "match_mode": "or",
            "priority": 10,
            "enabled": True,
            "body_pattern": "code",
            "extract_pattern": r"(\d{4,8})",
            "is_regex": True,
        }
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


def test_rule_match_mode_or_works():
    rule = create_verification_rule(
        {
            "name": "OR 规则",
            "scope_type": "global",
            "match_mode": "or",
            "priority": 20,
            "enabled": True,
            "sender_pattern": "github",
            "subject_pattern": "login",
            "body_pattern": "temporary code",
            "extract_pattern": r"(\d{6})",
            "is_regex": True,
        }
    )

    result = detect_verification_code_with_rules(
        email_account="user@example.com",
        message_id="msg-2",
        from_email="noreply@example.com",
        subject="No match in subject",
        body_plain="Your temporary code is 112233",
        persist_record=False,
    )

    assert result["code"] == "112233"
    assert result["matched_rule"]["id"] == rule["id"]


def test_fallback_detector_runs_when_no_rule_matches():
    result = detect_verification_code_with_rules(
        email_account="user@example.com",
        message_id="msg-3",
        from_email="random@example.com",
        subject="Verification message",
        body_plain="Your OTP is 778899",
        persist_record=False,
    )

    assert result["code"] == "778899"
    assert result["matched_rule"] is None
    assert result["matched_via"] == "fallback"


def test_can_test_rule_against_cached_email_detail():
    rule = create_verification_rule(
        {
            "name": "主题命中规则",
            "scope_type": "targeted",
            "match_mode": "and",
            "priority": 50,
            "enabled": True,
            "sender_pattern": "apple",
            "subject_pattern": "verification",
            "extract_pattern": r"(\d{6})",
            "is_regex": True,
        }
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


def test_rule_crud_roundtrip():
    created = create_verification_rule(
        {
            "name": "CRUD 规则",
            "scope_type": "global",
            "match_mode": "and",
            "priority": 1,
            "enabled": True,
            "body_pattern": "otp",
            "extract_pattern": r"(\d{6})",
            "is_regex": True,
        }
    )

    listed = list_verification_rules()
    assert any(rule["id"] == created["id"] for rule in listed)

    assert delete_verification_rule(created["id"]) is True
    assert all(rule["id"] != created["id"] for rule in list_verification_rules())
