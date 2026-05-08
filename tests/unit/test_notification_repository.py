from datetime import datetime, timedelta

import pytest

from app.domain.notifications.models.notification_model import NotificationType
from app.domain.notifications.repositories.notification_repository import (
    NotificationRepository,
)
from tests.factories.notification_factory import make_notification
from tests.factories.user_factory import make_user


async def seed_notifications(db_session):
    user = make_user(email="notification-user@email.com")
    other_user = make_user(email="other-notification-user@email.com")
    now = datetime.utcnow()
    db_session.add_all(
        [
            user,
            other_user,
        ]
    )
    await db_session.commit()

    newest_notification = make_notification(
        user_id=user.id,
        notification_type=NotificationType.LOAN_RETURNED,
        message="Newest",
        created_at=now,
    )
    oldest_notification = make_notification(
        user_id=user.id,
        notification_type=NotificationType.LOAN_CREATED,
        message="Oldest",
        created_at=now - timedelta(days=1),
    )
    other_user_notification = make_notification(
        user_id=other_user.id,
        notification_type=NotificationType.LOAN_CANCELLED,
        message="Other user",
        created_at=now - timedelta(hours=1),
    )

    db_session.add_all(
        [
            newest_notification,
            oldest_notification,
            other_user_notification,
        ]
    )
    await db_session.commit()

    return {
        "user": user,
        "other_user": other_user,
        "newest_notification": newest_notification,
        "oldest_notification": oldest_notification,
        "other_user_notification": other_user_notification,
    }


@pytest.mark.asyncio
async def test_repository_should_create_notification(db_session):
    user = make_user(email="notification-create-user@email.com")
    db_session.add(user)
    await db_session.commit()
    repository = NotificationRepository(db_session)
    notification = make_notification(
        user_id=user.id,
        message="Created notification",
    )

    created_notification = await repository.create(
        notification
    )

    assert created_notification.id == notification.id
    assert created_notification.message == "Created notification"


@pytest.mark.asyncio
async def test_repository_should_list_notifications_paginated(db_session):
    data = await seed_notifications(db_session)
    repository = NotificationRepository(db_session)

    notifications, total = await repository.list_paginated(
        page=1,
        size=2,
    )

    assert total == 3
    assert len(notifications) == 2
    assert notifications[0].id == data["newest_notification"].id


@pytest.mark.asyncio
async def test_repository_should_filter_notifications_by_user(db_session):
    data = await seed_notifications(db_session)
    repository = NotificationRepository(db_session)

    notifications, total = await repository.list_paginated(
        page=1,
        size=10,
        user_id=data["user"].id,
    )

    assert total == 2
    assert [notification.id for notification in notifications] == [
        data["newest_notification"].id,
        data["oldest_notification"].id,
    ]
