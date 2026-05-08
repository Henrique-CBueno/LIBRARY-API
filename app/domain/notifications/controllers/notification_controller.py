from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.notifications.repositories.notification_repository import NotificationRepository
from app.domain.notifications.schemas.notification_schema import NotificationResponseSchema
from app.domain.notifications.services.notification_service import NotificationService
from app.infra.database.session import get_db
from app.infra.padronize.pagination.schemas import PaginatedResponse

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


def get_notification_service(
    db: AsyncSession = Depends(get_db),
):
    repository = NotificationRepository(db)

    return NotificationService(repository)


@router.get(
    "",
    response_model=PaginatedResponse[NotificationResponseSchema],
    summary="List notifications",
)
async def list_notifications(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    user_id: str | None = Query(None),
    service: NotificationService = Depends(get_notification_service),
):
    return await service.list_paginated(
        page=page,
        size=size,
        user_id=user_id,
    )