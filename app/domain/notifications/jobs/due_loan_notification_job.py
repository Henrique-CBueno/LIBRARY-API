from datetime import date, timedelta

import structlog

from app.domain.loans.repositories.loan_repository import LoanRepository
from app.domain.notifications.models.notification_model import NotificationType
from app.domain.notifications.services.notification_service import NotificationService

logger = structlog.get_logger()


class DueLoanNotificationJob:
    def __init__(
        self,
        loan_repository: LoanRepository,
        notification_service: NotificationService,
    ):
        self.loan_repository = loan_repository
        self.notification_service = notification_service

    async def execute(self):
        logger.info("due_loan_notification_job_started")

        today = date.today()
        due_soon_date = today + timedelta(days=2)

        due_soon_loans = await self.loan_repository.list_due_on_date(
            due_soon_date,
        )

        for loan in due_soon_loans:
            await self.notification_service.send_once_per_day(
                user_id=loan.user_id,
                loan_id=loan.id,
                notification_type=NotificationType.LOAN_DUE_SOON,
                message="Seu empréstimo vence em 2 dias.",
            )

        due_today_loans = await self.loan_repository.list_due_on_date(
            today,
        )

        for loan in due_today_loans:
            await self.notification_service.send_once_per_day(
                user_id=loan.user_id,
                loan_id=loan.id,
                notification_type=NotificationType.LOAN_DUE_TODAY,
                message="Seu empréstimo vence hoje.",
            )

        overdue_loans = await self.loan_repository.list_overdue_for_notifications()

        for loan in overdue_loans:
            await self.notification_service.send_once_per_day(
                user_id=loan.user_id,
                loan_id=loan.id,
                notification_type=NotificationType.LOAN_OVERDUE,
                message="Seu empréstimo está atrasado. Regularize a devolução.",
            )

        logger.info("due_loan_notification_job_finished")