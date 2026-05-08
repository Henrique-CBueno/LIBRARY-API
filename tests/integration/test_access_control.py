import pytest

from tests.helpers.auth_helper import auth_headers_for_user
from tests.helpers.author_helper import create_author
from tests.helpers.book_helper import create_book
from tests.helpers.cache_helper import disable_cache
from tests.helpers.loan_helper import create_loan
from tests.helpers.user_helper import create_user
from tests.integration.test_reservations import (
    create_reservation,
    create_unavailable_book,
)


@pytest.fixture(autouse=True)
def disable_access_control_cache(monkeypatch):
    disable_cache(monkeypatch)


async def _user_headers(client):
    user = await create_user(client)
    headers = await auth_headers_for_user(client, user["email"])

    return user, headers


async def test_author_write_endpoints_require_admin(client):
    _, headers = await _user_headers(client)
    author = await create_author(client)

    create_response = await client.post(
        "/authors",
        json={
            "name": "Non Admin Author",
            "biography": "Should be blocked",
        },
        headers=headers,
    )
    update_response = await client.put(
        f"/authors/{author['id']}",
        json={"name": "Blocked"},
        headers=headers,
    )
    delete_response = await client.delete(
        f"/authors/{author['id']}",
        headers=headers,
    )

    assert create_response.status_code == 401
    assert update_response.status_code == 401
    assert delete_response.status_code == 401


async def test_book_write_endpoints_require_admin(client):
    _, headers = await _user_headers(client)
    author = await create_author(client)
    book = await create_book(client, author["id"])

    create_response = await client.post(
        "/books",
        json={
            "title": "Blocked Book",
            "isbn": "blocked-book-isbn",
            "category": "Security",
            "total_copies": 1,
            "author_id": author["id"],
        },
        headers=headers,
    )
    update_response = await client.put(
        f"/books/{book['id']}",
        json={"title": "Blocked"},
        headers=headers,
    )
    delete_response = await client.delete(
        f"/books/{book['id']}",
        headers=headers,
    )

    assert create_response.status_code == 401
    assert update_response.status_code == 401
    assert delete_response.status_code == 401


async def test_user_admin_endpoints_require_admin(client):
    _, headers = await _user_headers(client)
    target = await create_user(client)

    get_response = await client.get(
        f"/users/{target['id']}",
        headers=headers,
    )
    update_response = await client.put(
        f"/users/{target['id']}",
        json={"name": "Blocked"},
        headers=headers,
    )
    delete_response = await client.delete(
        f"/users/{target['id']}",
        headers=headers,
    )
    role_response = await client.put(
        f"/users/{target['id']}/role",
        json={"role": "ADMIN"},
        headers=headers,
    )

    assert get_response.status_code == 401
    assert update_response.status_code == 401
    assert delete_response.status_code == 401
    assert role_response.status_code == 401


async def test_notification_and_report_endpoints_require_admin(client):
    _, headers = await _user_headers(client)

    notifications_response = await client.get(
        "/notifications",
        headers=headers,
    )
    stats_response = await client.get(
        "/reports/stats",
        headers=headers,
    )
    loans_csv_response = await client.get(
        "/reports/loans.csv",
        headers=headers,
    )
    fines_pdf_response = await client.get(
        "/reports/fines.pdf",
        headers=headers,
    )

    assert notifications_response.status_code == 401
    assert stats_response.status_code == 401
    assert loans_csv_response.status_code == 401
    assert fines_pdf_response.status_code == 401


async def test_loan_owner_can_access_own_loan_and_other_user_cannot(client):
    owner, owner_headers = await _user_headers(client)
    _, other_headers = await _user_headers(client)
    loan = await create_loan(client, user_id=owner["id"])

    owner_get_response = await client.get(
        f"/loans/{loan['id']}",
        headers=owner_headers,
    )
    other_get_response = await client.get(
        f"/loans/{loan['id']}",
        headers=other_headers,
    )
    other_return_response = await client.post(
        f"/loans/{loan['id']}/return",
        headers=other_headers,
    )

    assert owner_get_response.status_code == 200
    assert other_get_response.status_code == 401
    assert other_return_response.status_code == 401


async def test_admin_can_access_and_mutate_any_loan(client):
    user = await create_user(client)
    loan = await create_loan(client, user_id=user["id"])

    get_response = await client.get(f"/loans/{loan['id']}")
    cancel_response = await client.post(f"/loans/{loan['id']}/cancel")

    assert get_response.status_code == 200
    assert cancel_response.status_code == 200


async def test_reservation_owner_can_access_own_reservation_and_other_user_cannot(
    client,
):
    owner, owner_headers = await _user_headers(client)
    _, other_headers = await _user_headers(client)
    book = await create_unavailable_book(
        client,
        isbn="access-control-reservation-book",
    )
    reservation = await create_reservation(
        client,
        user_id=owner["id"],
        book_id=book["id"],
        headers=owner_headers,
    )

    owner_get_response = await client.get(
        f"/reservations/{reservation['id']}",
        headers=owner_headers,
    )
    other_get_response = await client.get(
        f"/reservations/{reservation['id']}",
        headers=other_headers,
    )
    other_cancel_response = await client.post(
        f"/reservations/{reservation['id']}/cancel",
        headers=other_headers,
    )

    assert owner_get_response.status_code == 200
    assert other_get_response.status_code == 401
    assert other_cancel_response.status_code == 401


async def test_admin_can_access_and_mutate_any_reservation(client):
    owner, owner_headers = await _user_headers(client)
    book = await create_unavailable_book(
        client,
        isbn="access-control-admin-reservation-book",
    )
    reservation = await create_reservation(
        client,
        user_id=owner["id"],
        book_id=book["id"],
        headers=owner_headers,
    )

    get_response = await client.get(f"/reservations/{reservation['id']}")
    cancel_response = await client.post(
        f"/reservations/{reservation['id']}/cancel"
    )

    assert get_response.status_code == 200
    assert cancel_response.status_code == 200
