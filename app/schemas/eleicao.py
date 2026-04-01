from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.eleicao import TipoEleicao, StatusEleicao


class EleicaoBase(BaseModel):
    titulo: str
    descricao: Optional[str] = None
    tipo: TipoEleicao
    data_inicio: datetime
    data_fim: datetime
    exige_mfa: bool = True
    permite_voto_branco: bool = True
    max_votos: int = 1


class EleicaoCreate(EleicaoBase):
    pass


class EleicaoUpdate(BaseModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    tipo: Optional[TipoEleicao] = None
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    status: Optional[StatusEleicao] = None
    exige_mfa: Optional[bool] = None
    permite_voto_branco: Optional[bool] = None
    max_votos: Optional[int] = None


class EleicaoResponse(EleicaoBase):
    id: int
    status: StatusEleicao
    created_at: datetime
    total_candidatos: Optional[int] = 0
    total_votos: Optional[int] = 0
    total_cooperados: Optional[int] = 0

    class Config:
        from_attributes = True


class EleicaoDetalhe(EleicaoResponse):
    candidatos: List["CandidatoResponse"] = []
    chapas: List["ChapaResponse"] = []
    pautas: List["PautaResponse"] = []


from app.schemas.candidato import CandidatoResponse
from app.schemas.chapa import ChapaResponse
from app.schemas.pauta import PautaResponse

EleicaoDetalhe.model_rebuild()
