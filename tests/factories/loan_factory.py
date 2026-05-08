from datetime import datetime, timedelta

import uuid6 as uuid

from app.domain.loans.models.loan_model import LoanModel, LoanStatus


def make_loan(
    user_id: str | None = None,
    book_id: str | None = None,
    loan_date: datetime | None = None,
    due_date: datetime | None = None,
    returned_at: datetime | None = None,
    cancelled_at: datetime | None = None,
    status: LoanStatus = LoanStatus.ACTIVE,
    fine_amount: float = 0,
    fine_paid_at: datetime | None = None,
    fine_paid_amount: float = 0,
    renewal_count: int = 0,
):
    loan_date = loan_date or datetime.utcnow()

    return LoanModel(
        id=str(uuid.uuid7()),
        user_id=user_id or str(uuid.uuid7()),
        book_id=book_id or str(uuid.uuid7()),
        loan_date=loan_date,
        due_date=due_date or loan_date + timedelta(days=14),
        returned_at=returned_at,
        cancelled_at=cancelled_at,
        status=status,
        fine_amount=fine_amount,
        fine_paid_at=fine_paid_at,
        fine_paid_amount=fine_paid_amount,
        renewal_count=renewal_count,
    )
