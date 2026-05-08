import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.domain.loans.repositories.loan_repository import LoanRepository
from app.domain.notifications.jobs.due_loan_notification_job import DueLoanNotificationJob
from app.domain.notifications.repositories.notification_repository import NotificationRepository
from app.domain.notifications.services.notification_service import NotificationService
from app.infra.database.session import AsyncSessionLocal

scheduler = AsyncIOScheduler()


async def run_due_loan_notification_job():
    async with AsyncSessionLocal() as db:
        loan_repository = LoanRepository(db)

        notification_repository = NotificationRepository(db)

        notification_service = NotificationService(
            notification_repository,
        )

        job = DueLoanNotificationJob(
            loan_repository=loan_repository,
            notification_service=notification_service,
        )

        await job.execute()


def start_scheduler():
    scheduler.add_job(
        lambda: asyncio.create_task(
            run_due_loan_notification_job()
        ),
        trigger="cron",
        hour=8,
        minute=0,
        id="due_loan_notification_job",
        replace_existing=True,
    )

    scheduler.start()