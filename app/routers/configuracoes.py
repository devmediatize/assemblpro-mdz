from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel
import os
import shutil

from app.database import get_db
from app.models import Configuracao
from app.services.sms_service import SmsService
from app.services.email_service import EmailService


router = APIRouter(prefix="/api", tags=["Configurações"])

# Caminho para salvar as logos
STATIC_IMG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "img")


class ConfiguracaoSchema(BaseModel):
    chave: str
    valor: str | None = None


class ConfiguracaoResponse(BaseModel):
    id: int
    chave: str
    valor: str | None

    class Config:
        from_attributes = True


@router.get("/configuracoes", response_model=List[ConfiguracaoResponse])
async def listar_configuracoes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Configuracao))
    return result.scalars().all()


@router.get("/configuracoes/{chave}")
async def obter_configuracao(chave: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Configuracao).where(Configuracao.chave == chave)
    )
    config = result.scalar_one_or_none()
    if not config:
        return {"chave": chave, "valor": None}
    return {"chave": config.chave, "valor": config.valor}


@router.post("/configuracoes")
async def salvar_configuracao(
    data: ConfiguracaoSchema,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Configuracao).where(Configuracao.chave == data.chave)
    )
    config = result.scalar_one_or_none()

    if config:
        config.valor = data.valor
    else:
        config = Configuracao(chave=data.chave, valor=data.valor)
        db.add(config)

    await db.commit()
    return {"success": True, "chave": data.chave}


@router.post("/upload/logo")
async def upload_logo(
    file: UploadFile = File(...),
    filename: str = Form(...)
):
    """Upload de logo (logo.png para tema escuro, logo2.png para tema claro)"""
    # Valida o nome do arquivo
    if filename not in ["logo.png", "logo2.png"]:
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido")

    # Valida o tipo do arquivo
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser uma imagem")

    # Valida o tamanho (max 2MB)
    content = await file.read()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Arquivo muito grande (max 2MB)")

    # Garante que o diretório existe
    os.makedirs(STATIC_IMG_PATH, exist_ok=True)

    # Salva o arquivo
    file_path = os.path.join(STATIC_IMG_PATH, filename)
    with open(file_path, "wb") as f:
        f.write(content)

    return {"success": True, "filename": filename, "path": f"/static/img/{filename}"}


class TestarSmsRequest(BaseModel):
    telefone: str


@router.post("/sms/testar")
async def testar_sms(
    data: TestarSmsRequest,
    db: AsyncSession = Depends(get_db)
):
    """Envia SMS de teste para verificar configurações"""
    mensagem = "AssemblPro - Este é um SMS de teste. Se você recebeu esta mensagem, suas configurações estão corretas!"

    resultado = await SmsService.enviar_sms(db, data.telefone, mensagem)

    if resultado.get("sucesso"):
        return {
            "success": True,
            "message": resultado.get("mensagem", "SMS enviado com sucesso!"),
            "simulado": resultado.get("simulado", False)
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=resultado.get("erro", "Erro ao enviar SMS")
        )


class TestarEmailRequest(BaseModel):
    email: str


@router.post("/email/testar")
async def testar_email(
    data: TestarEmailRequest,
    db: AsyncSession = Depends(get_db)
):
    """Envia email de teste para verificar configurações SMTP"""
    assunto = "AssemblPro - Email de Teste"

    # Obtém a URL base do servidor para as imagens
    # Em produção, substitua por sua URL real
    base_url = "http://localhost:8033"

    corpo_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #0a1628;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #111d32; border-radius: 12px; padding: 30px;">
                <!-- Logo Header -->
                <div style="text-align: center; margin-bottom: 30px;">
                    <img src="{base_url}/static/img/logo.png" alt="Logo" style="max-height: 60px; max-width: 200px;">
                </div>

                <h2 style="color: #ffffff; text-align: center; margin: 0 0 10px 0;">Email de Teste</h2>
                <p style="text-align: center; color: #94a3b8; margin: 0 0 30px 0;">
                    Se você está recebendo este email, suas configurações SMTP estão corretas!
                </p>

                <div style="background-color: #162236; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
                    <span style="color: #00d4aa; font-size: 24px;">✓</span>
                    <p style="margin: 10px 0 0 0; color: #00d4aa; font-weight: bold;">
                        Configurações de email funcionando corretamente
                    </p>
                </div>

                <!-- Divider -->
                <div style="border-top: 1px solid #1e3a5f; margin: 30px 0;"></div>

                <!-- Logo Footer -->
                <div style="text-align: center;">
                    <img src="{base_url}/static/img/logoassemblpro.png" alt="AssemblPro" style="max-height: 40px; max-width: 150px; opacity: 0.8;">
                    <p style="color: #64748b; font-size: 12px; margin: 15px 0 0 0;">
                        Sistema de Votação Eletrônica Segura
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    corpo_texto = "AssemblPro - Email de Teste. Se você está recebendo este email, suas configurações SMTP estão corretas!"

    resultado = await EmailService.enviar_email(db, data.email, assunto, corpo_html, corpo_texto)

    if resultado.get("sucesso"):
        return {
            "success": True,
            "message": resultado.get("mensagem", "Email enviado com sucesso!"),
            "simulado": resultado.get("simulado", False)
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=resultado.get("erro", "Erro ao enviar email")
        )
