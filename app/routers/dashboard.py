from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone

from app.database import get_db
from app.models import Eleicao, Cooperado, Voto, ConviteVotacao, StatusEleicao

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/estatisticas")
async def estatisticas_gerais(db: AsyncSession = Depends(get_db)):
    # Total de eleições
    eleicoes_result = await db.execute(select(func.count(Eleicao.id)))
    total_eleicoes = eleicoes_result.scalar()

    # Eleições por status
    em_votacao_result = await db.execute(
        select(func.count(Eleicao.id)).where(Eleicao.status == StatusEleicao.VOTACAO)
    )
    em_votacao = em_votacao_result.scalar()

    # Total cooperados
    cooperados_result = await db.execute(
        select(func.count(Cooperado.id)).where(Cooperado.ativo == True)
    )
    total_cooperados = cooperados_result.scalar()

    # Total votos
    votos_result = await db.execute(select(func.count(Voto.id)))
    total_votos = votos_result.scalar()

    return {
        "total_eleicoes": total_eleicoes,
        "eleicoes_em_votacao": em_votacao,
        "total_cooperados": total_cooperados,
        "total_votos": total_votos
    }


@router.get("/eleicao/{eleicao_id}/tempo-real")
async def dados_tempo_real(
    eleicao_id: int,
    db: AsyncSession = Depends(get_db)
):
    from app.models import Candidato

    # Busca eleição
    eleicao_result = await db.execute(
        select(Eleicao).where(Eleicao.id == eleicao_id)
    )
    eleicao = eleicao_result.scalar_one_or_none()

    if not eleicao:
        return {"error": "Eleição não encontrada"}

    # Total convocados (ou total de cooperados ativos se não houver convites)
    convocados_result = await db.execute(
        select(func.count(ConviteVotacao.id)).where(
            ConviteVotacao.eleicao_id == eleicao_id
        )
    )
    total_convocados = convocados_result.scalar()

    # Se não há convites, usa total de cooperados ativos
    if total_convocados == 0:
        coop_result = await db.execute(
            select(func.count(Cooperado.id)).where(Cooperado.ativo == True)
        )
        total_convocados = coop_result.scalar()

    # Total votos
    votos_result = await db.execute(
        select(func.count(Voto.id)).where(Voto.eleicao_id == eleicao_id)
    )
    total_votos = votos_result.scalar()

    # Buscar candidatos com votos
    candidatos_result = await db.execute(
        select(Candidato).where(Candidato.eleicao_id == eleicao_id).order_by(Candidato.ordem)
    )
    candidatos = candidatos_result.scalars().all()

    candidatos_lista = []
    for cand in candidatos:
        cand_votos_result = await db.execute(
            select(func.count(Voto.id)).where(
                Voto.eleicao_id == eleicao_id,
                Voto.candidato_id == cand.id
            )
        )
        cand_votos = cand_votos_result.scalar()
        candidatos_lista.append({
            "id": cand.id,
            "nome": cand.nome,
            "cargo": cand.cargo,
            "votos": cand_votos
        })

    # Tempo restante
    now = datetime.now(timezone.utc)
    if eleicao.data_fim > now:
        tempo_restante = (eleicao.data_fim - now).total_seconds()
    else:
        tempo_restante = 0

    return {
        "eleicao_id": eleicao_id,
        "titulo": eleicao.titulo,
        "status": eleicao.status,
        "total_aptos": total_convocados,
        "total_votos": total_votos,
        "votos_por_minuto": 0,
        "candidatos": candidatos_lista,
        "tempo_restante_segundos": int(tempo_restante)
    }


@router.get("/eleicao/{eleicao_id}/participacao-regiao")
async def participacao_por_regiao(
    eleicao_id: int,
    db: AsyncSession = Depends(get_db)
):
    # Cooperados por região
    regioes_result = await db.execute(
        select(
            Cooperado.regiao,
            func.count(Cooperado.id).label('total')
        )
        .where(Cooperado.ativo == True)
        .group_by(Cooperado.regiao)
    )

    regioes_data = {row.regiao or "Não informada": {"total": row.total, "votos": 0} for row in regioes_result.all()}

    # Votos por região
    votos_result = await db.execute(
        select(
            Cooperado.regiao,
            func.count(Voto.id).label('votos')
        )
        .join(Voto, Voto.cooperado_id == Cooperado.id)
        .where(Voto.eleicao_id == eleicao_id)
        .group_by(Cooperado.regiao)
    )

    for row in votos_result.all():
        regiao = row.regiao or "Não informada"
        if regiao in regioes_data:
            regioes_data[regiao]["votos"] = row.votos

    # Formata resposta para o frontend
    regioes = []
    for regiao, dados in regioes_data.items():
        participacao = (dados["votos"] / dados["total"] * 100) if dados["total"] > 0 else 0
        regioes.append({
            "regiao": regiao,
            "participacao": round(participacao, 1),
            "votos": dados["votos"],
            "total": dados["total"]
        })

    return regioes


@router.get("/eleicao/{eleicao_id}/evolucao-votos")
async def evolucao_votos(
    eleicao_id: int,
    db: AsyncSession = Depends(get_db)
):
    # Agrupa votos por hora
    result = await db.execute(
        select(
            func.date_trunc('hour', Voto.created_at).label('hora'),
            func.count(Voto.id).label('votos')
        )
        .where(Voto.eleicao_id == eleicao_id)
        .group_by(func.date_trunc('hour', Voto.created_at))
        .order_by(func.date_trunc('hour', Voto.created_at))
    )

    evolucao = []
    total_acumulado = 0
    for row in result.all():
        total_acumulado += row.votos
        evolucao.append({
            "hora": row.hora.isoformat() if row.hora else None,
            "votos_hora": row.votos,
            "total_acumulado": total_acumulado
        })

    return {"evolucao": evolucao}
