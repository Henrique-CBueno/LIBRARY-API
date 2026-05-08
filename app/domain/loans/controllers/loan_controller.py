from fastapi import APIRouter, Depends, Request
from fastapi.params import Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis_service import CacheService
from app.config.security.dependencies import get_current_admin, get_current_user
from app.domain.loans.models.loan_model import LoanStatus
from app.domain.loans.repositories.loan_repository import LoanRepository
from app.domain.loans.schemas.loan_schema import (
    CancelLoanResponseSchema,
    CreateLoanSchema,
    LoanResponseSchema,
    PayLoanFineResponseSchema,
    ReturnLoanResponseSchema,
    UpdateLoanSchema, RenewLoanResponseSchema,
)
from app.domain.loans.services.fine_calculator import FineCalculator
from app.domain.loans.services.loan_service import LoanService
from app.domain.reservation.repositories.reservation_repository import ReservationRepository
from app.domain.users.enums.user_role import UserRole
from app.domain.users.models.user_model import UserModel
from app.domain.users.repositories.user_repository import UserRepository
from app.events.bus import EventBus
from app.events.registrar_handlers import register_event_handlers
from app.exceptions.base import UnauthorizedException
from app.infra.database.session import get_db
from app.infra.middleware.rate_limit import limiter
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
        reservation_repository=ReservationRepository(db),
        cache_service=CacheService(),
        fine_calculator=FineCalculator(),
        event_bus=event_bus,
    )


def user_is_not_admin_and_does_not_own_loan(
    user: UserModel,
    loan_user_id: str,
):
    return (
        user.role != UserRole.ADMIN.value
        and loan_user_id != str(user.id)
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
    _current_admin=Depends(get_current_admin),
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
    user=Depends(get_current_user),
):
    if user.role != UserRole.ADMIN.value and user_id != str(user.id):
        raise UnauthorizedException("You can only access your own loans")

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
    _current_admin=Depends(get_current_admin),
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
@limiter.limit("30/minute")
async def cancel_loan(
    request: Request,
    loan_id: str,
    service: LoanService = Depends(get_loan_service),
    user: UserModel = Depends(get_current_user),
):
    loan = await service.get_loan(loan_id)

    if user_is_not_admin_and_does_not_own_loan(user, loan["user_id"]):
        raise UnauthorizedException("You can only cancel your own loans")

    return await service.cancel_loan(loan_id)

@router.post(
    "/{loan_id}/pay-fine",
    response_model=PayLoanFineResponseSchema,
    summary="Pay loan fine",
)
async def pay_loan_fine(
    loan_id: str,
    service: LoanService = Depends(get_loan_service),
    user=Depends(get_current_user),
):
    loan = await service.get_loan(loan_id)

    if user_is_not_admin_and_does_not_own_loan(user, loan["user_id"]):
        raise UnauthorizedException("You can only pay your own loans")

    return await service.pay_fine(loan_id)

@router.post(
    "",
    response_model=LoanResponseSchema,
    status_code=201,
    summary="Create loan",
)
@limiter.limit("20/minute")
async def create_loan(
    request: Request,
    data: CreateLoanSchema,
    service: LoanService = Depends(get_loan_service),
    _current_admin=Depends(get_current_admin),
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
    _current_admin=Depends(get_current_admin),
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
    _current_admin=Depends(get_current_admin),
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
    user=Depends(get_current_user),
):
    loan = await service.get_loan(loan_id)

    if user_is_not_admin_and_does_not_own_loan(user, loan["user_id"]):
        raise UnauthorizedException("You can only view your own loans")

    return await service.get_loan(loan_id)


@router.post(
    "/{loan_id}/return",
    response_model=ReturnLoanResponseSchema,
    summary="Return loan",
)
@limiter.limit("30/minute")
async def return_loan(
    request: Request,
    loan_id: str,
    service: LoanService = Depends(get_loan_service),
    user=Depends(get_current_user),
):
    loan = await service.get_loan(loan_id)

    if user_is_not_admin_and_does_not_own_loan(user, loan["user_id"]):
        raise UnauthorizedException("You can only return your own loans")

    return await service.return_loan(loan_id)

@router.post(
    "/{loan_id}/renew",
    response_model=RenewLoanResponseSchema,
    summary="Renew loan",
)
@limiter.limit("30/minute")
async def renew_loan(
    request: Request,
    loan_id: str,
    service: LoanService = Depends(get_loan_service),
    user=Depends(get_current_user),
):
    loan = await service.get_loan(loan_id)

    if user_is_not_admin_and_does_not_own_loan(user, loan["user_id"]):
        raise UnauthorizedException("You can only renew your own loans")

    return await service.renew_loan(loan_id)

