from app.domain.notifications.models.notification_model import NotificationType
from app.domain.notifications.services.notification_service import NotificationService
from app.events.reservations.events import (
    ReservationCancelledEvent,
    ReservationCreatedEvent,
)


class ReservationCreatedNotificationHandler:
    def __init__(
        self,
        notification_service: NotificationService,
    ):
        self.notification_service = notification_service

    async def handle(
        self,
        event: ReservationCreatedEvent,
    ):
        await self.notification_service.send_notification(
            user_id=event.user_id,
            reservation_id=event.reservation_id,
            notification_type=NotificationType.RESERVATION_CREATED,
            message=(
                "Reserva criada com sucesso. "
                "Avisaremos quando o livro estiver disponivel."
            ),
        )


class ReservationCancelledNotificationHandler:
    def __init__(
        self,
        notification_service: NotificationService,
    ):
        self.notification_service = notification_service

    async def handle(
        self,
        event: ReservationCancelledEvent,
    ):
        await self.notification_service.send_notification(
            user_id=event.user_id,
            reservation_id=event.reservation_id,
            notification_type=NotificationType.RESERVATION_CANCELLED,
            message="Reserva cancelada com sucesso.",
        )
