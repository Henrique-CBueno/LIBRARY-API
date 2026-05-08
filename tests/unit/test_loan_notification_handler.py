from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from app.domain.notifications.models.notification_model import NotificationType
from app.events.loans.events import (
    LoanCancelledEvent,
    LoanCreatedEvent,
    LoanReturnedEvent,
)
from app.events.loans.handlers.loan_notification_handler import (
    LoanCancelledNotificationHandler,
    LoanCreatedNotificationHandler,
    LoanReturnedNotificationHandler,
)


@pytest.mark.asyncio
async def test_loan_created_handler_should_send_notification():
    notification_service = AsyncMock()
    handler = LoanCreatedNotificationHandler(
        notification_service
    )
    event = LoanCreatedEvent(
        occurred_at=datetime.utcnow(),
        loan_id="loan-id",
        user_id="user-id",
        book_id="book-id",
    )

    await handler.handle(event)

    notification_service.send_notification.assert_awaited_once()
    kwargs = notification_service.send_notification.await_args.kwargs

    assert kwargs["user_id"] == "user-id"
    assert kwargs["loan_id"] == "loan-id"
    assert kwargs["notification_type"] == NotificationType.LOAN_CREATED


@pytest.mark.asyncio
async def test_loan_returned_handler_should_send_notification():
    notification_service = AsyncMock()
    handler = LoanReturnedNotificationHandler(
        notification_service
    )
    event = LoanReturnedEvent(
        occurred_at=datetime.utcnow(),
        loan_id="loan-id",
        user_id="user-id",
        book_id="book-id",
    )

    await handler.handle(event)

    notification_service.send_notification.assert_awaited_once_with(
        user_id="user-id",
        loan_id="loan-id",
        notification_type=NotificationType.LOAN_RETURNED,
        message="Empréstimo devolvido com sucesso.",
    )


@pytest.mark.asyncio
async def test_loan_cancelled_handler_should_send_notification():
    notification_service = AsyncMock()
    handler = LoanCancelledNotificationHandler(
        notification_service
    )
    event = LoanCancelledEvent(
        occurred_at=datetime.utcnow(),
        loan_id="loan-id",
        user_id="user-id",
        book_id="book-id",
    )

    await handler.handle(event)

    notification_service.send_notification.assert_awaited_once_with(
        user_id="user-id",
        loan_id="loan-id",
        notification_type=NotificationType.LOAN_CANCELLED,
        message="Empréstimo cancelado com sucesso.",
    )
