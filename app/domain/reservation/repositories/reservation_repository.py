from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domain.reservation.models.reservation_model import ReservationModel, ReservationStatus


class ReservationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, reservation: ReservationModel):
        self.db.add(reservation)
        await self.db.commit()
        await self.db.refresh(reservation)

        return reservation

    async def find_by_id(self, reservation_id: str):
        query = (
            select(ReservationModel)
            .options(
                joinedload(ReservationModel.user),
                joinedload(ReservationModel.book),
            )
            .where(ReservationModel.id == reservation_id)
        )

        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def find_active_by_user_and_book(
        self,
        user_id: str,
        book_id: str,
    ):
        query = (
            select(ReservationModel)
            .where(ReservationModel.user_id == user_id)
            .where(ReservationModel.book_id == book_id)
            .where(ReservationModel.status == ReservationStatus.ACTIVE)
        )

        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def exists_active_for_book(self, book_id: str):
        query = (
            select(ReservationModel)
            .where(ReservationModel.book_id == book_id)
            .where(ReservationModel.status == ReservationStatus.ACTIVE)
            .limit(1)
        )

        result = await self.db.execute(query)

        return result.scalar_one_or_none() is not None

    async def list_paginated(
        self,
        page: int,
        size: int,
        user_id: str | None = None,
        book_id: str | None = None,
        status: ReservationStatus | None = None,
    ):
        offset = (page - 1) * size

        query = select(ReservationModel)
        count_query = select(func.count()).select_from(ReservationModel)

        filters = []

        if user_id:
            filters.append(ReservationModel.user_id == user_id)

        if book_id:
            filters.append(ReservationModel.book_id == book_id)

        if status:
            filters.append(ReservationModel.status == status)

        for item in filters:
            query = query.where(item)
            count_query = count_query.where(item)

        query = (
            query
            .order_by(ReservationModel.created_at.asc())
            .offset(offset)
            .limit(size)
        )

        result = await self.db.execute(query)
        total_result = await self.db.execute(count_query)

        return result.scalars().all(), total_result.scalar() or 0

    async def update(self, reservation: ReservationModel):
        await self.db.commit()
        await self.db.refresh(reservation)

        return reservation