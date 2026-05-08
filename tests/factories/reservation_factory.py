from datetime import datetime

import uuid6 as uuid

from app.domain.reservation.models.reservation_model import (
    ReservationModel,
    ReservationStatus,
)


def make_reservation(
    user_id: str | None = None,
    book_id: str | None = None,
    status: ReservationStatus = ReservationStatus.ACTIVE,
    created_at: datetime | None = None,
    cancelled_at: datetime | None = None,
    fulfilled_at: datetime | None = None,
    user=None,
    book=None,
):
    reservation = ReservationModel(
        id=str(uuid.uuid7()),
        user_id=user_id or str(uuid.uuid7()),
        book_id=book_id or str(uuid.uuid7()),
        status=status,
        created_at=created_at or datetime.utcnow(),
        cancelled_at=cancelled_at,
        fulfilled_at=fulfilled_at,
    )

    if user is not None:
        reservation.user = user

    if book is not None:
        reservation.book = book

    return reservation
