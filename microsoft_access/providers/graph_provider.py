from __future__ import annotations

from models import AccountCredentials, EmailDetailsResponse, EmailListResponse


def _graph_credentials(credentials: AccountCredentials) -> AccountCredentials:
    return credentials.model_copy(update={"api_method": "graph_api"})


async def list_messages(
    credentials: AccountCredentials,
    *,
    folder: str,
    page: int,
    page_size: int,
    skip_cache: bool = False,
    sender_search: str | None = None,
    subject_search: str | None = None,
    sort_by: str = "date",
    sort_order: str = "desc",
    start_time: str | None = None,
    end_time: str | None = None,
) -> EmailListResponse:
    from email_service import _list_emails_direct

    return await _list_emails_direct(
        _graph_credentials(credentials),
        folder=folder,
        page=page,
        page_size=page_size,
        force_refresh=skip_cache,
        sender_search=sender_search,
        subject_search=subject_search,
        sort_by=sort_by,
        sort_order=sort_order,
        start_time=start_time,
        end_time=end_time,
    )


async def get_message_detail(
    credentials: AccountCredentials,
    message_id: str,
    *,
    skip_cache: bool = False,
) -> EmailDetailsResponse:
    from email_service import _get_email_details_direct

    return await _get_email_details_direct(
        _graph_credentials(credentials),
        message_id,
        skip_cache=skip_cache,
    )


async def list_messages_with_body(
    credentials: AccountCredentials,
    *,
    folder: str,
    page: int,
    page_size: int,
    skip_cache: bool = False,
    sender_search: str | None = None,
    subject_search: str | None = None,
    sort_by: str = "date",
    sort_order: str = "desc",
    start_time: str | None = None,
    end_time: str | None = None,
) -> list[dict]:
    from graph_api_service import list_emails_with_body_graph

    return await list_emails_with_body_graph(
        _graph_credentials(credentials),
        folder=folder,
        max_count=page_size,
        sender_search=sender_search,
        subject_search=subject_search,
        sort_by=sort_by,
        sort_order=sort_order,
        start_time=start_time,
        end_time=end_time,
    )


async def delete_message(
    credentials: AccountCredentials,
    message_id: str,
) -> bool:
    from email_service import delete_email

    return await delete_email(_graph_credentials(credentials), message_id)


async def delete_messages_batch(
    credentials: AccountCredentials,
    *,
    folder: str,
) -> dict:
    from email_service import delete_emails_batch

    return await delete_emails_batch(_graph_credentials(credentials), folder)


async def send_message(
    credentials: AccountCredentials,
    *,
    to: str,
    subject: str,
    body_text: str | None = None,
    body_html: str | None = None,
) -> str:
    from email_service import send_email

    return await send_email(
        _graph_credentials(credentials),
        to,
        subject,
        body_text,
        body_html,
    )
