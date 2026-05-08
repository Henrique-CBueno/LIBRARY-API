from datetime import datetime


class FineCalculator:
    DAILY_FINE_AMOUNT = 2.0

    def calculate_days_late(
        self,
        due_date: datetime,
        reference_date: datetime | None = None,
    ) -> int:
        reference_date = reference_date or datetime.utcnow()

        if reference_date <= due_date:
            return 0

        return (
            reference_date.date()
            - due_date.date()
        ).days

    def calculate_amount(
        self,
        due_date: datetime,
        reference_date: datetime | None = None,
    ) -> float:
        days_late = self.calculate_days_late(
            due_date,
            reference_date,
        )

        return days_late * self.DAILY_FINE_AMOUNT