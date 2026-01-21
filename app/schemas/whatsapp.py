from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class WhatsAppReminderResponse(BaseModel):
    success: bool
    message: str
    qontak_response: Optional[dict] = None
    timestamp: datetime = datetime.utcnow()
