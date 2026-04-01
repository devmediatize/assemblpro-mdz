from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models import Pauta, Eleicao, StatusEleicao
from app.schemas.pauta import PautaCreate, PautaUpdate, PautaResponse

router = APIRouter(prefix="/api/pautas", tags=["Pautas"])


@router.get("/", response_model=List[PautaResponse])
async def listar_pautas(
    eleicao_id: int = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Pauta)

    if eleicao_id:
        query = query.where(Pauta.eleicao_id == eleicao_id)

    query = query.order_by(Pauta.ordem)
    result = await db.execute(query)

    return result.scalars().all()


@router.post("/", response_model=PautaResponse, status_code=status.HTTP_201_CREATED)
async def criar_pauta(
    data: PautaCreate,
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
            detail="Só é possível adicionar pautas em eleições em configuração"
        )

    pauta = Pauta(**data.model_dump())
    db.add(pauta)
    await db.commit()
    await db.refresh(pauta)

    return pauta


@router.get("/{pauta_id}", response_model=PautaResponse)
async def obter_pauta(
    pauta_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Pauta).where(Pauta.id == pauta_id)
    )
    pauta = result.scalar_one_or_none()

    if not pauta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pauta não encontrada"
        )

    return pauta


@router.put("/{pauta_id}", response_model=PautaResponse)
async def atualizar_pauta(
    pauta_id: int,
    data: PautaUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Pauta).where(Pauta.id == pauta_id)
    )
    pauta = result.scalar_one_or_none()

    if not pauta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pauta não encontrada"
        )

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(pauta, field, value)

    await db.commit()
    await db.refresh(pauta)

    return pauta


@router.delete("/{pauta_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_pauta(
    pauta_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Pauta).where(Pauta.id == pauta_id)
    )
    pauta = result.scalar_one_or_none()

    if not pauta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pauta não encontrada"
        )

    await db.delete(pauta)
    await db.commit()
