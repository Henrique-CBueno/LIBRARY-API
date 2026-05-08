from datetime import datetime

import structlog

from app.domain.notifications.models.notification_model import NotificationModel, NotificationStatus, NotificationType
from app.domain.notifications.repositories.notification_repository import NotificationRepository

logger = structlog.get_logger()


class NotificationService:
    def __init__(
        self,
        repository: NotificationRepository,
    ):
        self.repository = repository

    async def send_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        message: str,
        loan_id: str | None = None,
    ):
        notification = NotificationModel(
            user_id=user_id,
            loan_id=loan_id,
            type=notification_type,
            status=NotificationStatus.SENT,
            channel="EMAIL_FAKE",
            message=message,
            sent_at=datetime.utcnow(),
        )

        created = await self.repository.create(notification)

        logger.info(
            "notification_sent",
            notification_id=str(created.id),
            user_id=str(user_id),
            loan_id=str(loan_id) if loan_id else None,
            type=notification_type,
        )

        return created

    async def list_paginated(
        self,
        page: int,
        size: int,
        user_id: str | None = None,
    ):
        notifications, total = await self.repository.list_paginated(
            page=page,
            size=size,
            user_id=user_id,
        )

        return {
            "items": notifications,
            "total": total,
            "page": page,
            "size": size,
        }