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


@router.post("/{cooperado_id}/resetar-senha")
async def resetar_senha_cooperado(
    cooperado_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Gera nova senha e envia por email/SMS"""
    import random
    import string
    from app.services.sms_service import SmsService
    from app.services.email_service import EmailService
    from app.models.configuracao import Configuracao

    result = await db.execute(
        select(Cooperado).where(Cooperado.id == cooperado_id)
    )
    cooperado = result.scalar_one_or_none()

    if not cooperado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cooperado não encontrado"
        )

    # Gera senha aleatória de 8 caracteres
    nova_senha = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

    # Atualiza a senha no banco
    cooperado.senha_hash = hash_password(nova_senha)
    await db.commit()

    # Envia por SMS e/ou Email
    enviou_sms = False
    enviou_email = False
    canais = []

    # Busca URL base e nome do sistema
    base_url_result = await db.execute(
        select(Configuracao).where(Configuracao.chave == "baseUrl")
    )
    base_url_config = base_url_result.scalar_one_or_none()
    base_url = base_url_config.valor if base_url_config else "http://localhost:8033"
    logo_url = f"{base_url}/static/img/logo.png"

    if cooperado.telefone:
        resultado_sms = await SmsService.enviar_sms(
            db,
            cooperado.telefone,
            f"AssemblPro - Sua nova senha é: {nova_senha}"
        )
        if resultado_sms.get("sucesso"):
            enviou_sms = True
            canais.append("SMS")

    if cooperado.email:
        resultado_email = await EmailService.enviar_email(
            db,
            cooperado.email,
            "AssemblPro - Nova Senha",
            f"""
            <div style="font-family: Arial, sans-serif; background: #0a1628; padding: 30px; margin: 0;">
                <div style="max-width: 400px; margin: 0 auto; background: #111d32; border-radius: 12px; padding: 30px; text-align: center;">
                    <img src="{logo_url}" alt="Logo" style="max-height: 50px; margin-bottom: 15px;">
                    <h2 style="color: #00d4aa; margin-top: 0;">Nova Senha</h2>
                    <p style="color: #ffffff;">Olá, <strong style="color: #00d4aa;">{cooperado.nome}</strong>!</p>
                    <p style="color: #ffffff;">Sua senha foi redefinida. Use a senha abaixo para acessar o sistema:</p>
                    <div style="background: #162236; padding: 20px; border-radius: 8px; font-size: 24px; letter-spacing: 4px; color: #00d4aa; font-weight: bold; font-family: monospace;">
                        {nova_senha}
                    </div>
                    <p style="color: #fbbf24; font-size: 14px; margin-top: 20px;">
                        <strong>Importante:</strong> Recomendamos que você altere sua senha após o primeiro acesso.
                    </p>
                    <p style="color: #64748b; font-size: 12px; margin-top: 30px;">© 2026 AssemblPro</p>
                </div>
            </div>
            """,
            f"AssemblPro - Sua nova senha é: {nova_senha}"
        )
        if resultado_email.get("sucesso"):
            enviou_email = True
            canais.append("Email")

    if not canais:
        return {
            "sucesso": False,
            "mensagem": "Senha redefinida, mas não foi possível enviar. Cooperado sem email/telefone cadastrado.",
            "senha": nova_senha  # Retorna a senha para o admin poder informar manualmente
        }

    return {
        "sucesso": True,
        "mensagem": f"Nova senha enviada por {' e '.join(canais)}",
        "canais": canais
    }
