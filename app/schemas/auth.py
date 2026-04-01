from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    cpf: Optional[str] = None
    email: Optional[str] = None
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_type: str  # 'admin' ou 'cooperado'
    user_id: int
    nome: str
    requires_otp: bool = False


class OTPVerifyRequest(BaseModel):
    codigo: str
    temp_token: str


class OTPSendRequest(BaseModel):
    metodo: str = "email"  # email ou sms


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AlterarSenhaRequest(BaseModel):
    senha_atual: str
    nova_senha: str
    confirmar_senha: str
