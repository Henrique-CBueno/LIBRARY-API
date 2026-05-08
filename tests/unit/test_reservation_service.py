from unittest.mock import AsyncMock

import pytest

from app.domain.reservation.models.reservation_model import ReservationStatus
from app.domain.reservation.schema.reservation_schema import CreateReservationSchema
from app.domain.reservation.services.reservation_service import ReservationService
from app.events.reservations.events import (
    ReservationCancelledEvent,
    ReservationCreatedEvent,
)
from app.exceptions.base import BusinessRuleException, NotFoundException
from tests.factories.book_factory import make_book
from tests.factories.reservation_factory import make_reservation
from tests.factories.user_factory import make_user


def make_service():
    repository = AsyncMock()
    user_repository = AsyncMock()
    book_repository = AsyncMock()
    event_bus = AsyncMock()

    return (
        ReservationService(
            repository=repository,
            user_repository=user_repository,
            book_repository=book_repository,
            event_bus=event_bus,
        ),
        repository,
        user_repository,
        book_repository,
        event_bus,
    )


@pytest.mark.asyncio
async def test_should_create_reservation_for_unavailable_book():
    (
        service,
        repository,
        user_repository,
        book_repository,
        event_bus,
    ) = make_service()
    user = make_user()
    book = make_book(available_copies=0)
    reservation = make_reservation(
        user_id=user.id,
        book_id=book.id,
    )
    user_repository.find_by_id.return_value = user
    book_repository.find_by_id.return_value = book
    repository.find_active_by_user_and_book.return_value = None
    repository.create.return_value = reservation

    response = await service.create_reservation(
        CreateReservationSchema(
            book_id=book.id,
        ),
        user.id,
    )

    saved_reservation = repository.create.await_args.args[0]
    published_event = event_bus.publish.await_args.args[0]

    assert response == reservation
    assert saved_reservation.user_id == user.id
    assert saved_reservation.book_id == book.id
    assert saved_reservation.status == ReservationStatus.ACTIVE
    assert isinstance(published_event, ReservationCreatedEvent)
    assert published_event.reservation_id == reservation.id


@pytest.mark.asyncio
async def test_should_not_create_reservation_when_user_not_found():
    service, repository, user_repository, _, event_bus = make_service()
    user_repository.find_by_id.return_value = None

    with pytest.raises(NotFoundException):
        await service.create_reservation(
            CreateReservationSchema(
                book_id="book-id",
            ),
            "missing-user",
        )

    repository.create.assert_not_awaited()
    event_bus.publish.assert_not_awaited()


@pytest.mark.asyncio
async def test_should_not_create_reservation_when_book_not_found():
    (
        service,
        repository,
        user_repository,
        book_repository,
        event_bus,
    ) = make_service()
    user_repository.find_by_id.return_value = make_user()
    book_repository.find_by_id.return_value = None

    with pytest.raises(NotFoundException):
        await service.create_reservation(
            CreateReservationSchema(
                book_id="missing-book",
            ),
            "user-id",
        )

    repository.create.assert_not_awaited()
    event_bus.publish.assert_not_awaited()


@pytest.mark.asyncio
async def test_should_not_create_reservation_when_book_is_available():
    (
        service,
        repository,
        user_repository,
        book_repository,
        event_bus,
    ) = make_service()
    user_repository.find_by_id.return_value = make_user()
    book_repository.find_by_id.return_value = make_book(available_copies=1)

    with pytest.raises(BusinessRuleException):
        await service.create_reservation(
            CreateReservationSchema(
                book_id="book-id",
            ),
            "user-id",
        )

    repository.find_active_by_user_and_book.assert_not_awaited()
    repository.create.assert_not_awaited()
    event_bus.publish.assert_not_awaited()


@pytest.mark.asyncio
async def test_should_not_create_duplicate_active_reservation():
    (
        service,
        repository,
        user_repository,
        book_repository,
        event_bus,
    ) = make_service()
    user = make_user()
    book = make_book(available_copies=0)
    user_repository.find_by_id.return_value = user
    book_repository.find_by_id.return_value = book
    repository.find_active_by_user_and_book.return_value = make_reservation(
        user_id=user.id,
        book_id=book.id,
    )

    with pytest.raises(BusinessRuleException):
        await service.create_reservation(
            CreateReservationSchema(
                book_id=book.id,
            ),
            user.id,
        )

    repository.create.assert_not_awaited()
    event_bus.publish.assert_not_awaited()


@pytest.mark.asyncio
async def test_should_cancel_active_reservation():
    service, repository, _, _, event_bus = make_service()
    reservation = make_reservation()
    repository.find_by_id.return_value = reservation
    repository.update.return_value = reservation

    response = await service.cancel_reservation(reservation.id)

    published_event = event_bus.publish.await_args.args[0]

    assert reservation.status == ReservationStatus.CANCELLED
    assert reservation.cancelled_at is not None
    assert response["id"] == str(reservation.id)
    assert response["status"] == ReservationStatus.CANCELLED
    assert isinstance(published_event, ReservationCancelledEvent)
    assert published_event.reservation_id == reservation.id
    repository.update.assert_awaited_once_with(reservation)


@pytest.mark.asyncio
async def test_should_not_cancel_missing_reservation():
    service, repository, _, _, event_bus = make_service()
    repository.find_by_id.return_value = None

    with pytest.raises(NotFoundException):
        await service.cancel_reservation("missing-reservation")

    repository.update.assert_not_awaited()
    event_bus.publish.assert_not_awaited()


@pytest.mark.asyncio
async def test_should_not_cancel_non_active_reservation():
    service, repository, _, _, event_bus = make_service()
    repository.find_by_id.return_value = make_reservation(
        status=ReservationStatus.CANCELLED,
    )

    with pytest.raises(BusinessRuleException):
        await service.cancel_reservation("reservation-id")

    repository.update.assert_not_awaited()
    event_bus.publish.assert_not_awaited()


@pytest.mark.asyncio
async def test_should_list_paginated_reservations():
    service, repository, _, _, _ = make_service()
    reservations = [make_reservation()]
    repository.list_paginated.return_value = (
        reservations,
        1,
    )

    response = await service.list_paginated(
        page=2,
        size=5,
        user_id="user-id",
        book_id="book-id",
        status=ReservationStatus.ACTIVE,
    )

    assert response["items"] == reservations
    assert response["total"] == 1
    assert response["page"] == 2
    assert response["size"] == 5
    repository.list_paginated.assert_awaited_once_with(
        page=2,
        size=5,
        user_id="user-id",
        book_id="book-id",
        status=ReservationStatus.ACTIVE,
    )


@pytest.mark.asyncio
async def test_should_get_reservation():
    service, repository, _, _, _ = make_service()
    reservation = make_reservation()
    repository.find_by_id.return_value = reservation

    response = await service.get_reservation(reservation.id)

    assert response == reservation
    repository.find_by_id.assert_awaited_once_with(reservation.id)


@pytest.mark.asyncio
async def test_should_raise_not_found_when_getting_missing_reservation():
    service, repository, _, _, _ = make_service()
    repository.find_by_id.return_value = None

    with pytest.raises(NotFoundException):
        await service.get_reservation("missing-reservation")
