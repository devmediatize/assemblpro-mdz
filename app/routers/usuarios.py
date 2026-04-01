from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse
from app.utils.security import hash_password

router = APIRouter(prefix="/api/usuarios", tags=["Usuários"])


@router.get("/", response_model=List[UsuarioResponse])
async def listar_usuarios(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Usuario).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def criar_usuario(
    data: UsuarioCreate,
    db: AsyncSession = Depends(get_db)
):
    # Verifica se email já existe
    result = await db.execute(
        select(Usuario).where(Usuario.email == data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado"
        )

    usuario = Usuario(
        nome=data.nome,
        email=data.email,
        senha_hash=hash_password(data.senha),
        is_admin=data.is_admin
    )
    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)

    return usuario


@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def obter_usuario(
    usuario_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Usuario).where(Usuario.id == usuario_id)
    )
    usuario = result.scalar_one_or_none()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )

    return usuario


@router.put("/{usuario_id}", response_model=UsuarioResponse)
async def atualizar_usuario(
    usuario_id: int,
    data: UsuarioUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Usuario).where(Usuario.id == usuario_id)
    )
    usuario = result.scalar_one_or_none()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )

    update_data = data.model_dump(exclude_unset=True)

    if "senha" in update_data:
        update_data["senha_hash"] = hash_password(update_data.pop("senha"))

    for field, value in update_data.items():
        setattr(usuario, field, value)

    await db.commit()
    await db.refresh(usuario)

    return usuario


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_usuario(
    usuario_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Usuario).where(Usuario.id == usuario_id)
    )
    usuario = result.scalar_one_or_none()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )

    await db.delete(usuario)
    await db.commit()
