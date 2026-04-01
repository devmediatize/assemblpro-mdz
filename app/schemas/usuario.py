from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UsuarioBase(BaseModel):
    nome: str
    email: EmailStr


class UsuarioCreate(UsuarioBase):
    senha: str
    is_admin: bool = False


class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    senha: Optional[str] = None
    ativo: Optional[bool] = None
    is_admin: Optional[bool] = None
    tema: Optional[str] = None


class UsuarioResponse(UsuarioBase):
    id: int
    ativo: bool
    is_admin: bool
    tema: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
