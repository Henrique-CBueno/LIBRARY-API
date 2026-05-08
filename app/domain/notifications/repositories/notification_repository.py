from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.notifications.models.notification_model import NotificationModel, NotificationType


class NotificationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        notification: NotificationModel,
    ):
        self.db.add(notification)

        await self.db.commit()
        await self.db.refresh(notification)

        return notification

    async def list_paginated(
        self,
        page: int,
        size: int,
        user_id: str | None = None,
    ):
        offset = (page - 1) * size

        query = select(NotificationModel)
        count_query = select(func.count()).select_from(NotificationModel)

        if user_id:
            query = query.where(NotificationModel.user_id == user_id)
            count_query = count_query.where(NotificationModel.user_id == user_id)

        query = (
            query
            .order_by(NotificationModel.created_at.desc())
            .offset(offset)
            .limit(size)
        )

        result = await self.db.execute(query)
        total_result = await self.db.execute(count_query)

        return result.scalars().all(), total_result.scalar() or 0

    async def exists_for_loan_today(
            self,
            loan_id: str,
            notification_type: NotificationType,
    ):
        query = (
            select(NotificationModel)
            .where(NotificationModel.loan_id == loan_id)
            .where(NotificationModel.type == notification_type)
            .where(func.date(NotificationModel.created_at) == date.today())
        )

        result = await self.db.execute(query)

        return result.scalar_one_or_none() is not None