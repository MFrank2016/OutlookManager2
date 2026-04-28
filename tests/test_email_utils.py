from datetime import datetime
from email.message import EmailMessage

from email_utils import (
    extract_email_address,
    extract_email_addresses,
    get_message_id,
    parse_email_datetime,
)


def test_get_message_id_uses_header_when_present():
    msg = EmailMessage()
    msg["Message-ID"] = "<abc123@example.com>"

    assert get_message_id(msg) == "abc123@example.com"


def test_get_message_id_falls_back_to_subject_and_date_hash():
    msg = EmailMessage()
    msg["Subject"] = "Verification"
    msg["Date"] = "Mon, 01 Jan 2026 12:00:00 +0000"

    generated = get_message_id(msg)
    assert generated.endswith("@generated")
    assert generated


def test_extract_email_address_returns_primary_address():
    value = '"Microsoft Account Team" <noreply@microsoft.com>'
    assert extract_email_address(value) == "noreply@microsoft.com"


def test_extract_email_addresses_returns_all_addresses():
    value = '"A" <a@example.com>, b@example.com, "C" <c@example.com>'
    assert extract_email_addresses(value) == [
        "a@example.com",
        "b@example.com",
        "c@example.com",
    ]


def test_parse_email_datetime_parses_valid_rfc2822_string():
    parsed = parse_email_datetime("Mon, 01 Jan 2026 12:00:00 +0000")
    assert isinstance(parsed, datetime)
    assert parsed.year == 2026
    assert parsed.month == 1
    assert parsed.day == 1
