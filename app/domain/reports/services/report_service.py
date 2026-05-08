from datetime import datetime
from io import BytesIO, StringIO
import csv

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.books.models.book_model import BookModel
from app.domain.loans.models.loan_model import LoanStatus, LoanModel
from app.domain.users.models.user_model import UserModel


class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _apply_loan_filters(
        self,
        query,
        status: LoanStatus | None = None,
        user_id: str | None = None,
        book_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        if status:
            query = query.where(LoanModel.status == status)

        if user_id:
            query = query.where(LoanModel.user_id == user_id)

        if book_id:
            query = query.where(LoanModel.book_id == book_id)

        if start_date:
            query = query.where(LoanModel.loan_date >= start_date)

        if end_date:
            query = query.where(LoanModel.loan_date <= end_date)

        return query

    async def get_stats(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        total_books = await self.db.scalar(
            select(func.count()).select_from(BookModel)
        )

        total_users = await self.db.scalar(
            select(func.count()).select_from(UserModel)
        )

        loan_query = select(LoanModel)

        if start_date:
            loan_query = loan_query.where(LoanModel.loan_date >= start_date)

        if end_date:
            loan_query = loan_query.where(LoanModel.loan_date <= end_date)

        loans_result = await self.db.execute(loan_query)
        loans = loans_result.scalars().all()

        active_loans = len(
            [loan for loan in loans if loan.status == LoanStatus.ACTIVE]
        )

        returned_loans = len(
            [loan for loan in loans if loan.status == LoanStatus.RETURNED]
        )

        cancelled_loans = len(
            [loan for loan in loans if loan.status == LoanStatus.CANCELLED]
        )

        total_fines = sum(float(loan.fine_amount) for loan in loans)

        return {
            "total_books": total_books or 0,
            "total_users": total_users or 0,
            "total_loans": len(loans),
            "active_loans": active_loans,
            "returned_loans": returned_loans,
            "cancelled_loans": cancelled_loans,
            "total_fines": total_fines,
        }

    async def generate_loans_csv(
        self,
        status: LoanStatus | None = None,
        user_id: str | None = None,
        book_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        query = select(LoanModel)

        query = self._apply_loan_filters(
            query=query,
            status=status,
            user_id=user_id,
            book_id=book_id,
            start_date=start_date,
            end_date=end_date,
        )

        result = await self.db.execute(query)
        loans = result.scalars().all()

        output = StringIO()
        writer = csv.writer(output)

        writer.writerow(
            [
                "id",
                "user_id",
                "book_id",
                "loan_date",
                "due_date",
                "returned_at",
                "cancelled_at",
                "status",
                "fine_amount",
                "renewal_count",
            ]
        )

        for loan in loans:
            writer.writerow(
                [
                    str(loan.id),
                    str(loan.user_id),
                    str(loan.book_id),
                    loan.loan_date.isoformat() if loan.loan_date else "",
                    loan.due_date.isoformat() if loan.due_date else "",
                    loan.returned_at.isoformat() if loan.returned_at else "",
                    loan.cancelled_at.isoformat() if loan.cancelled_at else "",
                    loan.status.value,
                    float(loan.fine_amount),
                    loan.renewal_count,
                ]
            )

        return output.getvalue()

    async def generate_fines_pdf(
        self,
        user_id: str | None = None,
        book_id: str | None = None,
        min_amount: float | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        query = select(LoanModel).where(LoanModel.fine_amount > 0)

        query = self._apply_loan_filters(
            query=query,
            user_id=user_id,
            book_id=book_id,
            start_date=start_date,
            end_date=end_date,
        )

        if min_amount is not None:
            query = query.where(LoanModel.fine_amount >= min_amount)

        result = await self.db.execute(query)
        loans = result.scalars().all()

        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=24,
            leftMargin=24,
            topMargin=24,
            bottomMargin=24,
        )

        styles = getSampleStyleSheet()
        elements = []

        elements.append(
            Paragraph("Relatório de Multas", styles["Title"])
        )

        elements.append(Spacer(1, 12))

        total = sum(float(loan.fine_amount) for loan in loans)

        elements.append(
            Paragraph(
                f"Total de registros: {len(loans)} | Total de multas: R$ {total:.2f}",
                styles["Normal"],
            )
        )

        elements.append(Spacer(1, 12))

        if not loans:
            elements.append(
                Paragraph("Nenhuma multa encontrada para os filtros informados.", styles["Normal"])
            )
        else:
            data = [
                [
                    "Loan ID",
                    "User ID",
                    "Book ID",
                    "Status",
                    "Due Date",
                    "Returned At",
                    "Fine",
                ]
            ]

            for loan in loans:
                data.append(
                    [
                        Paragraph(str(loan.id), styles["BodyText"]),
                        Paragraph(str(loan.user_id), styles["BodyText"]),
                        Paragraph(str(loan.book_id), styles["BodyText"]),
                        loan.status.value,
                        loan.due_date.strftime("%Y-%m-%d") if loan.due_date else "",
                        loan.returned_at.strftime("%Y-%m-%d") if loan.returned_at else "",
                        f"R$ {float(loan.fine_amount):.2f}",
                    ]
                )

            table = Table(
                data,
                colWidths=[120, 120, 120, 65, 75, 75, 65],
                repeatRows=1,
            )

            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 7),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )

            elements.append(table)

        doc.build(elements)

        buffer.seek(0)

        return buffer