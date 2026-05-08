from datetime import datetime

from pydantic import BaseModel

from app.domain.notifications.models.notification_model import NotificationType, NotificationStatus


class NotificationResponseSchema(BaseModel):
    id: str
    user_id: str
    loan_id: str | None
    reservation_id: str | None
    type: NotificationType
    status: NotificationStatus
    channel: str
    message: str
    sent_at: datetime | None
    created_at: datetime

    model_config = {
        "from_attributes": True
    }
