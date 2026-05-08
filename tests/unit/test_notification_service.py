from unittest.mock import AsyncMock

import pytest

from app.domain.notifications.models.notification_model import (
    NotificationStatus,
    NotificationType,
)
from app.domain.notifications.services.notification_service import NotificationService
from tests.factories.notification_factory import make_notification


def make_service():
    repository = AsyncMock()

    return NotificationService(repository), repository


@pytest.mark.asyncio
async def test_should_send_notification():
    service, repository = make_service()
    notification = make_notification(
        user_id="user-id",
        loan_id="loan-id",
        notification_type=NotificationType.LOAN_CREATED,
        message="Loan created",
    )
    repository.create.return_value = notification

    response = await service.send_notification(
        user_id="user-id",
        loan_id="loan-id",
        notification_type=NotificationType.LOAN_CREATED,
        message="Loan created",
    )

    saved_notification = repository.create.await_args.args[0]

    assert response == notification
    assert saved_notification.user_id == "user-id"
    assert saved_notification.loan_id == "loan-id"
    assert saved_notification.type == NotificationType.LOAN_CREATED
    assert saved_notification.status == NotificationStatus.SENT
    assert saved_notification.channel == "EMAIL_FAKE"
    assert saved_notification.message == "Loan created"
    assert saved_notification.sent_at is not None


@pytest.mark.asyncio
async def test_should_send_notification_without_loan_id():
    service, repository = make_service()
    notification = make_notification(
        user_id="user-id",
        loan_id=None,
        notification_type=NotificationType.LOAN_OVERDUE,
    )
    repository.create.return_value = notification

    response = await service.send_notification(
        user_id="user-id",
        loan_id=None,
        notification_type=NotificationType.LOAN_OVERDUE,
        message="Loan overdue",
    )

    saved_notification = repository.create.await_args.args[0]

    assert response == notification
    assert saved_notification.loan_id is None


@pytest.mark.asyncio
async def test_should_list_notifications_paginated():
    service, repository = make_service()
    notifications = [
        make_notification(user_id="user-id"),
        make_notification(user_id="user-id"),
    ]
    repository.list_paginated.return_value = (
        notifications,
        2,
    )

    response = await service.list_paginated(
        page=1,
        size=10,
        user_id="user-id",
    )

    assert response["items"] == notifications
    assert response["total"] == 2
    assert response["page"] == 1
    assert response["size"] == 10
    repository.list_paginated.assert_awaited_once_with(
        page=1,
        size=10,
        user_id="user-id",
    )
