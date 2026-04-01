import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.configuracao import Configuracao


class EmailService:
    """Serviço para envio de emails"""

    @staticmethod
    async def get_config(db: AsyncSession, chave: str) -> Optional[str]:
        """Obtém uma configuração do banco"""
        result = await db.execute(
            select(Configuracao).where(Configuracao.chave == chave)
        )
        config = result.scalar_one_or_none()
        return config.valor if config else None

    @staticmethod
    async def enviar_email(
        db: AsyncSession,
        destinatario: str,
        assunto: str,
        corpo_html: str,
        corpo_texto: Optional[str] = None
    ) -> dict:
        """
        Envia email usando as configurações SMTP do sistema.
        Retorna dict com 'sucesso' e 'mensagem' ou 'erro'
        """
        smtp_host = await EmailService.get_config(db, "smtpHost")
        smtp_port = await EmailService.get_config(db, "smtpPort")
        smtp_security = await EmailService.get_config(db, "smtpSecurity")
        smtp_user = await EmailService.get_config(db, "smtpUser")
        smtp_password = await EmailService.get_config(db, "smtpPassword")

        if not all([smtp_host, smtp_port, smtp_user]):
            # Modo desenvolvimento - simula envio
            print(f"[EMAIL SIMULADO] Para: {destinatario}")
            print(f"[EMAIL SIMULADO] Assunto: {assunto}")
            print(f"[EMAIL SIMULADO] Corpo: {corpo_texto or corpo_html}")
            return {
                "sucesso": True,
                "mensagem": "Email simulado (modo desenvolvimento)",
                "simulado": True
            }

        try:
            # Busca nome do sistema para usar como remetente
            nome_sistema = await EmailService.get_config(db, "nomeSistema") or "AssemblPro"

            # Cria mensagem
            msg = MIMEMultipart("alternative")
            msg["Subject"] = assunto
            msg["From"] = f"{nome_sistema} <{smtp_user}>"
            msg["To"] = destinatario

            # Adiciona corpo texto e HTML
            if corpo_texto:
                msg.attach(MIMEText(corpo_texto, "plain", "utf-8"))
            msg.attach(MIMEText(corpo_html, "html", "utf-8"))

            # Conecta ao servidor SMTP
            port = int(smtp_port)

            if smtp_security == "ssl":
                server = smtplib.SMTP_SSL(smtp_host, port)
            else:
                server = smtplib.SMTP(smtp_host, port)
                if smtp_security == "tls":
                    server.starttls()

            if smtp_password:
                server.login(smtp_user, smtp_password)

            server.sendmail(smtp_user, destinatario, msg.as_string())
            server.quit()

            return {
                "sucesso": True,
                "mensagem": "Email enviado com sucesso"
            }

        except Exception as e:
            return {
                "sucesso": False,
                "erro": str(e)
            }

    @staticmethod
    async def enviar_codigo_verificacao(
        db: AsyncSession,
        email: str,
        codigo: str,
        eleicao_titulo: str,
        nome_cooperado: str
    ) -> dict:
        """Envia código de verificação para votação por email"""
        assunto = f"AssemblPro - Código de Verificação para Votação"

        # Busca URL base e logo das configurações
        base_url = await EmailService.get_config(db, "baseUrl") or "http://localhost:8033"
        logo_url = f"{base_url}/static/img/logo.png"

        corpo_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body style="font-family: Arial, sans-serif; background-color: #0a1628; color: #ffffff; padding: 20px; margin: 0;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #111d32; border-radius: 12px; padding: 30px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <img src="{logo_url}" alt="Logo" style="max-height: 60px; margin-bottom: 15px;">
                    <p style="color: #94a3b8; margin: 0;">Sistema de Votação Eletrônica Segura</p>
                </div>

                <p style="color: #ffffff;">Olá, <strong style="color: #00d4aa;">{nome_cooperado}</strong>!</p>

                <p style="color: #ffffff;">Você solicitou um código de verificação para votar na eleição:</p>
                <p style="color: #00d4aa; font-weight: bold; font-size: 16px;">{eleicao_titulo}</p>

                <p style="color: #ffffff;">Seu código de verificação é:</p>

                <div style="background-color: #162236; font-size: 32px; font-weight: bold; text-align: center; padding: 20px; border-radius: 8px; letter-spacing: 8px; color: #00d4aa; margin: 20px 0;">
                    {codigo}
                </div>

                <div style="background-color: rgba(251, 191, 36, 0.15); border-left: 4px solid #fbbf24; padding: 15px; margin: 20px 0; border-radius: 4px;">
                    <strong style="color: #fbbf24;">⚠️ Importante:</strong>
                    <ul style="margin: 10px 0; padding-left: 20px; color: #ffffff;">
                        <li>Este código é válido por <strong>5 minutos</strong></li>
                        <li>Não compartilhe este código com ninguém</li>
                        <li>Se você não solicitou este código, ignore este email</li>
                    </ul>
                </div>

                <div style="margin-top: 30px; text-align: center; color: #94a3b8; font-size: 12px;">
                    <p>Este é um email automático. Por favor, não responda.</p>
                    <p>© 2026 AssemblPro - Votação Eletrônica Segura</p>
                </div>
            </div>
        </body>
        </html>
        """

        corpo_texto = f"""
AssemblPro - Código de Verificação para Votação

Olá, {nome_cooperado}!

Você solicitou um código de verificação para votar na eleição: {eleicao_titulo}

Seu código de verificação é: {codigo}

IMPORTANTE:
- Este código é válido por 5 minutos
- Não compartilhe este código com ninguém
- Se você não solicitou este código, ignore este email

---
AssemblPro - Votação Eletrônica Segura
        """

        return await EmailService.enviar_email(
            db, email, assunto, corpo_html, corpo_texto
        )
