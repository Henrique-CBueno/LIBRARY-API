from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from app.domain.notifications.models.notification_model import NotificationType
from app.events.reservations.events import (
    ReservationCancelledEvent,
    ReservationCreatedEvent,
)
from app.events.reservations.handlers.reservation_notification_handler import (
    ReservationCancelledNotificationHandler,
    ReservationCreatedNotificationHandler,
)


@pytest.mark.asyncio
async def test_reservation_created_handler_should_send_notification():
    notification_service = AsyncMock()
    handler = ReservationCreatedNotificationHandler(
        notification_service
    )
    event = ReservationCreatedEvent(
        occurred_at=datetime.utcnow(),
        reservation_id="reservation-id",
        user_id="user-id",
        book_id="book-id",
    )

    await handler.handle(event)

    notification_service.send_notification.assert_awaited_once()
    kwargs = notification_service.send_notification.await_args.kwargs

    assert kwargs["user_id"] == "user-id"
    assert kwargs["reservation_id"] == "reservation-id"
    assert (
        kwargs["notification_type"]
        == NotificationType.RESERVATION_CREATED
    )


@pytest.mark.asyncio
async def test_reservation_cancelled_handler_should_send_notification():
    notification_service = AsyncMock()
    handler = ReservationCancelledNotificationHandler(
        notification_service
    )
    event = ReservationCancelledEvent(
        occurred_at=datetime.utcnow(),
        reservation_id="reservation-id",
        user_id="user-id",
        book_id="book-id",
    )

    await handler.handle(event)

    notification_service.send_notification.assert_awaited_once_with(
        user_id="user-id",
        reservation_id="reservation-id",
        notification_type=NotificationType.RESERVATION_CANCELLED,
        message="Reserva cancelada com sucesso.",
    )
