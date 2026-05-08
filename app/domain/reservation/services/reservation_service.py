from datetime import datetime

import structlog

from app.domain.books.repositories.book_repository import BookRepository
from app.domain.reservation.models.reservation_model import ReservationModel, ReservationStatus
from app.domain.reservation.repositories.reservation_repository import ReservationRepository
from app.domain.reservation.schema.reservation_schema import CreateReservationSchema
from app.domain.users.repositories.user_repository import UserRepository
from app.exceptions.base import NotFoundException, BusinessRuleException

logger = structlog.get_logger()


class ReservationService:
    def __init__(
        self,
        repository: ReservationRepository,
        user_repository: UserRepository,
        book_repository: BookRepository,
    ):
        self.repository = repository
        self.user_repository = user_repository
        self.book_repository = book_repository

    async def create_reservation(self, data: CreateReservationSchema):
        user = await self.user_repository.find_by_id(data.user_id)

        if not user:
            raise NotFoundException("User not found")

        book = await self.book_repository.find_by_id(data.book_id)

        if not book:
            raise NotFoundException("Book not found")

        if book.available_copies > 0:
            raise BusinessRuleException(
                "Book is available and does not need reservation"
            )

        existing_reservation = await self.repository.find_active_by_user_and_book(
            data.user_id,
            data.book_id,
        )

        if existing_reservation:
            raise BusinessRuleException(
                "User already has an active reservation for this book"
            )

        reservation = ReservationModel(
            user_id=data.user_id,
            book_id=data.book_id,
            status=ReservationStatus.ACTIVE,
        )

        created = await self.repository.create(reservation)

        logger.info(
            "reservation_created",
            reservation_id=str(created.id),
            user_id=str(created.user_id),
            book_id=str(created.book_id),
        )

        return created

    async def cancel_reservation(self, reservation_id: str):
        reservation = await self.repository.find_by_id(reservation_id)

        if not reservation:
            raise NotFoundException("Reservation not found")

        if reservation.status != ReservationStatus.ACTIVE:
            raise BusinessRuleException(
                "Only active reservations can be cancelled"
            )

        reservation.status = ReservationStatus.CANCELLED
        reservation.cancelled_at = datetime.utcnow()

        updated = await self.repository.update(reservation)

        logger.info(
            "reservation_cancelled",
            reservation_id=str(updated.id),
        )

        return {
            "id": str(updated.id),
            "status": updated.status,
            "cancelled_at": updated.cancelled_at,
        }

    async def list_paginated(
        self,
        page: int,
        size: int,
        user_id: str | None = None,
        book_id: str | None = None,
        status: ReservationStatus | None = None,
    ):
        reservations, total = await self.repository.list_paginated(
            page=page,
            size=size,
            user_id=user_id,
            book_id=book_id,
            status=status,
        )

        return {
            "items": reservations,
            "total": total,
            "page": page,
            "size": size,
        }

    async def get_reservation(self, reservation_id: str):
        reservation = await self.repository.find_by_id(reservation_id)

        if not reservation:
            raise NotFoundException("Reservation not found")

        return reservation