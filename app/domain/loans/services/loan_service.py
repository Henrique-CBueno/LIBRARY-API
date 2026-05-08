from datetime import datetime, timedelta

import structlog

from app.cache.redis_service import CacheService
from app.domain.loans.models.loan_model import LoanModel, LoanStatus
from app.domain.loans.repositories.loan_repository import LoanRepository
from app.domain.loans.schemas.loan_schema import CreateLoanSchema, UpdateLoanSchema
from app.domain.loans.services.fine_calculator import FineCalculator
from app.domain.users.repositories.user_repository import UserRepository
from app.events.bus import EventBus
from app.events.loans.events import LoanCreatedEvent, LoanReturnedEvent, LoanCancelledEvent
from app.exceptions.base import (
    BusinessRuleException,
    FinePaymentRequiredException,
    NotFoundException,
)

logger = structlog.get_logger()


class LoanService:
    LOAN_DAYS = 14
    MAX_ACTIVE_LOANS = 3
    CACHE_TTL_SECONDS = 30
    RENEWAL_DAYS = 7
    MAX_RENEWALS = 2

    def __init__(
        self,
        repository: LoanRepository,
        user_repository: UserRepository,
        cache_service: CacheService,
        fine_calculator: FineCalculator,
        event_bus: EventBus,
    ):
        self.repository = repository
        self.user_repository = user_repository
        self.cache_service = cache_service
        self.fine_calculator = fine_calculator
        self.event_bus = event_bus

    def _serialize_loan(
        self,
        loan: LoanModel,
    ):
        reference_date = (
            loan.returned_at
            if loan.status == LoanStatus.RETURNED
            else datetime.utcnow()
        )

        days_late = self.fine_calculator.calculate_days_late(
            loan.due_date,
            reference_date,
        )

        current_fine_amount = self.fine_calculator.calculate_amount(
            loan.due_date,
            reference_date,
        )

        return {
            "id": str(loan.id),
            "user_id": str(loan.user_id),
            "book_id": str(loan.book_id),
            "loan_date": loan.loan_date,
            "due_date": loan.due_date,
            "returned_at": loan.returned_at,
            "cancelled_at": loan.cancelled_at,
            "status": loan.status,
            "fine_amount": float(loan.fine_amount),
            "fine_paid_at": loan.fine_paid_at,
            "fine_paid_amount": float(loan.fine_paid_amount),
            "current_fine_amount": (
                current_fine_amount
                if loan.status == LoanStatus.ACTIVE
                else float(loan.fine_amount)
            ),
            "days_late": days_late,
            "is_overdue": (
                loan.status == LoanStatus.ACTIVE
                and days_late > 0
            ),
            "renewal_count": loan.renewal_count,
        }

    async def create_loan(
        self,
        data: CreateLoanSchema,
    ):
        user = await self.user_repository.find_by_id(
            data.user_id,
        )

        if not user:
            raise NotFoundException(
                "User not found"
            )

        active_loans = (
            await self.repository.count_active_by_user(
                data.user_id,
            )
        )

        if active_loans >= self.MAX_ACTIVE_LOANS:
            raise BusinessRuleException(
                "User has reached the maximum number of active loans"
            )

        book = await self.repository.get_book_for_update(
            data.book_id,
        )

        if not book:
            raise NotFoundException(
                "Book not found"
            )

        if book.available_copies <= 0:
            raise BusinessRuleException(
                "Book is unavailable"
            )

        now = datetime.utcnow()

        loan = LoanModel(
            user_id=data.user_id,
            book_id=data.book_id,
            loan_date=now,
            due_date=now + timedelta(days=self.LOAN_DAYS),
            status=LoanStatus.ACTIVE,
            fine_amount=0,
        )

        book.available_copies -= 1

        created_loan = await self.repository.create(
            loan,
        )

        await self.repository.db.commit()
        await self.repository.db.refresh(created_loan)

        await self.cache_service.delete(
            f"book:{data.book_id}"
        )
        await self.cache_service.delete_pattern(
            "books:list*"
        )
        await self._invalidate_loan_cache(
            user_id=data.user_id,
            loan_id=created_loan.id,
        )

        logger.info(
            "loan_created",
            loan_id=str(created_loan.id),
            user_id=str(data.user_id),
            book_id=str(data.book_id),
        )

        await self.event_bus.publish(
            LoanCreatedEvent(
                occurred_at=datetime.utcnow(),
                loan_id=created_loan.id,
                user_id=created_loan.user_id,
                book_id=created_loan.book_id,
            )
        )

        return self._serialize_loan(created_loan)

    async def get_loan(
        self,
        loan_id: str,
    ):
        cache_key = f"loans:item:{loan_id}"

        cached_loan = await self.cache_service.get(
            cache_key
        )

        if cached_loan:
            return cached_loan

        loan = await self.repository.find_by_id(
            loan_id,
        )

        if not loan:
            raise NotFoundException(
                "Loan not found"
            )

        serialized_loan = self._serialize_loan(loan)

        await self.cache_service.set(
            cache_key,
            serialized_loan,
            expire=self.CACHE_TTL_SECONDS,
        )

        return serialized_loan

    async def return_loan(
        self,
        loan_id: str,
    ):
        loan = (
            await self.repository.find_active_by_id_for_update(
                loan_id,
            )
        )

        if not loan:
            raise NotFoundException(
                "Active loan not found"
            )

        now = datetime.utcnow()

        days_late = (
            self.fine_calculator.calculate_days_late(
                loan.due_date,
                now,
            )
        )

        fine_amount = (
            self.fine_calculator.calculate_amount(
                loan.due_date,
                now,
            )
        )

        if fine_amount > 0 and (
            float(loan.fine_paid_amount) < fine_amount
        ):
            raise FinePaymentRequiredException()

        book = await self.repository.get_book_for_update(
            loan.book_id,
        )

        if not book:
            raise NotFoundException(
                "Book not found"
            )

        loan.status = LoanStatus.RETURNED
        loan.returned_at = now
        loan.fine_amount = fine_amount

        book.available_copies += 1

        await self.repository.db.commit()
        await self.repository.db.refresh(loan)

        await self.cache_service.delete(
            f"book:{loan.book_id}"
        )
        await self.cache_service.delete_pattern(
            "books:list*"
        )
        await self._invalidate_loan_cache(
            user_id=loan.user_id,
            loan_id=loan.id,
        )

        logger.info(
            "loan_returned",
            loan_id=str(loan.id),
            book_id=str(loan.book_id),
            fine_amount=float(loan.fine_amount),
        )

        await self.event_bus.publish(
            LoanReturnedEvent(
                occurred_at=datetime.utcnow(),
                loan_id=loan.id,
                user_id=loan.user_id,
                book_id=loan.book_id,
            )
        )

        return {
            "id": str(loan.id),
            "status": loan.status,
            "returned_at": loan.returned_at,
            "fine_amount": float(loan.fine_amount),
            "fine_paid_at": loan.fine_paid_at,
            "fine_paid_amount": float(loan.fine_paid_amount),
            "days_late": days_late,
        }

    async def pay_fine(
        self,
        loan_id: str,
    ):
        loan = (
            await self.repository.find_active_by_id_for_update(
                loan_id,
            )
        )

        if not loan:
            raise NotFoundException(
                "Active loan not found"
            )

        now = datetime.utcnow()

        fine_amount = self.fine_calculator.calculate_amount(
            loan.due_date,
            now,
        )

        if fine_amount <= 0:
            raise BusinessRuleException(
                "Loan has no fine to pay"
            )

        payment_amount = fine_amount - float(loan.fine_paid_amount)

        if payment_amount <= 0:
            raise BusinessRuleException(
                "Loan fine is already paid"
            )

        loan.fine_amount = fine_amount
        loan.fine_paid_amount = fine_amount
        loan.fine_paid_at = now

        await self.repository.db.commit()
        await self.repository.db.refresh(loan)

        await self._invalidate_loan_cache(
            user_id=loan.user_id,
            loan_id=loan.id,
        )

        logger.info(
            "loan_fine_paid",
            loan_id=str(loan.id),
            fine_amount=float(loan.fine_amount),
            payment_amount=payment_amount,
        )

        return {
            "id": str(loan.id),
            "fine_amount": float(loan.fine_amount),
            "payment_amount": payment_amount,
            "fine_paid_amount": float(loan.fine_paid_amount),
            "fine_paid_at": loan.fine_paid_at,
        }

    async def list_active(self):
        loans = await self.repository.list_active()

        return [
            self._serialize_loan(loan)
            for loan in loans
        ]

    async def list_overdue(self):
        loans = await self.repository.list_overdue()

        return [
            self._serialize_loan(loan)
            for loan in loans
        ]

    async def list_active_paginated(
            self,
            page: int,
            size: int,
    ):
        return await self.list_paginated(
            page=page,
            size=size,
            status=LoanStatus.ACTIVE,
        )

    async def list_overdue_paginated(
            self,
            page: int,
            size: int,
    ):
        return await self.list_paginated(
            page=page,
            size=size,
            overdue=True,
        )

    async def list_by_user(
        self,
        user_id: str,
    ):
        loans = await self.repository.list_by_user(
            user_id,
        )

        return [
            self._serialize_loan(loan)
            for loan in loans
        ]

    async def list_paginated(
            self,
            page: int,
            size: int,
            user_id: str | None = None,
            book_id: str | None = None,
            status: LoanStatus | None = None,
            overdue: bool | None = None,
    ):
        cache_key = (
            f"loans:list:{page}:{size}:{user_id}:{book_id}:{status}:{overdue}"
        )

        cached_loans = await self.cache_service.get(
            cache_key
        )

        if cached_loans:
            return cached_loans

        loans, total = await self.repository.list_paginated(
            page=page,
            size=size,
            user_id=user_id,
            book_id=book_id,
            status=status,
            overdue=overdue,
        )

        response = {
            "items": [
                self._serialize_loan(loan)
                for loan in loans
            ],
            "total": total,
            "page": page,
            "size": size,
        }

        await self.cache_service.set(
            cache_key,
            response,
            expire=self.CACHE_TTL_SECONDS,
        )

        return response

    async def list_by_user_paginated(
            self,
            user_id: str,
            page: int,
            size: int,
            status: LoanStatus | None = None,
    ):
        cache_key = (
            f"loans:user:{user_id}:{page}:{size}:{status}"
        )

        cached_loans = await self.cache_service.get(
            cache_key
        )

        if cached_loans:
            return cached_loans

        user = await self.user_repository.find_by_id(user_id)

        if not user:
            raise NotFoundException("User not found")

        loans, total = await self.repository.find_by_user_paginated(
            user_id=user_id,
            page=page,
            size=size,
            status=status,
        )

        response = {
            "items": [
                self._serialize_loan(loan)
                for loan in loans
            ],
            "total": total,
            "page": page,
            "size": size,
        }

        await self.cache_service.set(
            cache_key,
            response,
            expire=self.CACHE_TTL_SECONDS,
        )

        return response

    async def update_loan(
            self,
            loan_id: str,
            data: UpdateLoanSchema,
    ):
        loan = await self.repository.find_by_id(loan_id)

        if not loan:
            raise NotFoundException("Loan not found")

        if loan.status != LoanStatus.ACTIVE:
            raise BusinessRuleException(
                "Only active loans can be updated"
            )

        if data.due_date is not None:
            if data.due_date <= loan.loan_date:
                raise BusinessRuleException(
                    "due_date must be greater than loan_date"
                )

            loan.due_date = data.due_date

        updated_loan = await self.repository.update(loan)

        await self._invalidate_loan_cache(
            user_id=updated_loan.user_id,
            loan_id=updated_loan.id,
        )

        logger.info(
            "loan_updated",
            loan_id=str(loan.id),
        )

        return self._serialize_loan(updated_loan)

    async def cancel_loan(
            self,
            loan_id: str,
    ):
        loan = await self.repository.find_active_by_id_for_update(
            loan_id,
        )

        if not loan:
            raise NotFoundException("Active loan not found")

        book = await self.repository.get_book_for_update(
            loan.book_id,
        )

        if not book:
            raise NotFoundException("Book not found")

        now = datetime.utcnow()

        loan.status = LoanStatus.CANCELLED
        loan.cancelled_at = now
        loan.fine_amount = 0

        book.available_copies += 1

        await self.repository.db.commit()
        await self.repository.db.refresh(loan)

        await self.cache_service.delete(
            f"book:{loan.book_id}"
        )
        await self.cache_service.delete_pattern(
            "books:list*"
        )
        await self._invalidate_loan_cache(
            user_id=loan.user_id,
            loan_id=loan.id,
        )

        logger.info(
            "loan_cancelled",
            loan_id=str(loan.id),
            book_id=str(loan.book_id),
        )

        await self.event_bus.publish(
            LoanCancelledEvent(
                occurred_at=datetime.utcnow(),
                loan_id=loan.id,
                user_id=loan.user_id,
                book_id=loan.book_id,
            )
        )

        return {
            "id": str(loan.id),
            "status": loan.status,
            "cancelled_at": loan.cancelled_at,
        }

    async def _invalidate_loan_cache(
        self,
        user_id: str,
        loan_id: str,
    ):
        await self.cache_service.delete(
            f"loans:item:{loan_id}"
        )
        await self.cache_service.delete_pattern(
            "loans:list*"
        )
        await self.cache_service.delete_pattern(
            f"loans:user:{user_id}:*"
        )

    async def renew_loan(
            self,
            loan_id: str,
    ):
        loan = await self.repository.find_active_by_id_for_update(
            loan_id,
        )

        if not loan:
            raise NotFoundException(
                "Active loan not found"
            )

        days_late = self.fine_calculator.calculate_days_late(
            loan.due_date,
        )

        if days_late > 0:
            raise BusinessRuleException(
                "Overdue loans cannot be renewed"
            )

        if loan.renewal_count >= self.MAX_RENEWALS:
            raise BusinessRuleException(
                "Loan has reached the maximum number of renewals"
            )

        loan.due_date = loan.due_date + timedelta(
            days=self.RENEWAL_DAYS,
        )

        loan.renewal_count += 1

        await self.repository.db.commit()
        await self.repository.db.refresh(loan)

        logger.info(
            "loan_renewed",
            loan_id=str(loan.id),
            due_date=loan.due_date.isoformat(),
            renewal_count=loan.renewal_count,
        )

        return {
            "id": str(loan.id),
            "status": loan.status,
            "due_date": loan.due_date,
            "renewal_count": loan.renewal_count,
        }
