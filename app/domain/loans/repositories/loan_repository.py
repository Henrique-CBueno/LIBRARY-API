from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domain.books.models.book_model import BookModel
from app.domain.loans.models.loan_model import LoanModel, LoanStatus


class LoanRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        loan: LoanModel,
    ):
        self.db.add(loan)

        await self.db.flush()
        await self.db.refresh(loan)

        return loan

    async def find_by_id(
        self,
        loan_id: str,
    ):
        query = (
            select(LoanModel)
            .options(
                joinedload(LoanModel.book),
                joinedload(LoanModel.user),
            )
            .where(LoanModel.id == loan_id)
        )

        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def count_active_by_user(
        self,
        user_id: str,
    ):
        query = (
            select(func.count())
            .select_from(LoanModel)
            .where(LoanModel.user_id == user_id)
            .where(LoanModel.status == LoanStatus.ACTIVE)
        )

        result = await self.db.execute(query)

        return result.scalar() or 0

    async def get_book_for_update(
        self,
        book_id: str,
    ):
        query = (
            select(BookModel)
            .where(BookModel.id == book_id)
            .where(BookModel.is_active.is_(True))
            .with_for_update()
        )

        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def find_active_by_id_for_update(
        self,
        loan_id: str,
    ):
        query = (
            select(LoanModel)
            .where(LoanModel.id == loan_id)
            .where(LoanModel.status == LoanStatus.ACTIVE)
            .with_for_update()
        )

        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def list_active(self):
        query = (
            select(LoanModel)
            .options(
                joinedload(LoanModel.book),
                joinedload(LoanModel.user),
            )
            .where(LoanModel.status == LoanStatus.ACTIVE)
        )

        result = await self.db.execute(query)

        return result.scalars().all()

    async def list_overdue(self):
        now = datetime.utcnow()

        query = (
            select(LoanModel)
            .options(
                joinedload(LoanModel.book),
                joinedload(LoanModel.user),
            )
            .where(LoanModel.status == LoanStatus.ACTIVE)
            .where(LoanModel.due_date < now)
        )

        result = await self.db.execute(query)

        return result.scalars().all()

    async def list_by_user(
        self,
        user_id: str,
    ):
        query = (
            select(LoanModel)
            .options(
                joinedload(LoanModel.book),
                joinedload(LoanModel.user),
            )
            .where(LoanModel.user_id == user_id)
        )

        result = await self.db.execute(query)

        return result.scalars().all()

    async def list_paginated(
            self,
            page: int,
            size: int,
            user_id: str | None = None,
            book_id: str | None = None,
            status: LoanStatus | None = None,
            overdue: bool | None = None,
    ):
        offset = (page - 1) * size
        now = datetime.utcnow()

        query = select(LoanModel).options(
            joinedload(LoanModel.book),
            joinedload(LoanModel.user),
        )

        count_query = select(func.count()).select_from(LoanModel)

        filters = []

        if user_id:
            filters.append(LoanModel.user_id == user_id)

        if book_id:
            filters.append(LoanModel.book_id == book_id)

        if status:
            filters.append(LoanModel.status == status)

        if overdue is True:
            filters.append(LoanModel.status == LoanStatus.ACTIVE)
            filters.append(LoanModel.due_date < now)

        if overdue is False:
            filters.append(
                (LoanModel.status != LoanStatus.ACTIVE)
                | (LoanModel.due_date >= now)
            )

        for filter_item in filters:
            query = query.where(filter_item)
            count_query = count_query.where(filter_item)

        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        total_result = await self.db.execute(count_query)

        return result.scalars().all(), total_result.scalar() or 0

    async def update(
            self,
            loan: LoanModel,
    ):
        await self.db.commit()
        await self.db.refresh(loan)

        return loan

    async def find_by_user_paginated(
            self,
            user_id: str,
            page: int,
            size: int,
            status: LoanStatus | None = None,
    ):
        return await self.list_paginated(
            page=page,
            size=size,
            user_id=user_id,
            status=status,
        )
