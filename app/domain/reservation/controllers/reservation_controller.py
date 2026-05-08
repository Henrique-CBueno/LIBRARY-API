from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.security.dependencies import get_current_user
from app.domain.books.repositories.book_repository import BookRepository
from app.domain.reservation.models.reservation_model import ReservationStatus
from app.domain.reservation.repositories.reservation_repository import (
    ReservationRepository,
)
from app.domain.reservation.schema.reservation_schema import (
    CancelReservationResponseSchema,
    CreateReservationSchema,
    ReservationResponseSchema,
)
from app.domain.reservation.services.reservation_service import ReservationService
from app.domain.users.enums.user_role import UserRole
from app.domain.users.models.user_model import UserModel
from app.domain.users.repositories.user_repository import UserRepository
from app.events.bus import EventBus
from app.events.registrar_handlers import register_event_handlers
from app.exceptions.base import UnauthorizedException
from app.infra.database.session import get_db
from app.infra.middleware.rate_limit import limiter
from app.infra.padronize.pagination.schemas import PaginatedResponse

router = APIRouter(
    prefix="/reservations",
    tags=["Reservations"],
)


def get_reservation_service(
    db: AsyncSession = Depends(get_db),
):
    event_bus = EventBus()
    register_event_handlers(event_bus, db)

    return ReservationService(
        repository=ReservationRepository(db),
        user_repository=UserRepository(db),
        book_repository=BookRepository(db),
        event_bus=event_bus,
    )


@router.post(
    "",
    response_model=ReservationResponseSchema,
    status_code=201,
    summary="Create reservation",
)
@limiter.limit("20/minute")
async def create_reservation(
    request: Request,
    data: CreateReservationSchema,
    user: UserModel = Depends(get_current_user),
    service: ReservationService = Depends(get_reservation_service),
):

    return await service.create_reservation(data, user.id)


@router.get(
    "",
    response_model=PaginatedResponse[ReservationResponseSchema],
    summary="List reservations",
)
async def list_reservations(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    user_id: str | None = Query(None),
    book_id: str | None = Query(None),
    status: ReservationStatus | None = Query(None),
    service: ReservationService = Depends(get_reservation_service),
    user: UserModel = Depends(get_current_user),
):
    if user.role != UserRole.ADMIN:
        if user_id != user.id:
            raise UnauthorizedException("You can only list your reservations")

    return await service.list_paginated(
        page=page,
        size=size,
        user_id=user_id,
        book_id=book_id,
        status=status,
    )


@router.get(
    "/{reservation_id}",
    response_model=ReservationResponseSchema,
    summary="Get reservation",
)
async def get_reservation(
    reservation_id: str,
    service: ReservationService = Depends(get_reservation_service),
    user: UserModel = Depends(get_current_user),
):
    reservation = await service.get_reservation(reservation_id)

    if user.role != UserRole.ADMIN:
        if str(reservation.user_id) != str(user.id):
            raise UnauthorizedException("You can only list your reservations")

    return reservation


@router.post(
    "/{reservation_id}/cancel",
    response_model=CancelReservationResponseSchema,
    summary="Cancel reservation",
)
async def cancel_reservation(
    reservation_id: str,
    service: ReservationService = Depends(get_reservation_service),
    user: UserModel = Depends(get_current_user),
):
    reservation = await service.get_reservation(reservation_id)

    if user.role != UserRole.ADMIN:
        if str(reservation.user_id) != str(user.id):
            raise UnauthorizedException("You can only cancel your reservations")

    return await service.cancel_reservation(reservation_id)
