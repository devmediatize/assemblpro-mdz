from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta, datetime, timezone
from pydantic import BaseModel
import random
import string

from app.database import get_db
from app.models import Usuario, Cooperado, OtpVotacao
from app.schemas.auth import LoginRequest, TokenResponse, OTPVerifyRequest
from app.utils.security import verify_password, create_access_token, decode_token
from app.utils.otp import generate_otp, verify_otp, generate_otp_secret
from app.utils.validators import clean_cpf
from app.config import settings
from app.services.auditoria_service import AuditoriaService, TipoLog
from app.services.sms_service import SmsService
from app.services.email_service import EmailService

router = APIRouter(prefix="/api/auth", tags=["Autenticação"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    user = None
    user_type = None

    # Tenta login como admin (por email)
    if data.email:
        result = await db.execute(
            select(Usuario).where(Usuario.email == data.email)
        )
        user = result.scalar_one_or_none()
        user_type = "admin"

    # Tenta login como cooperado (por CPF)
    if data.cpf and not user:
        cpf = clean_cpf(data.cpf)
        result = await db.execute(
            select(Cooperado).where(Cooperado.cpf == cpf)
        )
        user = result.scalar_one_or_none()
        user_type = "cooperado"

    # Obter IP e User-Agent
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")[:255]

    if not user:
        # Log de falha
        await AuditoriaService.registrar(
            db=db,
            tipo=TipoLog.LOGIN_FALHA,
            descricao=f"Tentativa de login com credenciais invalidas: {data.email or data.cpf}",
            ip_address=ip_address,
            user_agent=user_agent
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas"
        )

    if not user.ativo:
        await AuditoriaService.registrar(
            db=db,
            tipo=TipoLog.LOGIN_FALHA,
            descricao=f"Tentativa de login com usuario inativo: {user.nome}",
            usuario_id=user.id if user_type == "admin" else None,
            cooperado_id=user.id if user_type == "cooperado" else None,
            ip_address=ip_address,
            user_agent=user_agent
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inativo"
        )

    if not verify_password(data.senha, user.senha_hash):
        await AuditoriaService.registrar(
            db=db,
            tipo=TipoLog.LOGIN_FALHA,
            descricao=f"Senha incorreta para: {user.nome}",
            usuario_id=user.id if user_type == "admin" else None,
            cooperado_id=user.id if user_type == "cooperado" else None,
            ip_address=ip_address,
            user_agent=user_agent
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas"
        )

    # Verifica se precisa de OTP (cooperado com MFA ativo)
    requires_otp = False
    if user_type == "cooperado" and user.otp_ativo:
        requires_otp = True
        # Gera token temporário para verificação OTP
        temp_token = create_access_token(
            data={"sub": str(user.id), "type": user_type, "temp": True},
            expires_delta=timedelta(minutes=5)
        )
        return TokenResponse(
            access_token=temp_token,
            expires_in=300,
            user_type=user_type,
            user_id=user.id,
            nome=user.nome,
            requires_otp=True
        )

    # Gera token de acesso completo
    access_token = create_access_token(
        data={"sub": str(user.id), "type": user_type}
    )

    # Log de login bem-sucedido
    await AuditoriaService.registrar(
        db=db,
        tipo=TipoLog.LOGIN_SUCESSO,
        descricao=f"Login realizado: {user.nome} ({user_type})",
        usuario_id=user.id if user_type == "admin" else None,
        cooperado_id=user.id if user_type == "cooperado" else None,
        ip_address=ip_address,
        user_agent=user_agent
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.JWT_EXPIRATION_MINUTES * 60,
        user_type=user_type,
        user_id=user.id,
        nome=user.nome,
        requires_otp=False
    )


@router.post("/verificar-otp", response_model=TokenResponse)
async def verificar_otp(
    data: OTPVerifyRequest,
    db: AsyncSession = Depends(get_db)
):
    payload = decode_token(data.temp_token)
    if not payload or not payload.get("temp"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token temporário inválido"
        )

    user_id = int(payload.get("sub"))
    user_type = payload.get("type")

    if user_type != "cooperado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP apenas para cooperados"
        )

    result = await db.execute(
        select(Cooperado).where(Cooperado.id == user_id)
    )
    cooperado = result.scalar_one_or_none()

    if not cooperado or not cooperado.otp_secret:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cooperado não encontrado"
        )

    if not verify_otp(cooperado.otp_secret, data.codigo):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código OTP inválido"
        )

    # Gera token de acesso completo
    access_token = create_access_token(
        data={"sub": str(cooperado.id), "type": "cooperado"}
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.JWT_EXPIRATION_MINUTES * 60,
        user_type="cooperado",
        user_id=cooperado.id,
        nome=cooperado.nome,
        requires_otp=False
    )


@router.post("/enviar-otp")
async def enviar_otp(
    temp_token: str,
    db: AsyncSession = Depends(get_db)
):
    payload = decode_token(temp_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )

    user_id = int(payload.get("sub"))

    result = await db.execute(
        select(Cooperado).where(Cooperado.id == user_id)
    )
    cooperado = result.scalar_one_or_none()

    if not cooperado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cooperado não encontrado"
        )

    if not cooperado.otp_secret:
        cooperado.otp_secret = generate_otp_secret()
        await db.commit()

    otp_code = generate_otp(cooperado.otp_secret)

    # TODO: Enviar OTP por email/SMS
    # Por enquanto, retorna o código (apenas em desenvolvimento)
    if settings.APP_ENV == "development":
        return {"message": "OTP enviado", "otp_debug": otp_code}

    return {"message": "OTP enviado para seu email/telefone"}


@router.post("/ativar-mfa")
async def ativar_mfa(
    cooperado_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Cooperado).where(Cooperado.id == cooperado_id)
    )
    cooperado = result.scalar_one_or_none()

    if not cooperado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cooperado não encontrado"
        )

    cooperado.otp_secret = generate_otp_secret()
    cooperado.otp_ativo = True
    await db.commit()

    return {"message": "MFA ativado com sucesso"}


# ============ LOGIN VIA CÓDIGO SMS/EMAIL ============

def mascara_telefone(telefone: str) -> str:
    """Mascara telefone: (65) *****-1234"""
    if not telefone:
        return None
    tel = telefone.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
    if tel.startswith("55"):
        tel = tel[2:]
    if len(tel) >= 10:
        ddd = tel[:2]
        final = tel[-4:]
        return f"({ddd}) *****-{final}"
    return "***"


def mascara_email(email: str) -> str:
    """Mascara email: c***@email.com"""
    if not email or "@" not in email:
        return None
    partes = email.split("@")
    usuario = partes[0]
    dominio = partes[1]
    if len(usuario) <= 2:
        mascarado = usuario[0] + "***"
    else:
        mascarado = usuario[0] + "***" + usuario[-1]
    return f"{mascarado}@{dominio}"


@router.get("/contatos-mascarados/{cpf}")
async def contatos_mascarados(
    cpf: str,
    db: AsyncSession = Depends(get_db)
):
    """Retorna telefone e email mascarados do cooperado"""
    cpf_limpo = clean_cpf(cpf)

    result = await db.execute(
        select(Cooperado).where(Cooperado.cpf == cpf_limpo)
    )
    cooperado = result.scalar_one_or_none()

    if not cooperado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CPF não encontrado"
        )

    return {
        "telefone": mascara_telefone(cooperado.telefone),
        "email": mascara_email(cooperado.email)
    }


class SolicitarCodigoLoginRequest(BaseModel):
    cpf: str


class VerificarCodigoLoginRequest(BaseModel):
    temp_token: str
    codigo: str


@router.post("/solicitar-codigo-login")
async def solicitar_codigo_login(
    request: Request,
    data: SolicitarCodigoLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Envia código de login via SMS/Email (login sem senha)"""
    cpf = clean_cpf(data.cpf)

    result = await db.execute(
        select(Cooperado).where(Cooperado.cpf == cpf)
    )
    cooperado = result.scalar_one_or_none()

    if not cooperado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CPF não encontrado"
        )

    if not cooperado.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inativo"
        )

    # Gera código de 6 dígitos
    codigo = ''.join(random.choices(string.digits, k=6))

    # Cria token temporário com o código embutido (hash)
    import hashlib
    codigo_hash = hashlib.sha256(codigo.encode()).hexdigest()

    temp_token = create_access_token(
        data={
            "sub": str(cooperado.id),
            "type": "cooperado",
            "login_otp": True,
            "codigo_hash": codigo_hash
        },
        expires_delta=timedelta(minutes=5)
    )

    # Envia código por SMS e/ou Email
    mensagem_envio = []

    if cooperado.telefone:
        resultado_sms = await SmsService.enviar_sms(
            db,
            cooperado.telefone,
            f"AssemblPro - Seu código de acesso é: {codigo}. Válido por 5 minutos."
        )
        if resultado_sms.get("sucesso"):
            mensagem_envio.append("SMS")

    if cooperado.email:
        # Busca URL base das configurações
        from app.models.configuracao import Configuracao
        base_url_result = await db.execute(
            select(Configuracao).where(Configuracao.chave == "baseUrl")
        )
        base_url_config = base_url_result.scalar_one_or_none()
        base_url = base_url_config.valor if base_url_config else "http://localhost:8033"
        logo_url = f"{base_url}/static/img/logo.png"

        resultado_email = await EmailService.enviar_email(
            db,
            cooperado.email,
            "AssemblPro - Código de Acesso",
            f"""
            <div style="font-family: Arial, sans-serif; background: #0a1628; padding: 30px; margin: 0;">
                <div style="max-width: 400px; margin: 0 auto; background: #111d32; border-radius: 12px; padding: 30px; text-align: center;">
                    <img src="{logo_url}" alt="Logo" style="max-height: 50px; margin-bottom: 15px;">
                    <h2 style="color: #00d4aa; margin-top: 0;">Código de Acesso</h2>
                    <p style="color: #ffffff;">Olá, <strong style="color: #00d4aa;">{cooperado.nome}</strong>!</p>
                    <p style="color: #ffffff;">Seu código de acesso é:</p>
                    <div style="background: #162236; padding: 20px; border-radius: 8px; font-size: 32px; letter-spacing: 8px; color: #00d4aa; font-weight: bold;">
                        {codigo}
                    </div>
                    <p style="color: #94a3b8; font-size: 14px; margin-top: 20px;">Válido por 5 minutos</p>
                    <p style="color: #64748b; font-size: 12px; margin-top: 30px;">© 2026 AssemblPro</p>
                </div>
            </div>
            """,
            f"AssemblPro - Seu código de acesso é: {codigo}. Válido por 5 minutos."
        )
        if resultado_email.get("sucesso"):
            mensagem_envio.append("Email")

    if not mensagem_envio:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível enviar o código. Verifique seu cadastro."
        )

    return {
        "temp_token": temp_token,
        "mensagem": f"Código enviado por {' e '.join(mensagem_envio)}"
    }


@router.post("/verificar-codigo-login", response_model=TokenResponse)
async def verificar_codigo_login(
    request: Request,
    data: VerificarCodigoLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Verifica código de login e retorna token de acesso"""
    payload = decode_token(data.temp_token)

    if not payload or not payload.get("login_otp"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado"
        )

    # Verifica o código
    import hashlib
    codigo_hash = hashlib.sha256(data.codigo.encode()).hexdigest()

    if codigo_hash != payload.get("codigo_hash"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código inválido"
        )

    cooperado_id = int(payload.get("sub"))

    result = await db.execute(
        select(Cooperado).where(Cooperado.id == cooperado_id)
    )
    cooperado = result.scalar_one_or_none()

    if not cooperado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cooperado não encontrado"
        )

    # Gera token de acesso completo
    access_token = create_access_token(
        data={"sub": str(cooperado.id), "type": "cooperado"}
    )

    # Log de login
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")[:255]

    await AuditoriaService.registrar(
        db=db,
        tipo=TipoLog.LOGIN_SUCESSO,
        descricao=f"Login via código: {cooperado.nome}",
        cooperado_id=cooperado.id,
        ip_address=ip_address,
        user_agent=user_agent
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.JWT_EXPIRATION_MINUTES * 60,
        user_type="cooperado",
        user_id=cooperado.id,
        nome=cooperado.nome,
        requires_otp=False
    )
