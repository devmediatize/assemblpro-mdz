from pydantic import BaseModel
from typing import Optional


class CandidatoBase(BaseModel):
    nome: str
    cargo: Optional[str] = None
    descricao: Optional[str] = None
    foto_url: Optional[str] = None
    ordem: int = 0


class CandidatoCreate(CandidatoBase):
    eleicao_id: int
    chapa_id: Optional[int] = None


class CandidatoUpdate(BaseModel):
    nome: Optional[str] = None
    cargo: Optional[str] = None
    descricao: Optional[str] = None
    foto_url: Optional[str] = None
    chapa_id: Optional[int] = None
    ordem: Optional[int] = None


class CandidatoResponse(CandidatoBase):
    id: int
    eleicao_id: int
    chapa_id: Optional[int] = None
    total_votos: Optional[int] = 0

    class Config:
        from_attributes = True
