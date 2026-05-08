from app.domain.notifications.models.notification_model import NotificationType
from app.domain.notifications.services.notification_service import NotificationService
from app.events.loans.events import LoanCreatedEvent, LoanReturnedEvent, LoanCancelledEvent


class LoanCreatedNotificationHandler:
    def __init__(
        self,
        notification_service: NotificationService,
    ):
        self.notification_service = notification_service

    async def handle(
        self,
        event: LoanCreatedEvent,
    ):
        await self.notification_service.send_notification(
            user_id=event.user_id,
            loan_id=event.loan_id,
            notification_type=NotificationType.LOAN_CREATED,
            message=(
                "Empréstimo criado com sucesso. "
                "O prazo padrão de devolução é de 14 dias."
            ),
        )


class LoanReturnedNotificationHandler:
    def __init__(
        self,
        notification_service: NotificationService,
    ):
        self.notification_service = notification_service

    async def handle(
        self,
        event: LoanReturnedEvent,
    ):
        await self.notification_service.send_notification(
            user_id=event.user_id,
            loan_id=event.loan_id,
            notification_type=NotificationType.LOAN_RETURNED,
            message="Empréstimo devolvido com sucesso.",
        )


class LoanCancelledNotificationHandler:
    def __init__(
        self,
        notification_service: NotificationService,
    ):
        self.notification_service = notification_service

    async def handle(
        self,
        event: LoanCancelledEvent,
    ):
        await self.notification_service.send_notification(
            user_id=event.user_id,
            loan_id=event.loan_id,
            notification_type=NotificationType.LOAN_CANCELLED,
            message="Empréstimo cancelado com sucesso.",
        )