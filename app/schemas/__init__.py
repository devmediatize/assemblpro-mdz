from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse
from app.schemas.cooperado import CooperadoCreate, CooperadoUpdate, CooperadoResponse
from app.schemas.eleicao import EleicaoCreate, EleicaoUpdate, EleicaoResponse
from app.schemas.candidato import CandidatoCreate, CandidatoUpdate, CandidatoResponse
from app.schemas.chapa import ChapaCreate, ChapaUpdate, ChapaResponse
from app.schemas.pauta import PautaCreate, PautaUpdate, PautaResponse
from app.schemas.voto import VotoCreate, VotoResponse, ComprovanteVoto
from app.schemas.auth import LoginRequest, TokenResponse, OTPVerifyRequest

__all__ = [
    "UsuarioCreate", "UsuarioUpdate", "UsuarioResponse",
    "CooperadoCreate", "CooperadoUpdate", "CooperadoResponse",
    "EleicaoCreate", "EleicaoUpdate", "EleicaoResponse",
    "CandidatoCreate", "CandidatoUpdate", "CandidatoResponse",
    "ChapaCreate", "ChapaUpdate", "ChapaResponse",
    "PautaCreate", "PautaUpdate", "PautaResponse",
    "VotoCreate", "VotoResponse", "ComprovanteVoto",
    "LoginRequest", "TokenResponse", "OTPVerifyRequest"
]
