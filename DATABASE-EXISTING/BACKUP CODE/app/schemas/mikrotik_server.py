from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MikrotikServerBase(BaseModel):
    name: str
    host_ip: str
    username: str
    port: int = 8728
    is_active: bool = True


class MikrotikServerCreate(MikrotikServerBase):
    password: str  # Wajib ada saat membuat


class MikrotikServerUpdate(BaseModel):
    name: Optional[str] = None
    host_ip: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None  # Opsional saat update
    port: Optional[int] = None
    is_active: Optional[bool] = None


class MikrotikServer(MikrotikServerBase):
    id: int
    ros_version: Optional[str] = None
    last_connection_status: Optional[str] = None
    last_connected_at: Optional[datetime] = None

    class Config:
        from_attributes = True
