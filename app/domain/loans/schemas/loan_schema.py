from datetime import datetime

from pydantic import BaseModel

from app.domain.loans.models.loan_model import LoanStatus


class CreateLoanSchema(BaseModel):
    user_id: str
    book_id: str


class UpdateLoanSchema(BaseModel):
    due_date: datetime | None = None


class LoanResponseSchema(BaseModel):
    id: str
    user_id: str
    book_id: str
    loan_date: datetime
    due_date: datetime
    returned_at: datetime | None
    cancelled_at: datetime | None
    status: LoanStatus
    fine_amount: float
    fine_paid_at: datetime | None
    fine_paid_amount: float
    current_fine_amount: float
    days_late: int
    is_overdue: bool
    renewal_count: int

    model_config = {
        "from_attributes": True
    }


class ReturnLoanResponseSchema(BaseModel):
    id: str
    status: LoanStatus
    returned_at: datetime
    fine_amount: float
    fine_paid_at: datetime | None
    fine_paid_amount: float
    days_late: int


class CancelLoanResponseSchema(BaseModel):
    id: str
    status: LoanStatus
    cancelled_at: datetime


class PayLoanFineResponseSchema(BaseModel):
    id: str
    fine_amount: float
    payment_amount: float
    fine_paid_amount: float
    fine_paid_at: datetime
