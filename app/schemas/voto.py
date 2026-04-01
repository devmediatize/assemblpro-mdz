from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class VotoCreate(BaseModel):
    eleicao_id: int
    candidato_id: Optional[int] = None
    chapa_id: Optional[int] = None
    pauta_id: Optional[int] = None
    opcao: Optional[str] = None  # 'sim', 'nao', 'branco', 'abstencao'
    codigo_otp: Optional[str] = None  # Código de verificação SMS/Email


class VotoResponse(BaseModel):
    id: int
    eleicao_id: int
    hash_voto: str
    created_at: datetime

    class Config:
        from_attributes = True


class ComprovanteVoto(BaseModel):
    hash_voto: str
    eleicao_titulo: str
    data_voto: datetime
    mensagem: str = "Voto registrado com sucesso!"


class VotoLote(BaseModel):
    eleicao_id: int
    votos: List[VotoCreate]


# Schemas para OTP de votação
class SolicitarOtpVotacao(BaseModel):
    eleicao_id: int
    cooperado_id: int


class VerificarOtpVotacao(BaseModel):
    eleicao_id: int
    cooperado_id: int
    codigo: str


class OtpVotacaoResponse(BaseModel):
    enviado: bool
    mensagem: str
    email_parcial: Optional[str] = None
    telefone_parcial: Optional[str] = None
