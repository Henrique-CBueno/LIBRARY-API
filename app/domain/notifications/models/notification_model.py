import enum
import uuid6 as uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.database.Base import Base


class NotificationType(str, enum.Enum):
    LOAN_CREATED = "LOAN_CREATED"
    LOAN_RETURNED = "LOAN_RETURNED"
    LOAN_CANCELLED = "LOAN_CANCELLED"
    LOAN_DUE_SOON = "LOAN_DUE_SOON"
    LOAN_DUE_TODAY = "LOAN_DUE_TODAY"
    LOAN_OVERDUE = "LOAN_OVERDUE"


class NotificationStatus(str, enum.Enum):
    SENT = "SENT"
    FAILED = "FAILED"


class NotificationModel(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid7()),
    )

    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id"),
        nullable=False,
    )

    loan_id: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("loans.id"),
        nullable=True,
    )

    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType),
        nullable=False,
    )

    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus),
        default=NotificationStatus.SENT,
        nullable=False,
    )

    channel: Mapped[str] = mapped_column(
        String(50),
        default="EMAIL_FAKE",
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )