from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.security.dependencies import get_current_admin
from app.domain.loans.models.loan_model import LoanStatus
from app.domain.reports.services.report_service import ReportService
from app.infra.database.session import get_db

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


def get_report_service(
    db: AsyncSession = Depends(get_db),
):
    return ReportService(db)


@router.get(
    "/stats",
    summary="Get system statistics",
)
async def get_stats(
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    service: ReportService = Depends(get_report_service),
    _current_admin=Depends(get_current_admin),
):
    return await service.get_stats(
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/loans.csv",
    summary="Export loans report as CSV",
)
async def export_loans_csv(
    status: LoanStatus | None = Query(None),
    user_id: str | None = Query(None),
    book_id: str | None = Query(None),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    service: ReportService = Depends(get_report_service),
    _current_admin=Depends(get_current_admin),
):
    csv_content = await service.generate_loans_csv(
        status=status,
        user_id=user_id,
        book_id=book_id,
        start_date=start_date,
        end_date=end_date,
    )

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=loans.csv"
        },
    )


@router.get(
    "/fines.pdf",
    summary="Export fines report as PDF",
)
async def export_fines_pdf(
    user_id: str | None = Query(None),
    book_id: str | None = Query(None),
    min_amount: float | None = Query(None, ge=0),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    service: ReportService = Depends(get_report_service),
    _current_admin=Depends(get_current_admin),
):
    pdf_buffer = await service.generate_fines_pdf(
        user_id=user_id,
        book_id=book_id,
        min_amount=min_amount,
        start_date=start_date,
        end_date=end_date,
    )

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=fines.pdf"
        },
    )