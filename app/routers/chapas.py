from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from app.database import get_db
from app.models import Chapa, Eleicao, StatusEleicao
from app.schemas.chapa import ChapaCreate, ChapaUpdate, ChapaResponse, ChapaDetalhe

router = APIRouter(prefix="/api/chapas", tags=["Chapas"])


@router.get("/", response_model=List[ChapaResponse])
async def listar_chapas(
    eleicao_id: int = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Chapa)

    if eleicao_id:
        query = query.where(Chapa.eleicao_id == eleicao_id)

    query = query.order_by(Chapa.numero)
    result = await db.execute(query)

    return result.scalars().all()


@router.post("/", response_model=ChapaResponse, status_code=status.HTTP_201_CREATED)
async def criar_chapa(
    data: ChapaCreate,
    db: AsyncSession = Depends(get_db)
):
    # Verifica se eleição existe e está em configuração
    result = await db.execute(
        select(Eleicao).where(Eleicao.id == data.eleicao_id)
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
            detail="Só é possível adicionar chapas em eleições em configuração"
        )

    # Verifica se número já existe na eleição
    existing = await db.execute(
        select(Chapa).where(
            Chapa.eleicao_id == data.eleicao_id,
            Chapa.numero == data.numero
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Número de chapa já existe nesta eleição"
        )

    chapa = Chapa(**data.model_dump())
    db.add(chapa)
    await db.commit()
    await db.refresh(chapa)

    return chapa


@router.get("/{chapa_id}", response_model=ChapaDetalhe)
async def obter_chapa(
    chapa_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Chapa)
        .options(selectinload(Chapa.candidatos))
        .where(Chapa.id == chapa_id)
    )
    chapa = result.scalar_one_or_none()

    if not chapa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapa não encontrada"
        )

    return chapa


@router.put("/{chapa_id}", response_model=ChapaResponse)
async def atualizar_chapa(
    chapa_id: int,
    data: ChapaUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Chapa).where(Chapa.id == chapa_id)
    )
    chapa = result.scalar_one_or_none()

    if not chapa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapa não encontrada"
        )

    update_data = data.model_dump(exclude_unset=True)

    # Verifica se número já existe em outra chapa
    if "numero" in update_data:
        existing = await db.execute(
            select(Chapa).where(
                Chapa.eleicao_id == chapa.eleicao_id,
                Chapa.numero == update_data["numero"],
                Chapa.id != chapa_id
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Número de chapa já existe nesta eleição"
            )

    for field, value in update_data.items():
        setattr(chapa, field, value)

    await db.commit()
    await db.refresh(chapa)

    return chapa


@router.delete("/{chapa_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_chapa(
    chapa_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Chapa).where(Chapa.id == chapa_id)
    )
    chapa = result.scalar_one_or_none()

    if not chapa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapa não encontrada"
        )

    await db.delete(chapa)
    await db.commit()
