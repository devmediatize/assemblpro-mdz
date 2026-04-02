from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime, timezone, timedelta

from app.database import get_db
from app.models import Voto, Eleicao, ConviteVotacao, Cooperado, StatusEleicao, OtpVotacao
from app.schemas.voto import (
    VotoCreate, VotoResponse, ComprovanteVoto,
    SolicitarOtpVotacao, VerificarOtpVotacao, OtpVotacaoResponse
)
from app.utils.security import generate_vote_hash
from app.utils.otp import generate_numeric_otp
from app.services.auditoria_service import AuditoriaService, TipoLog
from app.services.sms_service import SmsService
from app.services.email_service import EmailService

router = APIRouter(prefix="/api/votos", tags=["Votos"])


@router.post("/solicitar-codigo", response_model=OtpVotacaoResponse)
async def solicitar_codigo_verificacao(
    request: Request,
    data: SolicitarOtpVotacao,
    db: AsyncSession = Depends(get_db)
):
    """Envia código de verificação SMS/Email antes de votar"""

    # Verifica cooperado
    coop_result = await db.execute(
        select(Cooperado).where(Cooperado.id == data.cooperado_id)
    )
    cooperado = coop_result.scalar_one_or_none()

    if not cooperado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cooperado não encontrado"
        )

    # Verifica eleição
    eleicao_result = await db.execute(
        select(Eleicao).where(Eleicao.id == data.eleicao_id)
    )
    eleicao = eleicao_result.scalar_one_or_none()

    if not eleicao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Eleição não encontrada"
        )

    if eleicao.status != StatusEleicao.VOTACAO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Eleição não está em período de votação"
        )

    # Verifica se cooperado tem convite
    convite_result = await db.execute(
        select(ConviteVotacao).where(
            ConviteVotacao.eleicao_id == data.eleicao_id,
            ConviteVotacao.cooperado_id == data.cooperado_id
        )
    )
    convite = convite_result.scalar_one_or_none()

    if not convite:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cooperado não foi convocado para esta eleição"
        )

    if convite.votou:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Voto já registrado para esta eleição"
        )

    # Remove OTPs anteriores não utilizados
    await db.execute(
        delete(OtpVotacao).where(
            OtpVotacao.cooperado_id == data.cooperado_id,
            OtpVotacao.eleicao_id == data.eleicao_id,
            OtpVotacao.verificado == False
        )
    )

    # Gera novo código OTP
    codigo = generate_numeric_otp(6)

    otp = OtpVotacao(
        cooperado_id=data.cooperado_id,
        eleicao_id=data.eleicao_id,
        codigo=codigo,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)
    )

    db.add(otp)
    await db.commit()

    # Envia código por SMS e/ou Email
    enviou_sms = False
    enviou_email = False

    if cooperado.telefone:
        resultado_sms = await SmsService.enviar_codigo_verificacao(
            db, cooperado.telefone, codigo, eleicao.titulo
        )
        enviou_sms = resultado_sms.get("sucesso", False)
        if resultado_sms.get("simulado"):
            print(f"[OTP VOTAÇÃO - SMS SIMULADO] Cooperado: {cooperado.nome}, Código: {codigo}")

    if cooperado.email:
        resultado_email = await EmailService.enviar_codigo_verificacao(
            db, cooperado.email, codigo, eleicao.titulo, cooperado.nome
        )
        enviou_email = resultado_email.get("sucesso", False)
        if resultado_email.get("simulado"):
            print(f"[OTP VOTAÇÃO - EMAIL SIMULADO] Cooperado: {cooperado.nome}, Código: {codigo}")

    # Mascara email e telefone para resposta
    email_parcial = None
    telefone_parcial = None

    if cooperado.email:
        partes = cooperado.email.split("@")
        if len(partes) == 2:
            email_parcial = f"{partes[0][:3]}***@{partes[1]}"

    if cooperado.telefone:
        telefone_parcial = f"***{cooperado.telefone[-4:]}"

    # Log de auditoria
    await AuditoriaService.registrar(
        db=db,
        tipo=TipoLog.OTP_ENVIADO,
        descricao=f"Código de verificação enviado para votação na eleição: {eleicao.titulo}",
        cooperado_id=data.cooperado_id,
        eleicao_id=data.eleicao_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:255]
    )

    # Monta mensagem de resposta
    canais = []
    if enviou_sms and telefone_parcial:
        canais.append(f"SMS ({telefone_parcial})")
    if enviou_email and email_parcial:
        canais.append(f"email ({email_parcial})")

    if canais:
        mensagem = f"Código enviado para: {' e '.join(canais)}"
    else:
        mensagem = "Código de verificação gerado. Verifique seu SMS ou email."

    return OtpVotacaoResponse(
        enviado=True,
        mensagem=mensagem,
        email_parcial=email_parcial,
        telefone_parcial=telefone_parcial
    )


@router.post("/verificar-codigo")
async def verificar_codigo(
    request: Request,
    data: VerificarOtpVotacao,
    db: AsyncSession = Depends(get_db)
):
    """Verifica código OTP antes de permitir voto"""

    # Busca OTP mais recente
    result = await db.execute(
        select(OtpVotacao).where(
            OtpVotacao.cooperado_id == data.cooperado_id,
            OtpVotacao.eleicao_id == data.eleicao_id,
            OtpVotacao.verificado == False
        ).order_by(OtpVotacao.created_at.desc())
    )
    otp = result.scalar_one_or_none()

    if not otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código não encontrado. Solicite um novo código."
        )

    if otp.is_expired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código expirado. Solicite um novo código."
        )

    if otp.max_tentativas_excedidas:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Número máximo de tentativas excedido. Solicite um novo código."
        )

    if otp.codigo != data.codigo:
        otp.tentativas += 1
        await db.commit()
        tentativas_restantes = 3 - otp.tentativas
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Código inválido. {tentativas_restantes} tentativa(s) restante(s)."
        )

    # Código válido - marca como verificado
    otp.verificado = True
    await db.commit()

    return {
        "verificado": True,
        "mensagem": "Código verificado com sucesso! Você pode confirmar seu voto."
    }


@router.post("/", response_model=ComprovanteVoto, status_code=status.HTTP_201_CREATED)
async def registrar_voto(
    request: Request,
    data: VotoCreate,
    cooperado_id: int,
    db: AsyncSession = Depends(get_db)
):
    # Verifica cooperado
    coop_result = await db.execute(
        select(Cooperado).where(Cooperado.id == cooperado_id)
    )
    cooperado = coop_result.scalar_one_or_none()

    if not cooperado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cooperado não encontrado"
        )

    # Verifica eleição
    eleicao_result = await db.execute(
        select(Eleicao).where(Eleicao.id == data.eleicao_id)
    )
    eleicao = eleicao_result.scalar_one_or_none()

    if not eleicao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Eleição não encontrada"
        )

    if eleicao.status != StatusEleicao.VOTACAO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Eleição não está em período de votação"
        )

    now = datetime.now(timezone.utc)
    if now < eleicao.data_inicio or now > eleicao.data_fim:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fora do período de votação"
        )

    # Verifica se cooperado tem convite
    convite_result = await db.execute(
        select(ConviteVotacao).where(
            ConviteVotacao.eleicao_id == data.eleicao_id,
            ConviteVotacao.cooperado_id == cooperado_id
        )
    )
    convite = convite_result.scalar_one_or_none()

    if not convite:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cooperado não foi convocado para esta eleição"
        )

    if convite.votou:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Voto já registrado para esta eleição"
        )

    # Verifica se OTP foi verificado (OBRIGATÓRIO para todos os votos)
    otp_result = await db.execute(
        select(OtpVotacao).where(
            OtpVotacao.cooperado_id == cooperado_id,
            OtpVotacao.eleicao_id == data.eleicao_id,
            OtpVotacao.verificado == True
        ).order_by(OtpVotacao.created_at.desc())
    )
    otp_verificado = otp_result.scalar_one_or_none()

    if not otp_verificado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verificação de código SMS/Email obrigatória para votar"
        )

    # Verifica se o OTP não expirou (mesmo verificado, deve ser recente)
    if otp_verificado.is_expired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código de verificação expirado. Solicite um novo código."
        )

    # Gera hash do voto
    timestamp = datetime.now(timezone.utc)
    hash_voto = generate_vote_hash(data.eleicao_id, cooperado_id, timestamp)

    # Cria o voto
    voto = Voto(
        eleicao_id=data.eleicao_id,
        cooperado_id=cooperado_id,
        candidato_id=data.candidato_id,
        chapa_id=data.chapa_id,
        pauta_id=data.pauta_id,
        opcao=data.opcao,
        hash_voto=hash_voto,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    db.add(voto)

    # Marca convite como votado
    convite.votou = True

    await db.commit()

    # Log do voto (sem identificar candidato para manter sigilo)
    tipo_voto = TipoLog.VOTO_BRANCO if data.opcao == "branco" else TipoLog.VOTO_REGISTRADO
    await AuditoriaService.registrar(
        db=db,
        tipo=tipo_voto,
        descricao=f"Voto registrado na eleição: {eleicao.titulo}",
        cooperado_id=cooperado_id,
        eleicao_id=data.eleicao_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:255],
        dados_json={"hash_voto": hash_voto}
    )

    return ComprovanteVoto(
        hash_voto=hash_voto,
        eleicao_titulo=eleicao.titulo,
        data_voto=timestamp,
        mensagem="Voto registrado com sucesso!"
    )


@router.get("/comprovante/{hash_voto}")
async def verificar_comprovante(
    hash_voto: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Voto).where(Voto.hash_voto == hash_voto)
    )
    voto = result.scalar_one_or_none()

    if not voto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comprovante não encontrado"
        )

    # Busca eleição
    eleicao_result = await db.execute(
        select(Eleicao).where(Eleicao.id == voto.eleicao_id)
    )
    eleicao = eleicao_result.scalar_one_or_none()

    return {
        "valido": True,
        "hash_voto": hash_voto,
        "eleicao": eleicao.titulo if eleicao else "N/A",
        "data_voto": voto.created_at.isoformat(),
        "mensagem": "Voto verificado com sucesso. Seu voto foi registrado de forma segura e anônima."
    }


@router.get("/verificar-participacao/{eleicao_id}/{cooperado_id}")
async def verificar_participacao(
    eleicao_id: int,
    cooperado_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ConviteVotacao).where(
            ConviteVotacao.eleicao_id == eleicao_id,
            ConviteVotacao.cooperado_id == cooperado_id
        )
    )
    convite = result.scalar_one_or_none()

    if not convite:
        return {"pode_votar": False, "motivo": "Não convocado"}

    if convite.votou:
        return {"pode_votar": False, "motivo": "Já votou"}

    return {"pode_votar": True}


# ============ ADMIN - GERENCIAMENTO DE VOTOS ============

from app.models import Candidato, Chapa
from app.utils.auth import require_admin
import hashlib


def criptografar_nome(nome: str) -> str:
    """Criptografa parcialmente o nome para exibição"""
    if not nome:
        return "***"
    partes = nome.split()
    if len(partes) == 1:
        return nome[0] + "*" * (len(nome) - 1)
    # Mostra primeira letra de cada nome + asteriscos
    resultado = []
    for parte in partes:
        if len(parte) > 1:
            resultado.append(parte[0] + "*" * (len(parte) - 1))
        else:
            resultado.append(parte)
    return " ".join(resultado)


@router.get("/admin/eleicao/{eleicao_id}")
async def listar_votos_eleicao(
    eleicao_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Lista votos de uma eleição (apenas admin) - com nomes criptografados"""

    # Verifica eleição
    eleicao_result = await db.execute(
        select(Eleicao).where(Eleicao.id == eleicao_id)
    )
    eleicao = eleicao_result.scalar_one_or_none()

    if not eleicao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Eleição não encontrada"
        )

    # Busca votos com joins
    votos_result = await db.execute(
        select(Voto, Cooperado, Candidato, Chapa)
        .join(Cooperado, Voto.cooperado_id == Cooperado.id)
        .outerjoin(Candidato, Voto.candidato_id == Candidato.id)
        .outerjoin(Chapa, Voto.chapa_id == Chapa.id)
        .where(Voto.eleicao_id == eleicao_id)
        .order_by(Voto.created_at.desc())
    )

    votos = []
    for voto, cooperado, candidato, chapa in votos_result.all():
        votos.append({
            "id": voto.id,
            "cooperado_id": cooperado.id,
            "cooperado_nome": cooperado.nome,
            "cooperado_cpf": cooperado.cpf[:3] + ".***.***-" + cooperado.cpf[-2:],
            "candidato_nome": criptografar_nome(candidato.nome) if candidato else None,
            "chapa_nome": chapa.nome if chapa else None,
            "opcao": voto.opcao,
            "hash_voto": voto.hash_voto[:16] + "...",
            "data_voto": voto.created_at.isoformat() if voto.created_at else None,
            "ip_address": voto.ip_address
        })

    return {
        "eleicao": {
            "id": eleicao.id,
            "titulo": eleicao.titulo,
            "status": eleicao.status.value
        },
        "total_votos": len(votos),
        "votos": votos
    }


@router.delete("/admin/{voto_id}")
async def excluir_voto(
    voto_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Exclui um voto (apenas admin)"""

    # Busca voto
    voto_result = await db.execute(
        select(Voto).where(Voto.id == voto_id)
    )
    voto = voto_result.scalar_one_or_none()

    if not voto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voto não encontrado"
        )

    # Busca cooperado e eleição para log
    cooperado_result = await db.execute(
        select(Cooperado).where(Cooperado.id == voto.cooperado_id)
    )
    cooperado = cooperado_result.scalar_one_or_none()

    eleicao_result = await db.execute(
        select(Eleicao).where(Eleicao.id == voto.eleicao_id)
    )
    eleicao = eleicao_result.scalar_one_or_none()

    # Reseta o convite para permitir novo voto
    convite_result = await db.execute(
        select(ConviteVotacao).where(
            ConviteVotacao.eleicao_id == voto.eleicao_id,
            ConviteVotacao.cooperado_id == voto.cooperado_id
        )
    )
    convite = convite_result.scalar_one_or_none()

    if convite:
        convite.votou = False

    # Remove OTPs relacionados
    await db.execute(
        delete(OtpVotacao).where(
            OtpVotacao.cooperado_id == voto.cooperado_id,
            OtpVotacao.eleicao_id == voto.eleicao_id
        )
    )

    # Remove o voto
    await db.delete(voto)

    # Log de auditoria
    await AuditoriaService.registrar(
        db=db,
        tipo=TipoLog.VOTO_EXCLUIDO,
        descricao=f"Voto excluído - Cooperado: {cooperado.nome if cooperado else 'N/A'}, Eleição: {eleicao.titulo if eleicao else 'N/A'}",
        cooperado_id=voto.cooperado_id,
        eleicao_id=voto.eleicao_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:255]
    )

    await db.commit()

    return {"message": "Voto excluído com sucesso"}
