"""
Script para popular o banco de dados com dados de teste
"""
import asyncio
from sqlalchemy import select
from app.database import async_session
from app.models import Usuario, Cooperado, Eleicao, Candidato, TipoEleicao, StatusEleicao
from app.utils.security import hash_password
from datetime import datetime, timedelta


async def seed():
    async with async_session() as db:
        # Verifica se já existe admin
        result = await db.execute(select(Usuario).where(Usuario.email == "admin@admin.com"))
        if not result.scalar_one_or_none():
            # 1. Criar Admin
            admin = Usuario(
                nome="Administrador",
                email="admin@admin.com",
                senha_hash=hash_password("admin123"),
                is_admin=True,
                ativo=True
            )
            db.add(admin)
            print("Admin criado")

        # Verifica se já existem cooperados
        result = await db.execute(select(Cooperado).where(Cooperado.cpf == "12345678901"))
        if not result.scalar_one_or_none():
            # 2. Criar Cooperados de teste
            cooperados = [
                Cooperado(
                    nome="Joao Silva",
                    cpf="12345678901",
                    email="joao@teste.com",
                    telefone="11999999999",
                    senha_hash=hash_password("123456"),
                    regiao="Norte",
                    ativo=True,
                    otp_ativo=False
                ),
                Cooperado(
                    nome="Maria Santos",
                    cpf="98765432100",
                    email="maria@teste.com",
                    telefone="11988888888",
                    senha_hash=hash_password("123456"),
                    regiao="Sul",
                    ativo=True,
                    otp_ativo=False
                ),
                Cooperado(
                    nome="Pedro Oliveira",
                    cpf="11122233344",
                    email="pedro@teste.com",
                    telefone="11977777777",
                    senha_hash=hash_password("123456"),
                    regiao="Centro",
                    ativo=True,
                    otp_ativo=False
                ),
            ]
            for c in cooperados:
                db.add(c)
            print("Cooperados criados")

        await db.commit()

        # Verifica se já existe eleição
        result = await db.execute(select(Eleicao))
        if result.scalar_one_or_none():
            print("Dados já existem no banco!")
            return

        # 3. Criar Eleicao de teste
        eleicao = Eleicao(
            titulo="Eleicao Conselho Fiscal 2026",
            descricao="Eleicao para escolha dos membros do Conselho Fiscal para o biendio 2026-2028",
            tipo=TipoEleicao.CONSELHO,
            data_inicio=datetime.now(),
            data_fim=datetime.now() + timedelta(days=7),
            status=StatusEleicao.VOTACAO,
            exige_mfa=False,
            permite_voto_branco=True,
            created_by=1
        )
        db.add(eleicao)
        await db.commit()

        # 4. Criar Candidatos
        candidatos = [
            Candidato(
                eleicao_id=eleicao.id,
                nome="Carlos Ferreira",
                cargo="Conselheiro Fiscal Titular",
                descricao="Contador com 15 anos de experiencia em cooperativas",
                ordem=1
            ),
            Candidato(
                eleicao_id=eleicao.id,
                nome="Ana Costa",
                cargo="Conselheiro Fiscal Titular",
                descricao="Administradora e cooperada ha 10 anos",
                ordem=2
            ),
            Candidato(
                eleicao_id=eleicao.id,
                nome="Roberto Lima",
                cargo="Conselheiro Fiscal Suplente",
                descricao="Economista e especialista em auditoria",
                ordem=3
            ),
        ]
        for c in candidatos:
            db.add(c)

        await db.commit()

        print("=" * 50)
        print("DADOS DE TESTE CRIADOS COM SUCESSO!")
        print("=" * 50)
        print()
        print("ADMIN:")
        print("  Email: admin@admin.com")
        print("  Senha: admin123")
        print()
        print("COOPERADOS:")
        print("  CPF: 123.456.789-01 | Senha: 123456 | Nome: Joao Silva")
        print("  CPF: 987.654.321-00 | Senha: 123456 | Nome: Maria Santos")
        print("  CPF: 111.222.333-44 | Senha: 123456 | Nome: Pedro Oliveira")
        print()
        print("ELEICAO ATIVA:")
        print(f"  {eleicao.titulo}")
        print(f"  Status: {eleicao.status.value}")
        print(f"  Candidatos: {len(candidatos)}")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed())
