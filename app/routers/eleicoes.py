from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime, timezone

from app.database import get_db
from app.models import Eleicao, Candidato, Voto, ConviteVotacao, Cooperado, StatusEleicao
from app.schemas.eleicao import EleicaoCreate, EleicaoUpdate, EleicaoResponse, EleicaoDetalhe
from app.utils.security import generate_token
from app.services.auditoria_service import AuditoriaService, TipoLog

router = APIRouter(prefix="/api/eleicoes", tags=["Eleições"])


@router.get("/", response_model=List[EleicaoResponse])
async def listar_eleicoes(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Eleicao)

    if status_filter:
        query = query.where(Eleicao.status == status_filter)

    query = query.order_by(Eleicao.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    eleicoes = result.scalars().all()

    # Adiciona contagens
    response = []
    for eleicao in eleicoes:
        # Total candidatos
        cand_result = await db.execute(
            select(func.count(Candidato.id)).where(Candidato.eleicao_id == eleicao.id)
        )
        total_candidatos = cand_result.scalar()

        # Total votos
        votos_result = await db.execute(
            select(func.count(Voto.id)).where(Voto.eleicao_id == eleicao.id)
        )
        total_votos = votos_result.scalar()

        eleicao_dict = EleicaoResponse.model_validate(eleicao)
        eleicao_dict.total_candidatos = total_candidatos
        eleicao_dict.total_votos = total_votos

        response.append(eleicao_dict)

    return response


@router.post("/", response_model=EleicaoResponse, status_code=status.HTTP_201_CREATED)
async def criar_eleicao(
    data: EleicaoCreate,
    db: AsyncSession = Depends(get_db)
):
    if data.data_inicio >= data.data_fim:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data de início deve ser anterior à data de fim"
        )

    eleicao = Eleicao(**data.model_dump())
    db.add(eleicao)
    await db.commit()
    await db.refresh(eleicao)

    # Log da criacao
    await AuditoriaService.registrar(
        db=db,
        tipo=TipoLog.ELEICAO_CRIADA,
        descricao=f"Eleicao criada: {eleicao.titulo}",
        eleicao_id=eleicao.id,
        dados_json={"titulo": eleicao.titulo, "tipo": eleicao.tipo}
    )

    return eleicao


@router.get("/{eleicao_id}", response_model=EleicaoDetalhe)
async def obter_eleicao(
    eleicao_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Eleicao)
        .options(
            selectinload(Eleicao.candidatos),
            selectinload(Eleicao.chapas),
            selectinload(Eleicao.pautas)
        )
        .where(Eleicao.id == eleicao_id)
    )
    eleicao = result.scalar_one_or_none()

    if not eleicao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Eleição não encontrada"
        )

    return eleicao


@router.put("/{eleicao_id}", response_model=EleicaoResponse)
async def atualizar_eleicao(
    eleicao_id: int,
    data: EleicaoUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Eleicao).where(Eleicao.id == eleicao_id)
    )
    eleicao = result.scalar_one_or_none()

    if not eleicao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Eleição não encontrada"
        )

    if eleicao.status in [StatusEleicao.VOTACAO, StatusEleicao.ENCERRADA, StatusEleicao.APURADA]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível editar eleição em andamento ou encerrada"
        )

    # Verifica se já tem votos
    votos_result = await db.execute(
        select(func.count(Voto.id)).where(Voto.eleicao_id == eleicao_id)
    )
    total_votos = votos_result.scalar()

    if total_votos > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível editar eleição que já possui votos registrados"
        )

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(eleicao, field, value)

    await db.commit()
    await db.refresh(eleicao)

    return eleicao


@router.delete("/{eleicao_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_eleicao(
    eleicao_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Eleicao).where(Eleicao.id == eleicao_id)
    )
    eleicao = result.scalar_one_or_none()

    if not eleicao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Eleição não encontrada"
        )

    if eleicao.status != StatusEleicao.CONFIGURACAO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Só é possível excluir eleições em configuração"
        )

    await db.delete(eleicao)
    await db.commit()


@router.post("/{eleicao_id}/iniciar")
async def iniciar_eleicao(
    eleicao_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Eleicao).where(Eleicao.id == eleicao_id)
    )
    eleicao = result.scalar_one_or_none()

    if not eleicao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Eleição não encontrada"
        )

    if eleicao.status != StatusEleicao.CONVOCACAO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Eleição deve estar em convocação para iniciar"
        )

    eleicao.status = StatusEleicao.VOTACAO
    await db.commit()

    # Log da iniciacao
    await AuditoriaService.registrar(
        db=db,
        tipo=TipoLog.ELEICAO_INICIADA,
        descricao=f"Votacao iniciada: {eleicao.titulo}",
        eleicao_id=eleicao.id
    )

    return {"message": "Votação iniciada com sucesso"}


@router.post("/{eleicao_id}/encerrar")
async def encerrar_eleicao(
    eleicao_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Eleicao).where(Eleicao.id == eleicao_id)
    )
    eleicao = result.scalar_one_or_none()

    if not eleicao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Eleição não encontrada"
        )

    if eleicao.status != StatusEleicao.VOTACAO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Eleição deve estar em votação para encerrar"
        )

    eleicao.status = StatusEleicao.ENCERRADA
    await db.commit()

    # Log do encerramento
    await AuditoriaService.registrar(
        db=db,
        tipo=TipoLog.ELEICAO_ENCERRADA,
        descricao=f"Votacao encerrada: {eleicao.titulo}",
        eleicao_id=eleicao.id
    )

    return {"message": "Votação encerrada com sucesso"}


@router.post("/{eleicao_id}/convocar")
async def convocar_cooperados(
    eleicao_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Eleicao).where(Eleicao.id == eleicao_id)
    )
    eleicao = result.scalar_one_or_none()

    if not eleicao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Eleição não encontrada"
        )

    if eleicao.status != StatusEleicao.CONFIGURACAO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Eleição deve estar em configuração para convocar"
        )

    # Busca todos cooperados ativos
    coop_result = await db.execute(
        select(Cooperado).where(Cooperado.ativo == True)
    )
    cooperados = coop_result.scalars().all()

    convites_criados = 0
    for cooperado in cooperados:
        # Verifica se já existe convite
        existing = await db.execute(
            select(ConviteVotacao).where(
                ConviteVotacao.eleicao_id == eleicao_id,
                ConviteVotacao.cooperado_id == cooperado.id
            )
        )
        if existing.scalar_one_or_none():
            continue

        convite = ConviteVotacao(
            eleicao_id=eleicao_id,
            cooperado_id=cooperado.id,
            token=generate_token()
        )
        db.add(convite)
        convites_criados += 1

    eleicao.status = StatusEleicao.CONVOCACAO
    await db.commit()

    # TODO: Enviar emails/SMS

    return {
        "message": "Cooperados convocados com sucesso",
        "convites_criados": convites_criados
    }


@router.get("/{eleicao_id}/resultado")
async def resultado_eleicao(
    eleicao_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Eleicao)
        .options(selectinload(Eleicao.candidatos))
        .where(Eleicao.id == eleicao_id)
    )
    eleicao = result.scalar_one_or_none()

    if not eleicao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Eleição não encontrada"
        )

    # Total de votos
    total_result = await db.execute(
        select(func.count(Voto.id)).where(Voto.eleicao_id == eleicao_id)
    )
    total_votos = total_result.scalar()

    # Votos por candidato
    candidatos_resultado = []
    for candidato in eleicao.candidatos:
        votos_result = await db.execute(
            select(func.count(Voto.id)).where(
                Voto.eleicao_id == eleicao_id,
                Voto.candidato_id == candidato.id
            )
        )
        votos = votos_result.scalar()
        percentual = (votos / total_votos * 100) if total_votos > 0 else 0

        candidatos_resultado.append({
            "id": candidato.id,
            "nome": candidato.nome,
            "cargo": candidato.cargo,
            "votos": votos,
            "percentual": round(percentual, 2)
        })

    # Votos em branco
    brancos_result = await db.execute(
        select(func.count(Voto.id)).where(
            Voto.eleicao_id == eleicao_id,
            Voto.opcao == "branco"
        )
    )
    votos_branco = brancos_result.scalar()

    # Total de cooperados convocados
    convocados_result = await db.execute(
        select(func.count(ConviteVotacao.id)).where(
            ConviteVotacao.eleicao_id == eleicao_id
        )
    )
    total_convocados = convocados_result.scalar()

    participacao = (total_votos / total_convocados * 100) if total_convocados > 0 else 0

    return {
        "eleicao": {
            "id": eleicao.id,
            "titulo": eleicao.titulo,
            "status": eleicao.status
        },
        "total_votos": total_votos,
        "votos_branco": votos_branco,
        "total_convocados": total_convocados,
        "participacao": round(participacao, 2),
        "candidatos": sorted(candidatos_resultado, key=lambda x: x["votos"], reverse=True)
    }


@router.get("/ativas/cooperado/{cooperado_id}")
async def eleicoes_ativas_cooperado(
    cooperado_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Retorna eleições ativas que o cooperado pode votar"""
    now = datetime.now(timezone.utc)

    # Busca convites do cooperado para eleições em votação
    result = await db.execute(
        select(Eleicao)
        .join(ConviteVotacao)
        .where(
            ConviteVotacao.cooperado_id == cooperado_id,
            ConviteVotacao.votou == False,
            Eleicao.status == StatusEleicao.VOTACAO,
            Eleicao.data_inicio <= now,
            Eleicao.data_fim >= now
        )
    )

    eleicoes = result.scalars().all()
    return eleicoes
