import pytest

from tests.helpers.book_helper import create_book
from tests.helpers.auth_helper import auth_headers_for_user
from tests.helpers.cache_helper import disable_cache
from tests.helpers.loan_helper import create_loan
from tests.helpers.user_helper import create_user


@pytest.fixture(autouse=True)
def disable_reservation_cache(monkeypatch):
    disable_cache(monkeypatch)


async def create_unavailable_book(client, isbn: str):
    borrower = await create_user(client)
    book = await create_book(
        client,
        isbn=isbn,
        total_copies=1,
    )

    await create_loan(
        client,
        user_id=borrower["id"],
        book_id=book["id"],
    )

    return book


async def create_reservation(
    client,
    user_id: str | None = None,
    book_id: str | None = None,
    isbn: str = "reservation-helper-book",
    headers: dict | None = None,
):
    waiting_user = None

    if not user_id:
        waiting_user = await create_user(client)
        user_id = waiting_user["id"]
        headers = await auth_headers_for_user(client, waiting_user["email"])

    if not book_id:
        book = await create_unavailable_book(client, isbn)
        book_id = book["id"]

    response = await client.post(
        "/reservations",
        json={
            "user_id": user_id,
            "book_id": book_id,
        },
        headers=headers,
    )

    assert response.status_code == 201

    return response.json()


async def test_should_create_reservation_when_book_is_unavailable(client):
    waiting_user = await create_user(client)
    book = await create_unavailable_book(
        client,
        isbn="reservation-unavailable-book",
    )

    response = await client.post(
        "/reservations",
        json={
            "user_id": waiting_user["id"],
            "book_id": book["id"],
        },
        headers=await auth_headers_for_user(client, waiting_user["email"]),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["user_id"] == waiting_user["id"]
    assert body["book_id"] == book["id"]
    assert body["status"] == "ACTIVE"
    assert body["cancelled_at"] is None
    assert body["fulfilled_at"] is None


async def test_should_create_notification_when_reservation_is_created(client):
    waiting_user = await create_user(client)
    book = await create_unavailable_book(
        client,
        isbn="reservation-created-notification-book",
    )

    response = await client.post(
        "/reservations",
        json={
            "user_id": waiting_user["id"],
            "book_id": book["id"],
        },
        headers=await auth_headers_for_user(client, waiting_user["email"]),
    )

    assert response.status_code == 201

    reservation = response.json()

    notifications_response = await client.get(
        f"/notifications?user_id={waiting_user['id']}"
    )

    assert notifications_response.status_code == 200

    notifications = notifications_response.json()["items"]

    assert any(
        item["reservation_id"] == reservation["id"]
        and item["loan_id"] is None
        and item["type"] == "RESERVATION_CREATED"
        for item in notifications
    )


async def test_should_not_create_reservation_when_book_is_available(client):
    user = await create_user(client)
    book = await create_book(
        client,
        isbn="reservation-available-book",
        total_copies=1,
    )

    response = await client.post(
        "/reservations",
        json={
            "user_id": user["id"],
            "book_id": book["id"],
        },
        headers=await auth_headers_for_user(client, user["email"]),
    )

    assert response.status_code == 400

    body = response.json()

    assert (
        body["error"]["message"]
        == "Book is available and does not need reservation"
    )


async def test_should_create_reservation_for_authenticated_user(client):
    user = await create_user(client)
    book = await create_unavailable_book(
        client,
        isbn="reservation-authenticated-user-book",
    )

    response = await client.post(
        "/reservations",
        json={
            "user_id": "00000000-0000-0000-0000-000000000000",
            "book_id": book["id"],
        },
        headers=await auth_headers_for_user(client, user["email"]),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["user_id"] == user["id"]


async def test_should_not_create_reservation_when_book_not_found(client):
    user = await create_user(client)

    response = await client.post(
        "/reservations",
        json={
            "user_id": user["id"],
            "book_id": "00000000-0000-0000-0000-000000000000",
        },
        headers=await auth_headers_for_user(client, user["email"]),
    )

    assert response.status_code == 404

    body = response.json()

    assert body["error"]["message"] == "Book not found"


async def test_should_not_create_duplicate_active_reservation(client):
    waiting_user = await create_user(client)
    book = await create_unavailable_book(
        client,
        isbn="reservation-duplicate-book",
    )
    payload = {
        "user_id": waiting_user["id"],
        "book_id": book["id"],
    }

    first_response = await client.post(
        "/reservations",
        json=payload,
        headers=await auth_headers_for_user(client, waiting_user["email"]),
    )
    second_response = await client.post(
        "/reservations",
        json=payload,
        headers=await auth_headers_for_user(client, waiting_user["email"]),
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 400

    body = second_response.json()

    assert (
        body["error"]["message"]
        == "User already has an active reservation for this book"
    )


async def test_should_get_reservation_by_id(client):
    reservation = await create_reservation(
        client,
        isbn="reservation-get-book",
    )

    response = await client.get(
        f"/reservations/{reservation['id']}",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == reservation["id"]
    assert body["status"] == "ACTIVE"


async def test_should_return_404_when_reservation_not_found(client):
    response = await client.get(
        "/reservations/00000000-0000-0000-0000-000000000000",
    )

    assert response.status_code == 404

    body = response.json()

    assert body["error"]["message"] == "Reservation not found"


async def test_should_list_reservations_paginated(client):
    for index in range(3):
        await create_reservation(
            client,
            isbn=f"reservation-list-book-{index}",
        )

    response = await client.get(
        "/reservations?page=1&size=2",
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["items"]) == 2
    assert body["page"] == 1
    assert body["size"] == 2
    assert body["total"] >= 3


async def test_should_filter_reservations_by_user(client):
    waiting_user = await create_user(client)
    book = await create_unavailable_book(
        client,
        isbn="reservation-filter-user-book",
    )
    reservation = await create_reservation(
        client,
        user_id=waiting_user["id"],
        book_id=book["id"],
        headers=await auth_headers_for_user(client, waiting_user["email"]),
    )

    response = await client.get(
        f"/reservations?user_id={waiting_user['id']}",
    )

    assert response.status_code == 200

    body = response.json()

    assert any(
        item["id"] == reservation["id"]
        for item in body["items"]
    )


async def test_should_filter_reservations_by_book(client):
    waiting_user = await create_user(client)
    book = await create_unavailable_book(
        client,
        isbn="reservation-filter-book",
    )
    reservation = await create_reservation(
        client,
        user_id=waiting_user["id"],
        book_id=book["id"],
        headers=await auth_headers_for_user(client, waiting_user["email"]),
    )

    response = await client.get(
        f"/reservations?book_id={book['id']}",
    )

    assert response.status_code == 200

    body = response.json()

    assert any(
        item["id"] == reservation["id"]
        for item in body["items"]
    )


async def test_should_filter_reservations_by_status(client):
    active_reservation = await create_reservation(
        client,
        isbn="reservation-filter-active-book",
    )
    cancelled_reservation = await create_reservation(
        client,
        isbn="reservation-filter-cancelled-book",
    )

    await client.post(
        f"/reservations/{cancelled_reservation['id']}/cancel",
        headers=await auth_headers_for_user(
            client,
            cancelled_reservation["user"]["email"],
        ) if "user" in cancelled_reservation else None,
    )

    response = await client.get(
        "/reservations?status=ACTIVE",
    )

    assert response.status_code == 200

    body = response.json()

    assert any(
        item["id"] == active_reservation["id"]
        for item in body["items"]
    )
    assert all(
        item["status"] == "ACTIVE"
        for item in body["items"]
    )


async def test_should_cancel_reservation(client):
    reservation = await create_reservation(
        client,
        isbn="reservation-cancel-book",
    )

    response = await client.post(
        f"/reservations/{reservation['id']}/cancel",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == reservation["id"]
    assert body["status"] == "CANCELLED"
    assert body["cancelled_at"] is not None


async def test_should_create_notification_when_reservation_is_cancelled(client):
    waiting_user = await create_user(client)
    book = await create_unavailable_book(
        client,
        isbn="reservation-cancelled-notification-book",
    )
    reservation = await create_reservation(
        client,
        user_id=waiting_user["id"],
        book_id=book["id"],
        headers=await auth_headers_for_user(client, waiting_user["email"]),
    )

    response = await client.post(
        f"/reservations/{reservation['id']}/cancel",
    )

    assert response.status_code == 200

    notifications_response = await client.get(
        f"/notifications?user_id={waiting_user['id']}"
    )

    assert notifications_response.status_code == 200

    notifications = notifications_response.json()["items"]

    assert any(
        item["reservation_id"] == reservation["id"]
        and item["loan_id"] is None
        and item["type"] == "RESERVATION_CANCELLED"
        for item in notifications
    )


async def test_should_not_cancel_reservation_twice(client):
    reservation = await create_reservation(
        client,
        isbn="reservation-cancel-twice-book",
    )

    first_response = await client.post(
        f"/reservations/{reservation['id']}/cancel",
    )
    second_response = await client.post(
        f"/reservations/{reservation['id']}/cancel",
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 400

    body = second_response.json()

    assert (
        body["error"]["message"]
        == "Only active reservations can be cancelled"
    )


async def test_should_allow_new_reservation_after_cancelled_previous_one(
    client,
):
    waiting_user = await create_user(client)
    book = await create_unavailable_book(
        client,
        isbn="reservation-recreate-after-cancel-book",
    )

    first_reservation = await create_reservation(
        client,
        user_id=waiting_user["id"],
        book_id=book["id"],
        headers=await auth_headers_for_user(client, waiting_user["email"]),
    )

    cancel_response = await client.post(
        f"/reservations/{first_reservation['id']}/cancel",
    )

    second_response = await client.post(
        "/reservations",
        json={
            "user_id": waiting_user["id"],
            "book_id": book["id"],
        },
        headers=await auth_headers_for_user(client, waiting_user["email"]),
    )

    assert cancel_response.status_code == 200
    assert second_response.status_code == 201
    assert second_response.json()["status"] == "ACTIVE"
