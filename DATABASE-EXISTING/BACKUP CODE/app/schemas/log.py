from datetime import datetime

from pydantic import BaseModel


# ==================================
# Skema untuk System Log
# ==================================
class SystemLogBase(BaseModel):
    level: str
    message: str


class SystemLog(SystemLogBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True


# ==================================
# Skema untuk Activity Log
# ==================================
class ActivityLogBase(BaseModel):
    user_id: int
    action: str
    details: str | None = None


class ActivityLog(ActivityLogBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True
