from datetime import datetime, timedelta

from app.domain.notifications.repositories.notification_repository import (
    NotificationRepository,
)
from tests.factories.notification_factory import make_notification
from tests.helpers.user_helper import create_user


async def create_notification(
    db_session,
    user_id: str,
    message: str,
    created_at: datetime,
):
    repository = NotificationRepository(db_session)

    return await repository.create(
        make_notification(
            user_id=user_id,
            message=message,
            created_at=created_at,
        )
    )


async def test_should_list_notifications_paginated(
    client,
    db_session,
):
    user = await create_user(client)
    other_user = await create_user(
        client,
        email="other-notification@email.com",
    )
    now = datetime.utcnow()
    newest_notification = await create_notification(
        db_session,
        user["id"],
        "Newest",
        now,
    )
    await create_notification(
        db_session,
        other_user["id"],
        "Other user",
        now - timedelta(hours=1),
    )
    await create_notification(
        db_session,
        user["id"],
        "Oldest",
        now - timedelta(days=1),
    )

    response = await client.get(
        "/notifications?page=1&size=2"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 3
    assert body["page"] == 1
    assert body["size"] == 2
    assert len(body["items"]) == 2
    assert body["items"][0]["id"] == newest_notification.id


async def test_should_filter_notifications_by_user(
    client,
    db_session,
):
    user = await create_user(client)
    other_user = await create_user(
        client,
        email="another-notification@email.com",
    )
    now = datetime.utcnow()
    await create_notification(
        db_session,
        user["id"],
        "User notification",
        now,
    )
    await create_notification(
        db_session,
        other_user["id"],
        "Other user notification",
        now - timedelta(hours=1),
    )

    response = await client.get(
        f"/notifications?user_id={user['id']}"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert body["items"][0]["user_id"] == user["id"]
    assert body["items"][0]["message"] == "User notification"
