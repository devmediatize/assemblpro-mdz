from pydantic import BaseModel
from typing import Optional, List


class ChapaBase(BaseModel):
    nome: str
    numero: int
    descricao: Optional[str] = None
    foto_url: Optional[str] = None


class ChapaCreate(ChapaBase):
    eleicao_id: int


class ChapaUpdate(BaseModel):
    nome: Optional[str] = None
    numero: Optional[int] = None
    descricao: Optional[str] = None
    foto_url: Optional[str] = None


class ChapaResponse(ChapaBase):
    id: int
    eleicao_id: int
    total_votos: Optional[int] = 0

    class Config:
        from_attributes = True


class ChapaDetalhe(ChapaResponse):
    candidatos: List["CandidatoResponse"] = []


from app.schemas.candidato import CandidatoResponse

ChapaDetalhe.model_rebuild()
