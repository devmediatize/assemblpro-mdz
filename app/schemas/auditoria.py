from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class LogAuditoriaBase(BaseModel):
    tipo: str
    descricao: Optional[str] = None
    usuario_id: Optional[int] = None
    cooperado_id: Optional[int] = None
    eleicao_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    dados_json: Optional[dict] = None


class LogAuditoriaCreate(LogAuditoriaBase):
    pass


class LogAuditoriaResponse(LogAuditoriaBase):
    id: int
    hash_integridade: str
    created_at: datetime
    usuario_nome: Optional[str] = None
    cooperado_nome: Optional[str] = None
    eleicao_titulo: Optional[str] = None

    class Config:
        from_attributes = True


class LogAuditoriaFilter(BaseModel):
    tipo: Optional[str] = None
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    eleicao_id: Optional[int] = None
    usuario_id: Optional[int] = None
    cooperado_id: Optional[int] = None
