from datetime import datetime, timedelta

import pytest

from app.domain.loans.models.loan_model import LoanStatus
from app.domain.loans.repositories.loan_repository import LoanRepository
from tests.factories.author_factory import make_author
from tests.factories.book_factory import make_book
from tests.factories.loan_factory import make_loan
from tests.factories.user_factory import make_user


async def seed_loan_data(db_session):
    user = make_user(email="loan-user@email.com")
    other_user = make_user(email="other-loan-user@email.com")
    author = make_author()
    book = make_book(
        author=author,
        author_id=author.id,
        available_copies=2,
    )
    other_book = make_book(
        author=author,
        author_id=author.id,
        available_copies=1,
    )
    inactive_book = make_book(
        author=author,
        author_id=author.id,
        is_active=False,
    )
    now = datetime.utcnow()
    active_loan = make_loan(
        user_id=user.id,
        book_id=book.id,
        loan_date=now,
        due_date=now + timedelta(days=5),
        status=LoanStatus.ACTIVE,
    )
    overdue_loan = make_loan(
        user_id=user.id,
        book_id=other_book.id,
        loan_date=now - timedelta(days=20),
        due_date=now - timedelta(days=3),
        status=LoanStatus.ACTIVE,
    )
    returned_loan = make_loan(
        user_id=other_user.id,
        book_id=book.id,
        loan_date=now - timedelta(days=10),
        due_date=now - timedelta(days=1),
        returned_at=now,
        status=LoanStatus.RETURNED,
        fine_amount=2,
    )

    db_session.add_all(
        [
            user,
            other_user,
            author,
            book,
            other_book,
            inactive_book,
            active_loan,
            overdue_loan,
            returned_loan,
        ]
    )
    await db_session.commit()

    return {
        "user": user,
        "other_user": other_user,
        "book": book,
        "other_book": other_book,
        "inactive_book": inactive_book,
        "active_loan": active_loan,
        "overdue_loan": overdue_loan,
        "returned_loan": returned_loan,
    }


@pytest.mark.asyncio
async def test_repository_should_create_loan(db_session):
    data = await seed_loan_data(db_session)
    repository = LoanRepository(db_session)
    loan = make_loan(
        user_id=data["user"].id,
        book_id=data["book"].id,
    )

    created_loan = await repository.create(loan)

    assert created_loan.id == loan.id
    assert created_loan.status == LoanStatus.ACTIVE


@pytest.mark.asyncio
async def test_repository_should_find_loan_by_id(db_session):
    data = await seed_loan_data(db_session)
    repository = LoanRepository(db_session)

    loan = await repository.find_by_id(
        data["active_loan"].id
    )

    assert loan.id == data["active_loan"].id
    assert loan.book.id == data["book"].id
    assert loan.user.id == data["user"].id


@pytest.mark.asyncio
async def test_repository_should_count_active_loans_by_user(db_session):
    data = await seed_loan_data(db_session)
    repository = LoanRepository(db_session)

    total = await repository.count_active_by_user(
        data["user"].id
    )

    assert total == 2


@pytest.mark.asyncio
async def test_repository_should_get_active_book_for_update(db_session):
    data = await seed_loan_data(db_session)
    repository = LoanRepository(db_session)

    book = await repository.get_book_for_update(
        data["book"].id
    )
    inactive_book = await repository.get_book_for_update(
        data["inactive_book"].id
    )

    assert book.id == data["book"].id
    assert inactive_book is None


@pytest.mark.asyncio
async def test_repository_should_find_active_loan_for_update(db_session):
    data = await seed_loan_data(db_session)
    repository = LoanRepository(db_session)

    active_loan = await repository.find_active_by_id_for_update(
        data["active_loan"].id
    )
    returned_loan = await repository.find_active_by_id_for_update(
        data["returned_loan"].id
    )

    assert active_loan.id == data["active_loan"].id
    assert returned_loan is None


@pytest.mark.asyncio
async def test_repository_should_list_active_loans(db_session):
    data = await seed_loan_data(db_session)
    repository = LoanRepository(db_session)

    loans = await repository.list_active()

    assert {loan.id for loan in loans} == {
        data["active_loan"].id,
        data["overdue_loan"].id,
    }


@pytest.mark.asyncio
async def test_repository_should_list_overdue_loans(db_session):
    data = await seed_loan_data(db_session)
    repository = LoanRepository(db_session)

    loans = await repository.list_overdue()

    assert [loan.id for loan in loans] == [
        data["overdue_loan"].id
    ]


@pytest.mark.asyncio
async def test_repository_should_list_loans_by_user(db_session):
    data = await seed_loan_data(db_session)
    repository = LoanRepository(db_session)

    loans = await repository.list_by_user(
        data["user"].id
    )

    assert {loan.id for loan in loans} == {
        data["active_loan"].id,
        data["overdue_loan"].id,
    }


@pytest.mark.asyncio
async def test_repository_should_list_paginated_without_filters(db_session):
    await seed_loan_data(db_session)
    repository = LoanRepository(db_session)

    loans, total = await repository.list_paginated(
        page=1,
        size=2,
    )

    assert len(loans) == 2
    assert total == 3


@pytest.mark.asyncio
async def test_repository_should_list_paginated_with_filters(db_session):
    data = await seed_loan_data(db_session)
    repository = LoanRepository(db_session)

    loans, total = await repository.list_paginated(
        page=1,
        size=10,
        user_id=data["user"].id,
        book_id=data["other_book"].id,
        status=LoanStatus.ACTIVE,
        overdue=True,
    )

    assert total == 1
    assert [loan.id for loan in loans] == [
        data["overdue_loan"].id
    ]


@pytest.mark.asyncio
async def test_repository_should_filter_not_overdue_loans(db_session):
    data = await seed_loan_data(db_session)
    repository = LoanRepository(db_session)

    loans, total = await repository.list_paginated(
        page=1,
        size=10,
        overdue=False,
    )

    assert total == 2
    assert {loan.id for loan in loans} == {
        data["active_loan"].id,
        data["returned_loan"].id,
    }


@pytest.mark.asyncio
async def test_repository_should_update_loan(db_session):
    data = await seed_loan_data(db_session)
    repository = LoanRepository(db_session)
    loan = data["active_loan"]
    loan.status = LoanStatus.CANCELLED

    updated_loan = await repository.update(loan)

    assert updated_loan.status == LoanStatus.CANCELLED


@pytest.mark.asyncio
async def test_repository_should_find_by_user_paginated(db_session):
    data = await seed_loan_data(db_session)
    repository = LoanRepository(db_session)

    loans, total = await repository.find_by_user_paginated(
        user_id=data["user"].id,
        page=1,
        size=10,
        status=LoanStatus.ACTIVE,
    )

    assert total == 2
    assert {loan.id for loan in loans} == {
        data["active_loan"].id,
        data["overdue_loan"].id,
    }
