from datetime import datetime

import uuid6 as uuid

from app.domain.notifications.models.notification_model import (
    NotificationModel,
    NotificationStatus,
    NotificationType,
)


def make_notification(
    user_id: str | None = None,
    loan_id: str | None = None,
    reservation_id: str | None = None,
    notification_type: NotificationType = NotificationType.LOAN_CREATED,
    status: NotificationStatus = NotificationStatus.SENT,
    channel: str = "EMAIL_FAKE",
    message: str = "Notification message",
    sent_at: datetime | None = None,
    created_at: datetime | None = None,
):
    return NotificationModel(
        id=str(uuid.uuid7()),
        user_id=user_id or str(uuid.uuid7()),
        loan_id=loan_id,
        reservation_id=reservation_id,
        type=notification_type,
        status=status,
        channel=channel,
        message=message,
        sent_at=sent_at or datetime.utcnow(),
        created_at=created_at or datetime.utcnow(),
    )
