from datetime import datetime

from pydantic import BaseModel

from app.domain.reservation.models.reservation_model import ReservationStatus


class CreateReservationSchema(BaseModel):
    user_id: str
    book_id: str


class ReservationResponseSchema(BaseModel):
    id: str
    user_id: str
    book_id: str
    status: ReservationStatus
    created_at: datetime
    cancelled_at: datetime | None
    fulfilled_at: datetime | None

    model_config = {
        "from_attributes": True
    }


class CancelReservationResponseSchema(BaseModel):
    id: str
    status: ReservationStatus
    cancelled_at: datetime