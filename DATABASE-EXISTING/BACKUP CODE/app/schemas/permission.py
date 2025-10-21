from pydantic import BaseModel


class PermissionCreate(BaseModel):
    name: str

    class Config:
        from_attributes = True


class Permission(PermissionCreate):
    id: int

    class Config:
        from_attributes = True


class Permission(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
