from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from app.domain.loans.models.loan_model import LoanModel
from tests.helpers.book_helper import create_book
from tests.helpers.cache_helper import disable_cache
from tests.helpers.loan_helper import create_loan
from tests.helpers.user_helper import create_user


@pytest.fixture(autouse=True)
def disable_loan_cache(monkeypatch):
    disable_cache(monkeypatch)


async def test_should_create_loan(client):
    user = await create_user(client)
    book = await create_book(
        client,
        isbn="loan-create-book",
        total_copies=3,
    )

    response = await client.post(
        "/loans",
        json={
            "user_id": user["id"],
            "book_id": book["id"],
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["user_id"] == user["id"]
    assert body["book_id"] == book["id"]
    assert body["status"] == "ACTIVE"
    assert body["fine_amount"] == 0
    assert body["current_fine_amount"] == 0
    assert body["days_late"] == 0
    assert body["is_overdue"] is False


async def test_should_decrease_available_copies_when_create_loan(client):
    user = await create_user(client)
    book = await create_book(
        client,
        isbn="decrease-stock-book",
        total_copies=3,
    )

    await client.post(
        "/loans",
        json={
            "user_id": user["id"],
            "book_id": book["id"],
        },
    )

    response = await client.get(
        f"/books/{book['id']}",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["available_copies"] == 2


async def test_should_not_create_loan_when_user_not_found(client):
    book = await create_book(
        client,
        isbn="user-not-found-book",
    )

    response = await client.post(
        "/loans",
        json={
            "user_id": "00000000-0000-0000-0000-000000000000",
            "book_id": book["id"],
        },
    )

    assert response.status_code == 404

    body = response.json()

    assert body["error"]["message"] == "User not found"


async def test_should_not_create_loan_when_book_not_found(client):
    user = await create_user(client)

    response = await client.post(
        "/loans",
        json={
            "user_id": user["id"],
            "book_id": "00000000-0000-0000-0000-000000000000",
        },
    )

    assert response.status_code == 404

    body = response.json()

    assert body["error"]["message"] == "Book not found"


async def test_should_not_create_loan_when_book_unavailable(client):
    user_1 = await create_user(client)
    user_2 = await create_user(client)

    book = await create_book(
        client,
        isbn="unavailable-book",
        total_copies=1,
    )

    first_response = await client.post(
        "/loans",
        json={
            "user_id": user_1["id"],
            "book_id": book["id"],
        },
    )

    assert first_response.status_code == 201

    second_response = await client.post(
        "/loans",
        json={
            "user_id": user_2["id"],
            "book_id": book["id"],
        },
    )

    assert second_response.status_code == 400

    body = second_response.json()

    assert body["error"]["message"] == "Book is unavailable"


async def test_should_not_create_more_than_three_active_loans_for_user(client):
    user = await create_user(client)

    for index in range(3):
        book = await create_book(
            client,
            isbn=f"max-active-book-{index}",
        )

        response = await client.post(
            "/loans",
            json={
                "user_id": user["id"],
                "book_id": book["id"],
            },
        )

        assert response.status_code == 201

    fourth_book = await create_book(
        client,
        isbn="max-active-book-4",
    )

    response = await client.post(
        "/loans",
        json={
            "user_id": user["id"],
            "book_id": fourth_book["id"],
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert (
        body["error"]["message"]
        == "User has reached the maximum number of active loans"
    )


async def test_should_get_loan_by_id(client):
    loan = await create_loan(client)

    response = await client.get(
        f"/loans/{loan['id']}",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == loan["id"]
    assert body["status"] == "ACTIVE"


async def test_should_list_loans_paginated(client):
    for index in range(3):
        await create_loan(client)

    response = await client.get(
        "/loans?page=1&size=2",
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["items"]) == 2
    assert body["page"] == 1
    assert body["size"] == 2
    assert body["total"] >= 3


async def test_should_filter_loans_by_user(client):
    user = await create_user(client)

    book = await create_book(
        client,
        isbn="filter-user-book",
    )

    loan = await create_loan(
        client,
        user_id=user["id"],
        book_id=book["id"],
    )

    response = await client.get(
        f"/loans?user_id={user['id']}",
    )

    assert response.status_code == 200

    body = response.json()

    assert any(
        item["id"] == loan["id"]
        for item in body["items"]
    )


async def test_should_filter_loans_by_book(client):
    user = await create_user(client)

    book = await create_book(
        client,
        isbn="filter-book-book",
    )

    loan = await create_loan(
        client,
        user_id=user["id"],
        book_id=book["id"],
    )

    response = await client.get(
        f"/loans?book_id={book['id']}",
    )

    assert response.status_code == 200

    body = response.json()

    assert any(
        item["id"] == loan["id"]
        for item in body["items"]
    )


async def test_should_filter_loans_by_status(client):
    await create_loan(client)

    response = await client.get(
        "/loans?status=ACTIVE",
    )

    assert response.status_code == 200

    body = response.json()

    assert all(
        item["status"] == "ACTIVE"
        for item in body["items"]
    )


async def test_should_list_loans_by_user_endpoint(client):
    user = await create_user(client)

    book = await create_book(
        client,
        isbn="list-by-user-book",
    )

    loan = await create_loan(
        client,
        user_id=user["id"],
        book_id=book["id"],
    )

    response = await client.get(
        f"/loans/users/{user['id']}",
    )

    assert response.status_code == 200

    body = response.json()

    assert any(
        item["id"] == loan["id"]
        for item in body["items"]
    )


async def test_should_return_loan(client):
    loan = await create_loan(client)

    response = await client.post(
        f"/loans/{loan['id']}/return",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == loan["id"]
    assert body["status"] == "RETURNED"
    assert body["fine_amount"] == 0
    assert body["days_late"] == 0


async def test_should_increase_available_copies_when_return_loan(client):
    user = await create_user(client)

    book = await create_book(
        client,
        isbn="return-stock-book",
        total_copies=1,
    )

    loan = await create_loan(
        client,
        user_id=user["id"],
        book_id=book["id"],
    )

    after_loan_response = await client.get(
        f"/books/{book['id']}",
    )

    assert after_loan_response.json()["available_copies"] == 0

    await client.post(
        f"/loans/{loan['id']}/return",
    )

    after_return_response = await client.get(
        f"/books/{book['id']}",
    )

    assert after_return_response.json()["available_copies"] == 1


async def test_should_not_return_already_returned_loan(client):
    loan = await create_loan(client)

    first_response = await client.post(
        f"/loans/{loan['id']}/return",
    )

    assert first_response.status_code == 200

    second_response = await client.post(
        f"/loans/{loan['id']}/return",
    )

    assert second_response.status_code == 404


async def test_should_cancel_loan(client):
    loan = await create_loan(client)

    response = await client.post(
        f"/loans/{loan['id']}/cancel",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == loan["id"]
    assert body["status"] == "CANCELLED"


async def test_should_increase_available_copies_when_cancel_loan(client):
    user = await create_user(client)

    book = await create_book(
        client,
        isbn="cancel-stock-book",
        total_copies=1,
    )

    loan = await create_loan(
        client,
        user_id=user["id"],
        book_id=book["id"],
    )

    await client.post(
        f"/loans/{loan['id']}/cancel",
    )

    book_response = await client.get(
        f"/books/{book['id']}",
    )

    assert book_response.json()["available_copies"] == 1


async def test_should_not_cancel_returned_loan(client):
    loan = await create_loan(client)

    await client.post(
        f"/loans/{loan['id']}/return",
    )

    response = await client.post(
        f"/loans/{loan['id']}/cancel",
    )

    assert response.status_code == 404


async def test_should_update_loan_due_date(client):
    loan = await create_loan(client)

    new_due_date = (
        datetime.utcnow()
        + timedelta(days=20)
    ).isoformat()

    response = await client.put(
        f"/loans/{loan['id']}",
        json={
            "due_date": new_due_date,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == loan["id"]


async def test_should_not_update_returned_loan(client):
    loan = await create_loan(client)

    await client.post(
        f"/loans/{loan['id']}/return",
    )

    response = await client.put(
        f"/loans/{loan['id']}",
        json={
            "due_date": (
                datetime.utcnow()
                + timedelta(days=20)
            ).isoformat()
        },
    )

    assert response.status_code == 400


async def test_should_calculate_current_fine_for_overdue_loan(
    client,
    db_session,
):
    loan = await create_loan(client)

    loan_id = loan["id"]

    result = await db_session.execute(
        select(LoanModel).where(
            LoanModel.id == loan_id
        )
    )

    loan_model = result.scalar_one()

    loan_model.due_date = (
        datetime.utcnow()
        - timedelta(days=5)
    )

    await db_session.commit()

    response = await client.get(
        f"/loans/{loan['id']}",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ACTIVE"
    assert body["is_overdue"] is True
    assert body["days_late"] == 5
    assert body["current_fine_amount"] == 10
    assert body["fine_amount"] == 0


async def test_should_filter_overdue_loans(
    client,
    db_session,
):
    loan = await create_loan(client)

    loan_id = loan["id"]

    result = await db_session.execute(
        select(LoanModel).where(
            LoanModel.id == loan_id
        )
    )

    loan_model = result.scalar_one()

    loan_model.due_date = (
        datetime.utcnow()
        - timedelta(days=3)
    )

    await db_session.commit()

    response = await client.get(
        "/loans?overdue=true",
    )

    assert response.status_code == 200

    body = response.json()

    assert any(
        item["id"] == loan["id"]
        for item in body["items"]
    )


async def test_should_persist_fine_when_return_overdue_loan(
    client,
    db_session,
):
    loan = await create_loan(client)

    loan_id = loan["id"]

    result = await db_session.execute(
        select(LoanModel).where(
            LoanModel.id == loan_id
        )
    )

    loan_model = result.scalar_one()

    loan_model.due_date = (
        datetime.utcnow()
        - timedelta(days=4)
    )

    await db_session.commit()

    payment_response = await client.post(
        f"/loans/{loan['id']}/pay-fine",
    )

    assert payment_response.status_code == 200

    payment_body = payment_response.json()

    assert payment_body["fine_amount"] == 8
    assert payment_body["payment_amount"] == 8
    assert payment_body["fine_paid_amount"] == 8
    assert payment_body["fine_paid_at"] is not None

    response = await client.post(
        f"/loans/{loan['id']}/return",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "RETURNED"
    assert body["days_late"] == 4
    assert body["fine_amount"] == 8
    assert body["fine_paid_amount"] == 8
    assert body["fine_paid_at"] is not None


async def test_should_not_return_overdue_loan_without_paid_fine(
    client,
    db_session,
):
    loan = await create_loan(client)

    result = await db_session.execute(
        select(LoanModel).where(
            LoanModel.id == loan["id"]
        )
    )

    loan_model = result.scalar_one()

    loan_model.due_date = (
        datetime.utcnow()
        - timedelta(days=2)
    )

    await db_session.commit()

    response = await client.post(
        f"/loans/{loan['id']}/return",
    )

    assert response.status_code == 400

    body = response.json()

    assert body["error"]["code"] == "FINE_PAYMENT_REQUIRED"
    assert (
        body["error"]["message"]
        == "Loan fine must be paid before returning the book"
    )


async def test_should_not_pay_fine_when_loan_is_not_overdue(client):
    loan = await create_loan(client)

    response = await client.post(
        f"/loans/{loan['id']}/pay-fine",
    )

    assert response.status_code == 400

    body = response.json()

    assert body["error"]["message"] == "Loan has no fine to pay"


async def test_should_not_return_when_paid_fine_is_less_than_current_fine(
    client,
    db_session,
):
    loan = await create_loan(client)

    result = await db_session.execute(
        select(LoanModel).where(
            LoanModel.id == loan["id"]
        )
    )

    loan_model = result.scalar_one()
    loan_model.due_date = (
        datetime.utcnow()
        - timedelta(days=2)
    )

    await db_session.commit()

    payment_response = await client.post(
        f"/loans/{loan['id']}/pay-fine",
    )

    assert payment_response.status_code == 200
    assert payment_response.json()["fine_paid_amount"] == 4

    loan_model.due_date = (
        datetime.utcnow()
        - timedelta(days=3)
    )

    await db_session.commit()

    response = await client.post(
        f"/loans/{loan['id']}/return",
    )

    assert response.status_code == 400

    body = response.json()

    assert body["error"]["code"] == "FINE_PAYMENT_REQUIRED"
    assert (
        body["error"]["message"]
        == "Loan fine must be paid before returning the book"
    )

async def test_should_renew_loan(client):
    loan = await create_loan(client)

    old_due_date = loan["due_date"]

    response = await client.post(
        f"/loans/{loan['id']}/renew",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == loan["id"]
    assert body["status"] == "ACTIVE"
    assert body["renewal_count"] == 1
    assert body["due_date"] != old_due_date

async def test_should_not_renew_returned_loan(client):
    loan = await create_loan(client)

    await client.post(
        f"/loans/{loan['id']}/return",
    )

    response = await client.post(
        f"/loans/{loan['id']}/renew",
    )

    assert response.status_code == 404

async def test_should_not_renew_overdue_loan(
    client,
    db_session,
):


    loan = await create_loan(client)

    result = await db_session.execute(
        select(LoanModel).where(
            LoanModel.id == loan["id"]
        )
    )

    loan_model = result.scalar_one()

    loan_model.due_date = (
        datetime.utcnow()
        - timedelta(days=1)
    )

    await db_session.commit()

    response = await client.post(
        f"/loans/{loan['id']}/renew",
    )

    assert response.status_code == 400

    body = response.json()

    assert (
        body["error"]["message"]
        == "Overdue loans cannot be renewed"
    )

async def test_should_not_renew_more_than_maximum_allowed(
    client,
):
    loan = await create_loan(client)

    first_response = await client.post(
        f"/loans/{loan['id']}/renew",
    )

    assert first_response.status_code == 200

    second_response = await client.post(
        f"/loans/{loan['id']}/renew",
    )

    assert second_response.status_code == 200

    third_response = await client.post(
        f"/loans/{loan['id']}/renew",
    )

    assert third_response.status_code == 400

    body = third_response.json()

    assert (
        body["error"]["message"]
        == "Loan has reached the maximum number of renewals"
    )
