from models import EmailItem

from email_service import (
    _build_imap_recent_window,
    _enrich_paginated_items_from_cached_details,
    _should_prefetch_imap_detail,
    _should_use_imap_recent_window,
)


def test_should_use_imap_recent_window_only_for_unfiltered_recent_date_sort():
    assert _should_use_imap_recent_window(
        sender_search=None,
        subject_search=None,
        sort_by="date",
        sort_order="desc",
        start_time=None,
        end_time=None,
    ) is True

    assert _should_use_imap_recent_window(
        sender_search="github",
        subject_search=None,
        sort_by="date",
        sort_order="desc",
        start_time=None,
        end_time=None,
    ) is False

    assert _should_use_imap_recent_window(
        sender_search=None,
        subject_search=None,
        sort_by="subject",
        sort_order="desc",
        start_time=None,
        end_time=None,
    ) is False


def test_build_imap_recent_window_limits_old_message_fetches():
    message_ids = [str(i).encode() for i in range(1, 501)]
    selected = _build_imap_recent_window(message_ids, page=1, page_size=50)

    assert len(selected) >= 120
    assert len(selected) < len(message_ids)
    assert selected[0] == b"1"


def test_should_prefetch_imap_detail_for_likely_verification_mail():
    email = EmailItem(
        message_id="INBOX-1",
        folder="INBOX",
        subject="Your security code",
        from_email="noreply@microsoft.com",
        date="2026-01-01T00:00:00",
        sender_initial="M",
    )
    assert _should_prefetch_imap_detail(email) is True

    normal = EmailItem(
        message_id="INBOX-2",
        folder="INBOX",
        subject="Weekly newsletter",
        from_email="news@example.com",
        date="2026-01-01T00:00:00",
        sender_initial="N",
    )
    assert _should_prefetch_imap_detail(normal) is False


def test_enrich_paginated_items_from_cached_details_applies_code_and_preview():
    email = EmailItem(
        message_id="INBOX-1",
        folder="INBOX",
        subject="Security message",
        from_email="noreply@microsoft.com",
        date="2026-01-01T00:00:00",
        sender_initial="M",
        verification_code=None,
        body_preview=None,
    )

    details_by_id = {
        "INBOX-1": {
            "verification_code": "123456",
            "body_plain": "Your security code is 123456 and expires in 10 minutes.",
            "body_html": None,
        }
    }

    _enrich_paginated_items_from_cached_details([email], details_by_id)

    assert email.verification_code == "123456"
    assert email.body_preview is not None
    assert "123456" in email.body_preview
