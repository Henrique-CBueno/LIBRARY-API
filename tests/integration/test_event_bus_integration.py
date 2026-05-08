import pytest

from tests.helpers.book_helper import create_book
from tests.helpers.cache_helper import disable_cache
from tests.helpers.loan_helper import create_loan
from tests.helpers.user_helper import create_user


@pytest.fixture(autouse=True)
def disable_event_bus_cache(monkeypatch):
    disable_cache(monkeypatch)


def _assert_notification_for_type(body, expected_type):
    types = {item["type"] for item in body["items"]}

    assert expected_type in types


async def _get_notifications(client, user_id: str):
    response = await client.get(
        f"/notifications?user_id={user_id}"
    )

    assert response.status_code == 200

    return response.json()


async def test_should_create_notification_on_loan_create(client):
    user = await create_user(client)
    book = await create_book(
        client,
        isbn="eventbus-create-book",
        total_copies=1,
    )

    response = await client.post(
        "/loans",
        json={
            "user_id": user["id"],
            "book_id": book["id"],
        },
    )

    assert response.status_code == 201

    loan = response.json()

    body = await _get_notifications(
        client,
        user["id"],
    )

    assert body["total"] == 1

    item = body["items"][0]

    assert item["user_id"] == user["id"]
    assert item["loan_id"] == loan["id"]
    assert item["type"] == "LOAN_CREATED"
    assert item["status"] == "SENT"
    assert item["channel"] == "EMAIL_FAKE"
    assert item["message"]


async def test_should_create_notification_on_loan_return(client):
    loan = await create_loan(client)

    response = await client.post(
        f"/loans/{loan['id']}/return",
    )

    assert response.status_code == 200

    body = await _get_notifications(
        client,
        loan["user_id"],
    )

    assert body["total"] == 2
    _assert_notification_for_type(
        body,
        "LOAN_RETURNED",
    )


async def test_should_create_notification_on_loan_cancel(client):
    loan = await create_loan(client)

    response = await client.post(
        f"/loans/{loan['id']}/cancel",
    )

    assert response.status_code == 200

    body = await _get_notifications(
        client,
        loan["user_id"],
    )

    assert body["total"] == 2
    _assert_notification_for_type(
        body,
        "LOAN_CANCELLED",
    )
