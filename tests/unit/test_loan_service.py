from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from app.domain.loans.models.loan_model import LoanStatus
from app.domain.loans.schemas.loan_schema import CreateLoanSchema, UpdateLoanSchema
from app.domain.loans.services.fine_calculator import FineCalculator
from app.domain.loans.services.loan_service import LoanService
from app.exceptions.base import BusinessRuleException, NotFoundException
from tests.factories.book_factory import make_book
from tests.factories.loan_factory import make_loan
from tests.factories.user_factory import make_user


def make_service():
    repository = AsyncMock()
    repository.db = AsyncMock()
    user_repository = AsyncMock()
    cache_service = AsyncMock()
    cache_service.get.return_value = None
    fine_calculator = FineCalculator()

    return (
        LoanService(
            repository=repository,
            user_repository=user_repository,
            cache_service=cache_service,
            fine_calculator=fine_calculator,
        ),
        repository,
        user_repository,
        cache_service,
    )


def test_fine_calculator_should_return_zero_when_not_late():
    calculator = FineCalculator()
    due_date = datetime.utcnow() + timedelta(days=1)

    assert calculator.calculate_days_late(due_date) == 0
    assert calculator.calculate_amount(due_date) == 0


def test_fine_calculator_should_calculate_days_and_amount():
    calculator = FineCalculator()
    due_date = datetime(2026, 5, 1, 10, 0, 0)
    reference_date = datetime(2026, 5, 4, 9, 0, 0)

    assert calculator.calculate_days_late(due_date, reference_date) == 3
    assert calculator.calculate_amount(due_date, reference_date) == 6.0


def test_should_serialize_active_overdue_loan():
    service, _, _, _ = make_service()
    loan = make_loan(
        due_date=datetime.utcnow() - timedelta(days=2),
        status=LoanStatus.ACTIVE,
    )

    response = service._serialize_loan(loan)

    assert response["id"] == str(loan.id)
    assert response["status"] == LoanStatus.ACTIVE
    assert response["is_overdue"] is True
    assert response["days_late"] >= 2
    assert response["current_fine_amount"] >= 4


def test_should_serialize_returned_loan_using_persisted_fine():
    service, _, _, _ = make_service()
    returned_at = datetime.utcnow()
    loan = make_loan(
        due_date=returned_at - timedelta(days=5),
        returned_at=returned_at,
        status=LoanStatus.RETURNED,
        fine_amount=10,
    )

    response = service._serialize_loan(loan)

    assert response["status"] == LoanStatus.RETURNED
    assert response["is_overdue"] is False
    assert response["current_fine_amount"] == 10
    assert response["days_late"] == 5


@pytest.mark.asyncio
async def test_should_create_loan_and_decrease_available_copies():
    service, repository, user_repository, cache_service = make_service()
    user = make_user()
    book = make_book(available_copies=3)
    created_loan = make_loan(
        user_id=user.id,
        book_id=book.id,
    )
    user_repository.find_by_id.return_value = user
    repository.count_active_by_user.return_value = 0
    repository.get_book_for_update.return_value = book
    repository.create.return_value = created_loan

    response = await service.create_loan(
        CreateLoanSchema(
            user_id=user.id,
            book_id=book.id,
        )
    )

    saved_loan = repository.create.await_args.args[0]

    assert saved_loan.user_id == user.id
    assert saved_loan.book_id == book.id
    assert saved_loan.status == LoanStatus.ACTIVE
    assert book.available_copies == 2
    assert response["user_id"] == user.id
    repository.db.commit.assert_awaited_once()
    repository.db.refresh.assert_awaited_once_with(created_loan)
    cache_service.delete.assert_any_await(f"book:{book.id}")
    cache_service.delete.assert_any_await(f"loans:item:{created_loan.id}")
    cache_service.delete_pattern.assert_any_await("books:list*")
    cache_service.delete_pattern.assert_any_await("loans:list*")
    cache_service.delete_pattern.assert_any_await(f"loans:user:{user.id}:*")


@pytest.mark.asyncio
async def test_should_not_create_loan_when_user_not_found():
    service, repository, user_repository, _ = make_service()
    user_repository.find_by_id.return_value = None

    with pytest.raises(NotFoundException):
        await service.create_loan(
            CreateLoanSchema(
                user_id="missing-user",
                book_id="book-id",
            )
        )

    repository.count_active_by_user.assert_not_awaited()


@pytest.mark.asyncio
async def test_should_not_create_loan_when_user_reached_limit():
    service, repository, user_repository, _ = make_service()
    user_repository.find_by_id.return_value = make_user()
    repository.count_active_by_user.return_value = service.MAX_ACTIVE_LOANS

    with pytest.raises(BusinessRuleException):
        await service.create_loan(
            CreateLoanSchema(
                user_id="user-id",
                book_id="book-id",
            )
        )

    repository.get_book_for_update.assert_not_awaited()


@pytest.mark.asyncio
async def test_should_not_create_loan_when_book_not_found():
    service, repository, user_repository, _ = make_service()
    user_repository.find_by_id.return_value = make_user()
    repository.count_active_by_user.return_value = 0
    repository.get_book_for_update.return_value = None

    with pytest.raises(NotFoundException):
        await service.create_loan(
            CreateLoanSchema(
                user_id="user-id",
                book_id="missing-book",
            )
        )

    repository.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_should_not_create_loan_when_book_unavailable():
    service, repository, user_repository, _ = make_service()
    user_repository.find_by_id.return_value = make_user()
    repository.count_active_by_user.return_value = 0
    repository.get_book_for_update.return_value = make_book(available_copies=0)

    with pytest.raises(BusinessRuleException):
        await service.create_loan(
            CreateLoanSchema(
                user_id="user-id",
                book_id="book-id",
            )
        )

    repository.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_should_get_loan():
    service, repository, _, _ = make_service()
    loan = make_loan()
    repository.find_by_id.return_value = loan

    response = await service.get_loan(loan.id)

    assert response["id"] == str(loan.id)
    repository.find_by_id.assert_awaited_once_with(loan.id)
    cache_service = service.cache_service
    cache_service.set.assert_awaited_once()


@pytest.mark.asyncio
async def test_should_return_cached_loan():
    service, repository, _, cache_service = make_service()
    cached_loan = {
        "id": "loan-id",
        "status": LoanStatus.ACTIVE,
    }
    cache_service.get.return_value = cached_loan

    response = await service.get_loan("loan-id")

    assert response == cached_loan
    repository.find_by_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_should_raise_not_found_when_getting_missing_loan():
    service, repository, _, _ = make_service()
    repository.find_by_id.return_value = None

    with pytest.raises(NotFoundException):
        await service.get_loan("missing-loan")


@pytest.mark.asyncio
async def test_should_return_loan_and_restore_available_copy():
    service, repository, _, cache_service = make_service()
    book = make_book(available_copies=0)
    loan = make_loan(
        book_id=book.id,
        due_date=datetime.utcnow() - timedelta(days=3),
    )
    repository.find_active_by_id_for_update.return_value = loan
    repository.get_book_for_update.return_value = book

    response = await service.return_loan(loan.id)

    assert loan.status == LoanStatus.RETURNED
    assert loan.returned_at is not None
    assert loan.fine_amount == 6
    assert book.available_copies == 1
    assert response["status"] == LoanStatus.RETURNED
    assert response["days_late"] == 3
    repository.db.commit.assert_awaited_once()
    repository.db.refresh.assert_awaited_once_with(loan)
    cache_service.delete.assert_any_await(f"book:{book.id}")
    cache_service.delete.assert_any_await(f"loans:item:{loan.id}")


@pytest.mark.asyncio
async def test_should_raise_not_found_when_returning_missing_active_loan():
    service, repository, _, _ = make_service()
    repository.find_active_by_id_for_update.return_value = None

    with pytest.raises(NotFoundException):
        await service.return_loan("missing-loan")

    repository.get_book_for_update.assert_not_awaited()


@pytest.mark.asyncio
async def test_should_raise_not_found_when_return_book_is_missing():
    service, repository, _, _ = make_service()
    repository.find_active_by_id_for_update.return_value = make_loan()
    repository.get_book_for_update.return_value = None

    with pytest.raises(NotFoundException):
        await service.return_loan("loan-id")


@pytest.mark.asyncio
async def test_should_list_active_and_overdue_loans():
    service, repository, _, _ = make_service()
    active_loan = make_loan(status=LoanStatus.ACTIVE)
    overdue_loan = make_loan(
        due_date=datetime.utcnow() - timedelta(days=1),
    )
    repository.list_active.return_value = [active_loan]
    repository.list_overdue.return_value = [overdue_loan]

    active_response = await service.list_active()
    overdue_response = await service.list_overdue()

    assert active_response[0]["id"] == str(active_loan.id)
    assert overdue_response[0]["id"] == str(overdue_loan.id)


@pytest.mark.asyncio
async def test_should_list_paginated_loans():
    service, repository, _, _ = make_service()
    loan = make_loan()
    repository.list_paginated.return_value = ([loan], 1)

    response = await service.list_paginated(
        page=2,
        size=5,
        user_id="user-id",
        book_id="book-id",
        status=LoanStatus.ACTIVE,
        overdue=False,
    )

    assert response["items"][0]["id"] == str(loan.id)
    assert response["total"] == 1
    assert response["page"] == 2
    assert response["size"] == 5
    repository.list_paginated.assert_awaited_once_with(
        page=2,
        size=5,
        user_id="user-id",
        book_id="book-id",
        status=LoanStatus.ACTIVE,
        overdue=False,
    )
    service.cache_service.set.assert_awaited_once()


@pytest.mark.asyncio
async def test_should_return_cached_paginated_loans():
    service, repository, _, cache_service = make_service()
    cached_response = {
        "items": [],
        "total": 0,
        "page": 1,
        "size": 10,
    }
    cache_service.get.return_value = cached_response

    response = await service.list_paginated(
        page=1,
        size=10,
    )

    assert response == cached_response
    repository.list_paginated.assert_not_awaited()


@pytest.mark.asyncio
async def test_should_list_active_and_overdue_paginated():
    service, repository, _, _ = make_service()
    repository.list_paginated.return_value = ([], 0)

    active_response = await service.list_active_paginated(1, 10)
    overdue_response = await service.list_overdue_paginated(2, 5)

    assert active_response["total"] == 0
    assert overdue_response["page"] == 2
    repository.list_paginated.assert_any_await(
        page=1,
        size=10,
        user_id=None,
        book_id=None,
        status=LoanStatus.ACTIVE,
        overdue=None,
    )
    repository.list_paginated.assert_any_await(
        page=2,
        size=5,
        user_id=None,
        book_id=None,
        status=None,
        overdue=True,
    )


@pytest.mark.asyncio
async def test_should_list_by_user_paginated():
    service, repository, user_repository, _ = make_service()
    user = make_user()
    loan = make_loan(user_id=user.id)
    user_repository.find_by_id.return_value = user
    repository.find_by_user_paginated.return_value = ([loan], 1)

    response = await service.list_by_user_paginated(
        user_id=user.id,
        page=1,
        size=10,
        status=LoanStatus.ACTIVE,
    )

    assert response["items"][0]["user_id"] == user.id
    assert response["total"] == 1
    cache_service = service.cache_service
    cache_service.set.assert_awaited_once()


@pytest.mark.asyncio
async def test_should_return_cached_user_loans():
    service, repository, user_repository, cache_service = make_service()
    cached_response = {
        "items": [],
        "total": 0,
        "page": 1,
        "size": 10,
    }
    cache_service.get.return_value = cached_response

    response = await service.list_by_user_paginated(
        user_id="user-id",
        page=1,
        size=10,
    )

    assert response == cached_response
    user_repository.find_by_id.assert_not_awaited()
    repository.find_by_user_paginated.assert_not_awaited()


@pytest.mark.asyncio
async def test_should_raise_not_found_when_listing_missing_user_loans():
    service, repository, user_repository, _ = make_service()
    user_repository.find_by_id.return_value = None

    with pytest.raises(NotFoundException):
        await service.list_by_user_paginated(
            user_id="missing-user",
            page=1,
            size=10,
        )

    repository.find_by_user_paginated.assert_not_awaited()


@pytest.mark.asyncio
async def test_should_list_by_user_legacy_method():
    service, repository, _, _ = make_service()
    loan = make_loan(user_id="user-id")
    repository.list_by_user.return_value = [loan]

    response = await service.list_by_user("user-id")

    assert response[0]["user_id"] == "user-id"


@pytest.mark.asyncio
async def test_should_update_active_loan_due_date():
    service, repository, _, _ = make_service()
    loan = make_loan()
    new_due_date = loan.loan_date + timedelta(days=30)
    repository.find_by_id.return_value = loan
    repository.update.return_value = loan

    response = await service.update_loan(
        loan.id,
        UpdateLoanSchema(due_date=new_due_date),
    )

    assert loan.due_date == new_due_date
    assert response["id"] == str(loan.id)
    repository.update.assert_awaited_once_with(loan)


@pytest.mark.asyncio
async def test_should_raise_not_found_when_updating_missing_loan():
    service, repository, _, _ = make_service()
    repository.find_by_id.return_value = None

    with pytest.raises(NotFoundException):
        await service.update_loan(
            "missing-loan",
            UpdateLoanSchema(),
        )


@pytest.mark.asyncio
async def test_should_not_update_non_active_loan():
    service, repository, _, _ = make_service()
    repository.find_by_id.return_value = make_loan(
        status=LoanStatus.RETURNED,
    )

    with pytest.raises(BusinessRuleException):
        await service.update_loan(
            "loan-id",
            UpdateLoanSchema(),
        )


@pytest.mark.asyncio
async def test_should_not_update_due_date_before_loan_date():
    service, repository, _, _ = make_service()
    loan = make_loan()
    repository.find_by_id.return_value = loan

    with pytest.raises(BusinessRuleException):
        await service.update_loan(
            loan.id,
            UpdateLoanSchema(
                due_date=loan.loan_date,
            ),
        )


@pytest.mark.asyncio
async def test_should_cancel_loan_and_restore_available_copy():
    service, repository, _, cache_service = make_service()
    book = make_book(available_copies=0)
    loan = make_loan(book_id=book.id)
    repository.find_active_by_id_for_update.return_value = loan
    repository.get_book_for_update.return_value = book

    response = await service.cancel_loan(loan.id)

    assert loan.status == LoanStatus.CANCELLED
    assert loan.cancelled_at is not None
    assert loan.fine_amount == 0
    assert book.available_copies == 1
    assert response["status"] == LoanStatus.CANCELLED
    repository.db.commit.assert_awaited_once()
    repository.db.refresh.assert_awaited_once_with(loan)
    cache_service.delete.assert_any_await(f"book:{book.id}")
    cache_service.delete.assert_any_await(f"loans:item:{loan.id}")


@pytest.mark.asyncio
async def test_should_raise_not_found_when_cancelling_missing_active_loan():
    service, repository, _, _ = make_service()
    repository.find_active_by_id_for_update.return_value = None

    with pytest.raises(NotFoundException):
        await service.cancel_loan("missing-loan")

    repository.get_book_for_update.assert_not_awaited()


@pytest.mark.asyncio
async def test_should_raise_not_found_when_cancel_book_is_missing():
    service, repository, _, _ = make_service()
    repository.find_active_by_id_for_update.return_value = make_loan()
    repository.get_book_for_update.return_value = None

    with pytest.raises(NotFoundException):
        await service.cancel_loan("loan-id")
