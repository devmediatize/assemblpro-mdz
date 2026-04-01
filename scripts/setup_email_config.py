#!/usr/bin/env python3
"""
Script para configurar os dados de email no banco de dados.
Execute: python scripts/setup_email_config.py
"""

import asyncio
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import async_session_maker
from app.models.configuracao import Configuracao


async def setup_email_config():
    """Configura as credenciais de email"""

    configs = [
        ("smtpHost", "mail.mdzmail.com.br", "Servidor SMTP"),
        ("smtpPort", "465", "Porta SMTP"),
        ("smtpSecurity", "ssl", "Segurança (ssl/tls/none)"),
        ("smtpUser", "contato@iterativa.com.br", "Email de envio"),
        ("smtpPassword", "deusedemais10@", "Senha do email"),
    ]

    async with async_session_maker() as session:
        for chave, valor, descricao in configs:
            # Verifica se já existe
            result = await session.execute(
                select(Configuracao).where(Configuracao.chave == chave)
            )
            config = result.scalar_one_or_none()

            if config:
                # Atualiza
                config.valor = valor
                config.descricao = descricao
                print(f"Atualizado: {chave}")
            else:
                # Cria novo
                config = Configuracao(
                    chave=chave,
                    valor=valor,
                    descricao=descricao
                )
                session.add(config)
                print(f"Criado: {chave}")

        await session.commit()
        print("\n✓ Configurações de email salvas com sucesso!")


if __name__ == "__main__":
    asyncio.run(setup_email_config())
