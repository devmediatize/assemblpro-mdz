from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
import csv
import io

from app.database import get_db
from app.models import Cooperado
from app.schemas.cooperado import CooperadoCreate, CooperadoUpdate, CooperadoResponse
from app.utils.security import hash_password
from app.utils.validators import validate_cpf, clean_cpf

router = APIRouter(prefix="/api/cooperados", tags=["Cooperados"])


@router.get("/", response_model=List[CooperadoResponse])
async def listar_cooperados(
    skip: int = 0,
    limit: int = 100,
    regiao: str = None,
    ativo: bool = None,
    busca: str = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Cooperado)

    if regiao:
        query = query.where(Cooperado.regiao == regiao)
    if ativo is not None:
        query = query.where(Cooperado.ativo == ativo)
    if busca:
        # Busca por nome ou CPF
        busca_termo = f"%{busca}%"
        busca_cpf = busca.replace(".", "").replace("-", "")
        query = query.where(
            (Cooperado.nome.ilike(busca_termo)) |
            (Cooperado.cpf.ilike(f"%{busca_cpf}%"))
        )

    query = query.order_by(Cooperado.nome).offset(skip).limit(limit)
    result = await db.execute(query)

    return result.scalars().all()


@router.get("/total")
async def total_cooperados(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(func.count(Cooperado.id)))
    total = result.scalar()
    return {"total": total}


@router.post("/", response_model=CooperadoResponse, status_code=status.HTTP_201_CREATED)
async def criar_cooperado(
    data: CooperadoCreate,
    db: AsyncSession = Depends(get_db)
):
    cpf = clean_cpf(data.cpf)

    if not validate_cpf(cpf):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF inválido"
        )

    # Verifica se CPF já existe
    result = await db.execute(
        select(Cooperado).where(Cooperado.cpf == cpf)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF já cadastrado"
        )

    cooperado = Cooperado(
        nome=data.nome,
        cpf=cpf,
        email=data.email,
        telefone=data.telefone,
        regiao=data.regiao,
        matricula=data.matricula,
        senha_hash=hash_password(data.senha)
    )
    db.add(cooperado)
    await db.commit()
    await db.refresh(cooperado)

    return cooperado


@router.get("/{cooperado_id}", response_model=CooperadoResponse)
async def obter_cooperado(
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

    return cooperado


@router.put("/{cooperado_id}", response_model=CooperadoResponse)
async def atualizar_cooperado(
    cooperado_id: int,
    data: CooperadoUpdate,
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

    update_data = data.model_dump(exclude_unset=True)

    # Limpa e valida CPF se estiver sendo atualizado
    if "cpf" in update_data:
        cpf = clean_cpf(update_data["cpf"])
        if not validate_cpf(cpf):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CPF inválido"
            )
        # Verifica se o novo CPF já existe em outro cooperado
        existing = await db.execute(
            select(Cooperado).where(
                Cooperado.cpf == cpf,
                Cooperado.id != cooperado_id
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CPF já cadastrado para outro cooperado"
            )
        update_data["cpf"] = cpf

    if "senha" in update_data:
        update_data["senha_hash"] = hash_password(update_data.pop("senha"))

    for field, value in update_data.items():
        setattr(cooperado, field, value)

    await db.commit()
    await db.refresh(cooperado)

    return cooperado


@router.delete("/{cooperado_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_cooperado(
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

    await db.delete(cooperado)
    await db.commit()


@router.post("/importar")
async def importar_cooperados(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo deve ser CSV"
        )

    content = await file.read()
    decoded = content.decode('utf-8')
    reader = csv.DictReader(io.StringIO(decoded))

    importados = 0
    erros = []

    for row in reader:
        try:
            cpf = clean_cpf(row.get('cpf', ''))

            if not validate_cpf(cpf):
                erros.append(f"CPF inválido: {row.get('cpf')}")
                continue

            # Verifica se já existe
            result = await db.execute(
                select(Cooperado).where(Cooperado.cpf == cpf)
            )
            if result.scalar_one_or_none():
                erros.append(f"CPF já existe: {cpf}")
                continue

            cooperado = Cooperado(
                nome=row.get('nome', ''),
                cpf=cpf,
                email=row.get('email'),
                telefone=row.get('telefone'),
                regiao=row.get('regiao'),
                matricula=row.get('matricula'),
                senha_hash=hash_password(cpf[-4:])  # Senha padrão: últimos 4 dígitos do CPF
            )
            db.add(cooperado)
            importados += 1

        except Exception as e:
            erros.append(f"Erro na linha: {str(e)}")

    await db.commit()

    return {
        "importados": importados,
        "erros": erros
    }


@router.get("/regioes/lista")
async def listar_regioes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Cooperado.regiao).distinct().where(Cooperado.regiao.isnot(None))
    )
    regioes = [r[0] for r in result.all()]
    return {"regioes": regioes}
