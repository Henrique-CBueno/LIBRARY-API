from dataclasses import dataclass

from app.events.base import DomainEvent


@dataclass
class ReservationCreatedEvent(DomainEvent):
    reservation_id: str
    user_id: str
    book_id: str


@dataclass
class ReservationCancelledEvent(DomainEvent):
    reservation_id: str
    user_id: str
    book_id: str
