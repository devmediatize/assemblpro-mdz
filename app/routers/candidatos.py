from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import os
import uuid

from app.database import get_db
from app.models import Candidato, Eleicao, StatusEleicao
from app.schemas.candidato import CandidatoCreate, CandidatoUpdate, CandidatoResponse

router = APIRouter(prefix="/api/candidatos", tags=["Candidatos"])

UPLOAD_DIR = "static/img/candidatos"


@router.get("/", response_model=List[CandidatoResponse])
async def listar_candidatos(
    eleicao_id: int = None,
    chapa_id: int = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Candidato)

    if eleicao_id:
        query = query.where(Candidato.eleicao_id == eleicao_id)
    if chapa_id:
        query = query.where(Candidato.chapa_id == chapa_id)

    query = query.order_by(Candidato.ordem)
    result = await db.execute(query)

    return result.scalars().all()


@router.post("/", response_model=CandidatoResponse, status_code=status.HTTP_201_CREATED)
async def criar_candidato(
    data: CandidatoCreate,
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
            detail="Só é possível adicionar candidatos em eleições em configuração"
        )

    candidato = Candidato(**data.model_dump())
    db.add(candidato)
    await db.commit()
    await db.refresh(candidato)

    return candidato


@router.get("/{candidato_id}", response_model=CandidatoResponse)
async def obter_candidato(
    candidato_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Candidato).where(Candidato.id == candidato_id)
    )
    candidato = result.scalar_one_or_none()

    if not candidato:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidato não encontrado"
        )

    return candidato


@router.put("/{candidato_id}", response_model=CandidatoResponse)
async def atualizar_candidato(
    candidato_id: int,
    data: CandidatoUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Candidato).where(Candidato.id == candidato_id)
    )
    candidato = result.scalar_one_or_none()

    if not candidato:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidato não encontrado"
        )

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(candidato, field, value)

    await db.commit()
    await db.refresh(candidato)

    return candidato


@router.delete("/{candidato_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_candidato(
    candidato_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Candidato).where(Candidato.id == candidato_id)
    )
    candidato = result.scalar_one_or_none()

    if not candidato:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidato não encontrado"
        )

    await db.delete(candidato)
    await db.commit()


@router.post("/{candidato_id}/foto")
async def upload_foto(
    candidato_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Candidato).where(Candidato.id == candidato_id)
    )
    candidato = result.scalar_one_or_none()

    if not candidato:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidato não encontrado"
        )

    # Valida extensão
    ext = file.filename.split('.')[-1].lower()
    if ext not in ['jpg', 'jpeg', 'png', 'webp']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato inválido. Use JPG, PNG ou WebP"
        )

    # Cria diretório se não existir
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Salva arquivo
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    with open(filepath, 'wb') as f:
        f.write(content)

    # Atualiza candidato
    candidato.foto_url = f"/{filepath}"
    await db.commit()

    return {"foto_url": candidato.foto_url}
