from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class CooperadoBase(BaseModel):
    nome: str
    cpf: str
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    regiao: Optional[str] = None
    matricula: Optional[str] = None


class CooperadoCreate(CooperadoBase):
    senha: str


class CooperadoUpdate(BaseModel):
    nome: Optional[str] = None
    cpf: Optional[str] = None
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    regiao: Optional[str] = None
    matricula: Optional[str] = None
    senha: Optional[str] = None
    ativo: Optional[bool] = None
    tema: Optional[str] = None


class CooperadoResponse(CooperadoBase):
    id: int
    ativo: bool
    tema: str
    otp_ativo: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CooperadoImport(BaseModel):
    nome: str
    cpf: str
    email: Optional[str] = None
    telefone: Optional[str] = None
    regiao: Optional[str] = None
    matricula: Optional[str] = None
