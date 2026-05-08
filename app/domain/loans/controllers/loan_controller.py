from fastapi import APIRouter, Depends
from fastapi.params import Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis_service import CacheService
from app.domain.loans.models.loan_model import LoanStatus
from app.domain.loans.repositories.loan_repository import LoanRepository
from app.domain.loans.schemas.loan_schema import LoanResponseSchema, CreateLoanSchema, ReturnLoanResponseSchema, \
    UpdateLoanSchema, CancelLoanResponseSchema
from app.domain.loans.services.fine_calculator import FineCalculator
from app.domain.loans.services.loan_service import LoanService
from app.domain.users.repositories.user_repository import UserRepository
from app.events.bus import EventBus
from app.events.registrar_handlers import register_event_handlers
from app.infra.database.session import get_db
from app.infra.padronize.pagination.schemas import PaginatedResponse

router = APIRouter(
    prefix="/loans",
    tags=["Loans"],
)


def get_loan_service(
    db: AsyncSession = Depends(get_db),
):
    event_bus = EventBus()
    register_event_handlers(event_bus, db)

    return LoanService(
        repository=LoanRepository(db),
        user_repository=UserRepository(db),
        cache_service=CacheService(),
        fine_calculator=FineCalculator(),
        event_bus=event_bus,
    )


@router.get(
    "",
    response_model=PaginatedResponse[LoanResponseSchema],
    summary="List loans",
)
async def list_loans(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    user_id: str | None = Query(None),
    book_id: str | None = Query(None),
    status: LoanStatus | None = Query(None),
    overdue: bool | None = Query(None),
    service: LoanService = Depends(get_loan_service),
):
    return await service.list_paginated(
        page=page,
        size=size,
        user_id=user_id,
        book_id=book_id,
        status=status,
        overdue=overdue,
    )

@router.get(
    "/users/{user_id}",
    response_model=PaginatedResponse[LoanResponseSchema],
    summary="List loans by user",
)
async def list_loans_by_user(
    user_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    status: LoanStatus | None = Query(None),
    service: LoanService = Depends(get_loan_service),
):
    return await service.list_by_user_paginated(
        user_id=user_id,
        page=page,
        size=size,
        status=status,
    )

@router.put(
    "/{loan_id}",
    response_model=LoanResponseSchema,
    summary="Update loan",
)
async def update_loan(
    loan_id: str,
    data: UpdateLoanSchema,
    service: LoanService = Depends(get_loan_service),
):
    return await service.update_loan(
        loan_id,
        data,
    )

@router.post(
    "/{loan_id}/cancel",
    response_model=CancelLoanResponseSchema,
    summary="Cancel loan",
)
async def cancel_loan(
    loan_id: str,
    service: LoanService = Depends(get_loan_service),
):
    return await service.cancel_loan(loan_id)

@router.post(
    "",
    response_model=LoanResponseSchema,
    status_code=201,
    summary="Create loan",
)
async def create_loan(
    data: CreateLoanSchema,
    service: LoanService = Depends(get_loan_service),
):
    return await service.create_loan(data)


@router.get(
    "/active",
    response_model=PaginatedResponse[LoanResponseSchema],
    summary="List active loans",
)
async def list_active_loans(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    service: LoanService = Depends(get_loan_service),
):
    return await service.list_active_paginated(
        page=page,
        size=size,
    )


@router.get(
    "/overdue",
    response_model=PaginatedResponse[LoanResponseSchema],
    summary="List overdue loans",
)
async def list_overdue_loans(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    service: LoanService = Depends(get_loan_service),
):
    return await service.list_overdue_paginated(
        page=page,
        size=size,
    )


@router.get(
    "/{loan_id}",
    response_model=LoanResponseSchema,
    summary="Get loan by ID",
)
async def get_loan(
    loan_id: str,
    service: LoanService = Depends(get_loan_service),
):
    return await service.get_loan(loan_id)


@router.post(
    "/{loan_id}/return",
    response_model=ReturnLoanResponseSchema,
    summary="Return loan",
)
async def return_loan(
    loan_id: str,
    service: LoanService = Depends(get_loan_service),
):
    return await service.return_loan(loan_id)

