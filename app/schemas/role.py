from pydantic import BaseModel
from typing import List, Optional
from .permission import Permission

# Impor skema Permission yang sudah Anda buat
from .permission import Permission


class RoleBase(BaseModel):
    name: str


# Skema untuk membuat Role baru, sekarang menerima list permission_ids
class RoleCreate(RoleBase):
    permission_ids: Optional[List[int]] = []


# Skema untuk update Role, juga menerima list permission_ids
class RoleUpdate(BaseModel):
    name: Optional[str] = None
    permission_ids: Optional[List[int]] = None


# Skema untuk response, akan menampilkan daftar permission yang terhubung
class Role(RoleBase):
    id: int
    permissions: List[Permission] = []  # Tampilkan list permission yang terhubung

    class Config:
        # Ganti orm_mode dengan from_attributes untuk Pydantic v2
        from_attributes = True
