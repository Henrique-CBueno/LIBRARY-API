from datetime import datetime, timedelta

import pytest

from app.domain.reservation.models.reservation_model import ReservationStatus
from app.domain.reservation.repositories.reservation_repository import (
    ReservationRepository,
)
from tests.factories.author_factory import make_author
from tests.factories.book_factory import make_book
from tests.factories.reservation_factory import make_reservation
from tests.factories.user_factory import make_user


async def seed_reservation_data(db_session):
    user = make_user(email="reservation-user@email.com")
    other_user = make_user(email="other-reservation-user@email.com")
    author = make_author()
    book = make_book(
        author=author,
        author_id=author.id,
        available_copies=0,
    )
    other_book = make_book(
        author=author,
        author_id=author.id,
        available_copies=0,
    )
    now = datetime.utcnow()
    active_reservation = make_reservation(
        user=user,
        user_id=user.id,
        book=book,
        book_id=book.id,
        status=ReservationStatus.ACTIVE,
        created_at=now - timedelta(minutes=2),
    )
    cancelled_reservation = make_reservation(
        user=user,
        user_id=user.id,
        book=other_book,
        book_id=other_book.id,
        status=ReservationStatus.CANCELLED,
        cancelled_at=now,
        created_at=now - timedelta(minutes=1),
    )
    other_reservation = make_reservation(
        user=other_user,
        user_id=other_user.id,
        book=book,
        book_id=book.id,
        status=ReservationStatus.ACTIVE,
        created_at=now,
    )

    db_session.add_all(
        [
            user,
            other_user,
            author,
            book,
            other_book,
            active_reservation,
            cancelled_reservation,
            other_reservation,
        ]
    )
    await db_session.commit()

    return {
        "user": user,
        "other_user": other_user,
        "book": book,
        "other_book": other_book,
        "active_reservation": active_reservation,
        "cancelled_reservation": cancelled_reservation,
        "other_reservation": other_reservation,
    }


@pytest.mark.asyncio
async def test_repository_should_create_reservation(db_session):
    data = await seed_reservation_data(db_session)
    repository = ReservationRepository(db_session)
    reservation = make_reservation(
        user_id=data["other_user"].id,
        book_id=data["other_book"].id,
    )

    created_reservation = await repository.create(reservation)

    assert created_reservation.id == reservation.id
    assert created_reservation.status == ReservationStatus.ACTIVE


@pytest.mark.asyncio
async def test_repository_should_find_reservation_by_id(db_session):
    data = await seed_reservation_data(db_session)
    repository = ReservationRepository(db_session)

    reservation = await repository.find_by_id(
        data["active_reservation"].id
    )

    assert reservation.id == data["active_reservation"].id
    assert reservation.user.id == data["user"].id
    assert reservation.book.id == data["book"].id


@pytest.mark.asyncio
async def test_repository_should_find_active_by_user_and_book(db_session):
    data = await seed_reservation_data(db_session)
    repository = ReservationRepository(db_session)

    active_reservation = await repository.find_active_by_user_and_book(
        user_id=data["user"].id,
        book_id=data["book"].id,
    )
    cancelled_reservation = await repository.find_active_by_user_and_book(
        user_id=data["user"].id,
        book_id=data["other_book"].id,
    )

    assert active_reservation.id == data["active_reservation"].id
    assert cancelled_reservation is None


@pytest.mark.asyncio
async def test_repository_should_check_active_reservation_for_book(db_session):
    data = await seed_reservation_data(db_session)
    repository = ReservationRepository(db_session)

    has_active_for_book = await repository.exists_active_for_book(
        data["book"].id
    )
    has_active_for_other_book = await repository.exists_active_for_book(
        data["other_book"].id
    )

    assert has_active_for_book is True
    assert has_active_for_other_book is False


@pytest.mark.asyncio
async def test_repository_should_list_paginated_without_filters(db_session):
    await seed_reservation_data(db_session)
    repository = ReservationRepository(db_session)

    reservations, total = await repository.list_paginated(
        page=1,
        size=2,
    )

    assert len(reservations) == 2
    assert total == 3


@pytest.mark.asyncio
async def test_repository_should_list_paginated_with_filters(db_session):
    data = await seed_reservation_data(db_session)
    repository = ReservationRepository(db_session)

    reservations, total = await repository.list_paginated(
        page=1,
        size=10,
        user_id=data["user"].id,
        book_id=data["book"].id,
        status=ReservationStatus.ACTIVE,
    )

    assert total == 1
    assert [reservation.id for reservation in reservations] == [
        data["active_reservation"].id
    ]


@pytest.mark.asyncio
async def test_repository_should_update_reservation(db_session):
    data = await seed_reservation_data(db_session)
    repository = ReservationRepository(db_session)
    reservation = data["active_reservation"]

    reservation.status = ReservationStatus.CANCELLED
    reservation.cancelled_at = datetime.utcnow()

    updated_reservation = await repository.update(reservation)

    assert updated_reservation.status == ReservationStatus.CANCELLED
    assert updated_reservation.cancelled_at is not None
