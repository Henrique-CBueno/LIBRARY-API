from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.notifications.repositories.notification_repository import NotificationRepository
from app.domain.notifications.services.notification_service import NotificationService
from app.events.bus import event_bus
from app.events.loans.events import LoanCreatedEvent, LoanReturnedEvent, LoanCancelledEvent
from app.events.loans.handlers.loan_notification_handler import LoanCreatedNotificationHandler, \
    LoanReturnedNotificationHandler, LoanCancelledNotificationHandler


def register_event_handlers(
    db: AsyncSession,
):
    notification_service = NotificationService(
        NotificationRepository(db)
    )

    event_bus.subscribe(
        LoanCreatedEvent,
        LoanCreatedNotificationHandler(
            notification_service
        ),
    )

    event_bus.subscribe(
        LoanReturnedEvent,
        LoanReturnedNotificationHandler(
            notification_service
        ),
    )

    event_bus.subscribe(
        LoanCancelledEvent,
        LoanCancelledNotificationHandler(
            notification_service
        ),
    )