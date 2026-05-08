from dataclasses import dataclass

from app.events.base import DomainEvent


@dataclass
class LoanCreatedEvent(DomainEvent):
    loan_id: str
    user_id: str
    book_id: str


@dataclass
class LoanReturnedEvent(DomainEvent):
    loan_id: str
    user_id: str
    book_id: str


@dataclass
class LoanCancelledEvent(DomainEvent):
    loan_id: str
    user_id: str
    book_id: str