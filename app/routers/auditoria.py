from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from typing import Optional
from datetime import datetime, timedelta, timezone

from app.database import get_db
from app.models.log_auditoria import LogAuditoria
from app.models.usuario import Usuario
from app.models.cooperado import Cooperado
from app.models.eleicao import Eleicao
from app.schemas.auditoria import LogAuditoriaResponse
from app.services.auditoria_service import AuditoriaService

router = APIRouter(prefix="/api/auditoria", tags=["Auditoria"])


@router.get("/")
async def listar_logs(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    tipo: Optional[str] = None,
    eleicao_id: Optional[int] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None
):
    """Lista logs de auditoria com filtros"""

    # Query base
    query = select(LogAuditoria)

    # Aplicar filtros
    filters = []

    if tipo:
        filters.append(LogAuditoria.tipo == tipo)

    if eleicao_id:
        filters.append(LogAuditoria.eleicao_id == eleicao_id)

    if data_inicio:
        try:
            dt_inicio = datetime.fromisoformat(data_inicio.replace('Z', '+00:00'))
            filters.append(LogAuditoria.created_at >= dt_inicio)
        except:
            pass

    if data_fim:
        try:
            dt_fim = datetime.fromisoformat(data_fim.replace('Z', '+00:00'))
            filters.append(LogAuditoria.created_at <= dt_fim)
        except:
            pass

    if filters:
        query = query.where(and_(*filters))

    # Ordenar e paginar
    query = query.order_by(desc(LogAuditoria.created_at)).offset(skip).limit(limit)

    result = await db.execute(query)
    logs = result.scalars().all()

    # Buscar nomes relacionados
    logs_response = []
    for log in logs:
        log_dict = {
            "id": log.id,
            "tipo": log.tipo,
            "descricao": log.descricao,
            "usuario_id": log.usuario_id,
            "cooperado_id": log.cooperado_id,
            "eleicao_id": log.eleicao_id,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "dados_json": log.dados_json,
            "hash_integridade": log.hash_integridade,
            "created_at": log.created_at,
            "usuario_nome": None,
            "cooperado_nome": None,
            "eleicao_titulo": None
        }

        # Buscar nome do usuario
        if log.usuario_id:
            usuario = await db.execute(select(Usuario.nome).where(Usuario.id == log.usuario_id))
            usuario_nome = usuario.scalar_one_or_none()
            log_dict["usuario_nome"] = usuario_nome

        # Buscar nome do cooperado
        if log.cooperado_id:
            cooperado = await db.execute(select(Cooperado.nome).where(Cooperado.id == log.cooperado_id))
            cooperado_nome = cooperado.scalar_one_or_none()
            log_dict["cooperado_nome"] = cooperado_nome

        # Buscar titulo da eleicao
        if log.eleicao_id:
            eleicao = await db.execute(select(Eleicao.titulo).where(Eleicao.id == log.eleicao_id))
            eleicao_titulo = eleicao.scalar_one_or_none()
            log_dict["eleicao_titulo"] = eleicao_titulo

        logs_response.append(log_dict)

    # Contar total
    count_query = select(func.count(LogAuditoria.id))
    if filters:
        count_query = count_query.where(and_(*filters))
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    return {
        "items": logs_response,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/tipos/")
async def listar_tipos(db: AsyncSession = Depends(get_db)):
    """Lista todos os tipos de log distintos"""
    result = await db.execute(
        select(LogAuditoria.tipo)
        .distinct()
        .order_by(LogAuditoria.tipo)
    )
    tipos = result.scalars().all()
    return tipos


@router.get("/estatisticas/")
async def estatisticas_logs(
    db: AsyncSession = Depends(get_db),
    dias: int = Query(7, ge=1, le=90)
):
    """Estatisticas dos logs de auditoria"""

    data_limite = datetime.now(timezone.utc) - timedelta(days=dias)

    # Total de logs
    total_result = await db.execute(select(func.count(LogAuditoria.id)))
    total = total_result.scalar()

    # Logs no periodo
    periodo_result = await db.execute(
        select(func.count(LogAuditoria.id))
        .where(LogAuditoria.created_at >= data_limite)
    )
    no_periodo = periodo_result.scalar()

    # Contagem por tipo
    por_tipo_result = await db.execute(
        select(LogAuditoria.tipo, func.count(LogAuditoria.id))
        .where(LogAuditoria.created_at >= data_limite)
        .group_by(LogAuditoria.tipo)
        .order_by(desc(func.count(LogAuditoria.id)))
    )
    por_tipo = [{"tipo": row[0], "quantidade": row[1]} for row in por_tipo_result.all()]

    # Logs por dia
    por_dia_result = await db.execute(
        select(
            func.date(LogAuditoria.created_at).label('data'),
            func.count(LogAuditoria.id)
        )
        .where(LogAuditoria.created_at >= data_limite)
        .group_by(func.date(LogAuditoria.created_at))
        .order_by(func.date(LogAuditoria.created_at))
    )
    por_dia = [{"data": str(row[0]), "quantidade": row[1]} for row in por_dia_result.all()]

    return {
        "total": total,
        "no_periodo": no_periodo,
        "dias_analisados": dias,
        "por_tipo": por_tipo,
        "por_dia": por_dia
    }


@router.get("/verificar-integridade/")
async def verificar_integridade(db: AsyncSession = Depends(get_db)):
    """Verifica a integridade da cadeia de logs"""
    resultado = await AuditoriaService.verificar_integridade(db)
    return resultado


@router.get("/{log_id}/")
async def obter_log(log_id: int, db: AsyncSession = Depends(get_db)):
    """Obtem detalhes de um log especifico"""
    result = await db.execute(
        select(LogAuditoria).where(LogAuditoria.id == log_id)
    )
    log = result.scalar_one_or_none()

    if not log:
        return {"error": "Log nao encontrado"}

    log_dict = {
        "id": log.id,
        "tipo": log.tipo,
        "descricao": log.descricao,
        "usuario_id": log.usuario_id,
        "cooperado_id": log.cooperado_id,
        "eleicao_id": log.eleicao_id,
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "dados_json": log.dados_json,
        "hash_integridade": log.hash_integridade,
        "created_at": log.created_at,
        "usuario_nome": None,
        "cooperado_nome": None,
        "eleicao_titulo": None
    }

    # Buscar nomes relacionados
    if log.usuario_id:
        usuario = await db.execute(select(Usuario.nome).where(Usuario.id == log.usuario_id))
        log_dict["usuario_nome"] = usuario.scalar_one_or_none()

    if log.cooperado_id:
        cooperado = await db.execute(select(Cooperado.nome).where(Cooperado.id == log.cooperado_id))
        log_dict["cooperado_nome"] = cooperado.scalar_one_or_none()

    if log.eleicao_id:
        eleicao = await db.execute(select(Eleicao.titulo).where(Eleicao.id == log.eleicao_id))
        log_dict["eleicao_titulo"] = eleicao.scalar_one_or_none()

    return log_dict
