from datetime import datetime

import structlog

from app.config.observability.metrics import reservations_created_total, reservations_cancelled_total
from app.domain.books.repositories.book_repository import BookRepository
from app.domain.reservation.models.reservation_model import ReservationModel, ReservationStatus
from app.domain.reservation.repositories.reservation_repository import ReservationRepository
from app.domain.reservation.schema.reservation_schema import CreateReservationSchema
from app.domain.users.repositories.user_repository import UserRepository
from app.events.bus import EventBus
from app.events.reservations.events import (
    ReservationCancelledEvent,
    ReservationCreatedEvent,
)
from app.exceptions.base import NotFoundException, BusinessRuleException

logger = structlog.get_logger()


class ReservationService:
    def __init__(
        self,
        repository: ReservationRepository,
        user_repository: UserRepository,
        book_repository: BookRepository,
        event_bus: EventBus,
    ):
        self.repository = repository
        self.user_repository = user_repository
        self.book_repository = book_repository
        self.event_bus = event_bus

    async def create_reservation(self, data: CreateReservationSchema, user_id: str):
        user = await self.user_repository.find_by_id(user_id)

        if not user:
            raise NotFoundException("Usuário não encontrado")

        book = await self.book_repository.find_by_id(data.book_id)

        if not book:
            raise NotFoundException("Livro não encontrado")

        if book.available_copies > 0:
            raise BusinessRuleException(
                "O livro está disponível e não precisa de reserva"
            )

        existing_reservation = await self.repository.find_active_by_user_and_book(
            user_id,
            data.book_id,
        )

        if existing_reservation:
            raise BusinessRuleException(
                "O usuário já possui uma reserva ativa para este livro"
            )

        reservation = ReservationModel(
            user_id=user_id,
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

        await self.event_bus.publish(
            ReservationCreatedEvent(
                occurred_at=datetime.utcnow(),
                reservation_id=created.id,
                user_id=created.user_id,
                book_id=created.book_id,
            )
        )

        reservations_created_total.inc()

        return created

    async def cancel_reservation(self, reservation_id: str):
        reservation = await self.repository.find_by_id(reservation_id)

        if not reservation:
            raise NotFoundException("Reserva não encontrada")

        if reservation.status != ReservationStatus.ACTIVE:
            raise BusinessRuleException(
                "Apenas reservas ativas podem ser canceladas"
            )

        reservation.status = ReservationStatus.CANCELLED
        reservation.cancelled_at = datetime.utcnow()

        updated = await self.repository.update(reservation)

        logger.info(
            "reservation_cancelled",
            reservation_id=str(updated.id),
        )

        await self.event_bus.publish(
            ReservationCancelledEvent(
                occurred_at=datetime.utcnow(),
                reservation_id=updated.id,
                user_id=updated.user_id,
                book_id=updated.book_id,
            )
        )

        reservations_cancelled_total.inc()

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
            raise NotFoundException("Reserva não encontrada")

        return reservation
