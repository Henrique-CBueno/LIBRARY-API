import pytest

from tests.helpers.cache_helper import disable_cache
from tests.helpers.book_helper import create_book
from tests.helpers.loan_helper import create_loan
from tests.helpers.auth_helper import auth_headers_for_user
from tests.helpers.user_helper import create_user


@pytest.fixture(autouse=True)
def disable_reservation_notification_cache(monkeypatch):
    disable_cache(monkeypatch)


async def test_should_notify_when_reservation_is_created(client):
    borrower = await create_user(client)
    waiting_user = await create_user(client)
    book = await create_book(
        client,
        isbn="reservation-notification-create-book",
        total_copies=1,
    )

    await create_loan(
        client,
        user_id=borrower["id"],
        book_id=book["id"],
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
        and item["type"] == "RESERVATION_CREATED"
        for item in notifications
    )


async def test_should_notify_when_reservation_is_cancelled(client):
    borrower = await create_user(client)
    waiting_user = await create_user(client)
    book = await create_book(
        client,
        isbn="reservation-notification-cancel-book",
        total_copies=1,
    )

    await create_loan(
        client,
        user_id=borrower["id"],
        book_id=book["id"],
    )

    create_response = await client.post(
        "/reservations",
        json={
            "user_id": waiting_user["id"],
            "book_id": book["id"],
        },
        headers=await auth_headers_for_user(client, waiting_user["email"]),
    )

    reservation_id = create_response.json()["id"]

    response = await client.post(
        f"/reservations/{reservation_id}/cancel",
    )

    assert response.status_code == 200

    notifications_response = await client.get(
        f"/notifications?user_id={waiting_user['id']}"
    )

    assert notifications_response.status_code == 200

    notifications = notifications_response.json()["items"]

    assert any(
        item["reservation_id"] == reservation_id
        and item["type"] == "RESERVATION_CANCELLED"
        for item in notifications
    )
