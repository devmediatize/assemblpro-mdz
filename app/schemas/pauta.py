from pydantic import BaseModel
from typing import Optional, List
from app.models.pauta import TipoVotoPauta


class PautaBase(BaseModel):
    titulo: str
    descricao: Optional[str] = None
    ordem: int = 0
    tipo_voto: TipoVotoPauta = TipoVotoPauta.SIM_NAO
    opcoes: Optional[str] = None  # JSON string para opções de múltipla escolha


class PautaCreate(PautaBase):
    eleicao_id: int


class PautaUpdate(BaseModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    ordem: Optional[int] = None
    tipo_voto: Optional[TipoVotoPauta] = None
    opcoes: Optional[str] = None


class PautaResponse(PautaBase):
    id: int
    eleicao_id: int
    votos_sim: Optional[int] = 0
    votos_nao: Optional[int] = 0
    votos_branco: Optional[int] = 0
    votos_abstencao: Optional[int] = 0

    class Config:
        from_attributes = True
